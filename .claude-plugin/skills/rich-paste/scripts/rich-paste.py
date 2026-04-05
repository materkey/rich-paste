#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = ["markdownify>=0.14"]
# ///
"""
rich-paste: read HTML from clipboard, convert to Markdown, preview and confirm.
"""

import argparse
import os
import platform
import shutil
import subprocess
import sys
import tty
import termios

# -- ANSI constants --
CLEAR = "\033[2J\033[H"
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN_BOLD = "\033[1;36m"
GREEN_BOLD = "\033[1;32m"
YELLOW_BOLD = "\033[1;33m"
RED_BOLD = "\033[1;31m"
RULE = f"{DIM}-------------------------------------------------------{RESET}"
ACCEPT_KEYS = ("\r", "\n")
QUIT_KEYS = ("q", "Q", "ESC", "\x1b", "\x03")
REFRESH_KEYS = ("r", "R")

# -- AppleScript for reading HTML clipboard (static, passed via stdin) --
_APPLESCRIPT_READ_HTML = '''\
use framework "AppKit"
set pb to current application's NSPasteboard's generalPasteboard()
set htmlData to pb's dataForType:"public.html"
if htmlData is missing value then
    return ""
end if
set htmlString to (current application's NSString's alloc()'s initWithData:htmlData encoding:(current application's NSUTF8StringEncoding))
return htmlString as text
'''


def _read_clipboard_html_macos() -> str:
    result = subprocess.run(
        ["osascript", "-"], input=_APPLESCRIPT_READ_HTML,
        capture_output=True, text=True, timeout=10,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def _read_clipboard_html_linux() -> str:
    has_display = bool(os.environ.get("DISPLAY"))
    has_wayland = bool(os.environ.get("WAYLAND_DISPLAY"))

    if has_display and shutil.which("xclip"):
        result = subprocess.run(
            ["xclip", "-selection", "clipboard", "-t", "text/html", "-o"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()

    if has_display and shutil.which("xsel"):
        result = subprocess.run(
            ["xsel", "--clipboard", "--output"],
            capture_output=True, text=True, timeout=5,
        )
        html = result.stdout.strip()
        if result.returncode == 0 and html.startswith("<"):
            return html

    if has_wayland and shutil.which("wl-paste"):
        result = subprocess.run(
            ["wl-paste", "--type", "text/html"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()

    return ""


def clipboard_available() -> bool:
    if platform.system() == "Darwin":
        return shutil.which("osascript") is not None
    has_display = bool(os.environ.get("DISPLAY"))
    has_wayland = bool(os.environ.get("WAYLAND_DISPLAY"))
    if has_display and (shutil.which("xclip") or shutil.which("xsel")):
        return True
    if has_wayland and shutil.which("wl-paste"):
        return True
    return False


def read_clipboard_html() -> str:
    if not clipboard_available():
        return ""
    if platform.system() == "Darwin":
        return _read_clipboard_html_macos()
    return _read_clipboard_html_linux()


def _read_clipboard_plain_macos() -> str:
    result = subprocess.run(["pbpaste"], capture_output=True, text=True, timeout=5)
    return result.stdout.strip() if result.returncode == 0 else ""


def _read_clipboard_plain_linux() -> str:
    has_display = bool(os.environ.get("DISPLAY"))
    has_wayland = bool(os.environ.get("WAYLAND_DISPLAY"))

    if has_display and shutil.which("xclip"):
        result = subprocess.run(
            ["xclip", "-selection", "clipboard", "-o"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    if has_display and shutil.which("xsel"):
        result = subprocess.run(
            ["xsel", "--clipboard", "--output"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    if has_wayland and shutil.which("wl-paste"):
        result = subprocess.run(
            ["wl-paste"], capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    return ""


def read_clipboard_plain() -> str:
    if platform.system() == "Darwin":
        return _read_clipboard_plain_macos()
    return _read_clipboard_plain_linux()


def read_manual_html() -> str:
    print(f"{BOLD}Paste HTML below, then press Ctrl-D:{RESET}\n", file=sys.stderr)
    return sys.stdin.read()


def convert_html_to_markdown(html: str) -> str:
    from markdownify import markdownify

    md = markdownify(
        html,
        heading_style="ATX",
        bullets="-",
        strong_em_symbol="*",
        strip=["img", "script", "style"],
    )

    lines = md.split("\n")
    cleaned = []
    blank_count = 0
    for line in lines:
        stripped = line.rstrip()
        if not stripped:
            blank_count += 1
            if blank_count <= 2:
                cleaned.append("")
        else:
            blank_count = 0
            cleaned.append(stripped)

    return "\n".join(cleaned).strip() + "\n"


def read_single_key() -> str:
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == "\x1b":
            ch2 = sys.stdin.read(1) if sys.stdin.readable() else ""
            return "ESC" if not ch2 else ch + ch2
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def render_preview(markdown: str):
    print(CLEAR, end="")
    print(f"{CYAN_BOLD}--- rich-paste ----------------------------------------{RESET}")
    print(f"{CYAN_BOLD}|{RESET}  HTML -> Markdown")
    print(f"{CYAN_BOLD}-------------------------------------------------------{RESET}")
    print()
    for line in markdown.split("\n"):
        print(f"  {line}")
    print()
    print(RULE)
    print(f"{GREEN_BOLD} Enter{RESET} accept  {YELLOW_BOLD} r{RESET} re-read clipboard  {RED_BOLD} q/Esc{RESET} cancel")
    print()


def render_plain_fallback(plain: str):
    print(CLEAR, end="")
    print(f"{YELLOW_BOLD}No HTML found in clipboard.{RESET}")
    print(f"{DIM}Clipboard contains plain text only:{RESET}\n")
    print(plain[:500])
    if len(plain) > 500:
        print(f"\n{DIM}... ({len(plain)} chars total){RESET}")
    print(f"\n{RULE}")
    print(f"{GREEN_BOLD} Enter{RESET} use as-is  {YELLOW_BOLD} r{RESET} re-read clipboard  {RED_BOLD} q/Esc{RESET} cancel")


def main():
    parser = argparse.ArgumentParser(description="rich-paste: HTML clipboard to Markdown")
    parser.add_argument("--output", "-o", required=True)
    parser.add_argument("--manual", "-m", action="store_true")
    parser.add_argument("--no-preview", action="store_true")
    args = parser.parse_args()

    if args.manual:
        html = read_manual_html()
    elif not clipboard_available():
        print("error: no clipboard tool available (need osascript on macOS, or xclip/xsel/wl-paste on Linux)", file=sys.stderr)
        print("hint: use /rich-paste --manual to paste HTML from stdin", file=sys.stderr)
        sys.exit(1)
    else:
        html = read_clipboard_html()

    if args.no_preview:
        if not html:
            plain = read_clipboard_plain()
            if plain:
                with open(args.output, "w") as f:
                    f.write(plain)
            return
        markdown = convert_html_to_markdown(html)
        with open(args.output, "w") as f:
            f.write(markdown)
        return

    if not html:
        plain = read_clipboard_plain()
        if plain:
            render_plain_fallback(plain)
            while True:
                key = read_single_key()
                if key in ACCEPT_KEYS:
                    with open(args.output, "w") as f:
                        f.write(plain)
                    return
                if key in REFRESH_KEYS:
                    html = read_clipboard_html()
                    if html:
                        break
                    plain = read_clipboard_plain()
                    render_plain_fallback(plain if plain else "(empty)")
                    continue
                if key in QUIT_KEYS:
                    return
        else:
            print(CLEAR, end="")
            print(f"{RED_BOLD}Clipboard is empty.{RESET}")
            print(f"{YELLOW_BOLD} r{RESET} re-read clipboard  {RED_BOLD} q/Esc{RESET} cancel")
            while True:
                key = read_single_key()
                if key in REFRESH_KEYS:
                    html = read_clipboard_html()
                    if html:
                        break
                    plain = read_clipboard_plain()
                    if plain:
                        render_plain_fallback(plain)
                        continue
                    print(CLEAR, end="")
                    print(f"{RED_BOLD}Clipboard is still empty.{RESET}")
                    print(f"{YELLOW_BOLD} r{RESET} re-read clipboard  {RED_BOLD} q/Esc{RESET} cancel")
                    continue
                if key in QUIT_KEYS:
                    return

    markdown = convert_html_to_markdown(html)
    render_preview(markdown)

    while True:
        key = read_single_key()
        if key in ACCEPT_KEYS:
            with open(args.output, "w") as f:
                f.write(markdown)
            return
        if key in REFRESH_KEYS:
            html = read_clipboard_html()
            if not html:
                render_preview(markdown)
                print(f"{YELLOW_BOLD}  (no HTML in clipboard, showing previous){RESET}")
                continue
            markdown = convert_html_to_markdown(html)
            render_preview(markdown)
            continue
        if key in QUIT_KEYS:
            return


if __name__ == "__main__":
    main()
