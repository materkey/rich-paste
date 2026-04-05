#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = ["markdownify>=0.14"]
# ///
"""
rich-paste: read HTML from clipboard, convert to Markdown, preview and confirm.

Modes:
  default  — read text/html from system clipboard (macOS or Linux)
  --manual — read raw HTML from stdin (paste + Ctrl-D)
"""

import argparse
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import tty
import termios


def _read_clipboard_html_macos() -> str:
    """Read HTML from macOS clipboard using AppleScript + Cocoa bridge."""
    script = '''\
use framework "AppKit"
set pb to current application's NSPasteboard's generalPasteboard()
set htmlData to pb's dataForType:"public.html"
if htmlData is missing value then
    return ""
end if
set htmlString to (current application's NSString's alloc()'s initWithData:htmlData encoding:(current application's NSUTF8StringEncoding))
return htmlString as text
'''
    with tempfile.NamedTemporaryFile(suffix=".applescript", mode="w", delete=False) as f:
        f.write(script)
        tmp = f.name
    try:
        result = subprocess.run(
            ["osascript", tmp], capture_output=True, text=True, timeout=10
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    finally:
        os.unlink(tmp)


def _read_clipboard_html_linux() -> str:
    """Read HTML from Linux clipboard using xclip or xsel."""
    has_display = bool(os.environ.get("DISPLAY"))
    has_wayland = bool(os.environ.get("WAYLAND_DISPLAY"))

    # Try xclip first (supports target selection, needs X11)
    if has_display and shutil.which("xclip"):
        result = subprocess.run(
            ["xclip", "-selection", "clipboard", "-t", "text/html", "-o"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()

    # Try xsel (needs X11)
    if has_display and shutil.which("xsel"):
        result = subprocess.run(
            ["xsel", "--clipboard", "--output"],
            capture_output=True, text=True, timeout=5,
        )
        html = result.stdout.strip()
        if result.returncode == 0 and html.startswith("<"):
            return html

    # Try wl-paste for Wayland (needs WAYLAND_DISPLAY)
    if has_wayland and shutil.which("wl-paste"):
        result = subprocess.run(
            ["wl-paste", "--type", "text/html"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()

    return ""


def clipboard_available() -> bool:
    """Check if any clipboard tool is available and can actually work."""
    if platform.system() == "Darwin":
        return shutil.which("osascript") is not None
    # X11 tools need DISPLAY
    if os.environ.get("DISPLAY") and shutil.which("xclip"):
        return True
    if os.environ.get("DISPLAY") and shutil.which("xsel"):
        return True
    # Wayland tools need WAYLAND_DISPLAY
    if os.environ.get("WAYLAND_DISPLAY") and shutil.which("wl-paste"):
        return True
    return False


def read_clipboard_html() -> str:
    """Read HTML from system clipboard (macOS or Linux with display)."""
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
    """Fallback: read plain text from clipboard."""
    if platform.system() == "Darwin":
        return _read_clipboard_plain_macos()
    return _read_clipboard_plain_linux()


def read_manual_html() -> str:
    """Read raw HTML from stdin."""
    print("\033[1mPaste HTML below, then press Ctrl-D:\033[0m\n", file=sys.stderr)
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

    # Clean up excessive whitespace
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
    """Read a single keypress."""
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        # Handle escape sequences
        if ch == "\x1b":
            ch2 = sys.stdin.read(1) if sys.stdin.readable() else ""
            return "ESC" if not ch2 else ch + ch2
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def render_preview(markdown: str):
    """Render the preview screen."""
    # Clear screen
    print("\033[2J\033[H", end="")

    # Header
    print("\033[1;36m--- rich-paste ----------------------------------------\033[0m")
    print("\033[1;36m|\033[0m  HTML -> Markdown")
    print("\033[1;36m-------------------------------------------------------\033[0m")
    print()

    # Content
    for line in markdown.split("\n"):
        print(f"  {line}")

    print()
    print("\033[2m-------------------------------------------------------\033[0m")
    print("\033[1;32m Enter\033[0m accept  \033[1;33m r\033[0m re-read clipboard  \033[1;31m q/Esc\033[0m cancel")
    print()


def main():
    parser = argparse.ArgumentParser(description="rich-paste: HTML clipboard to Markdown")
    parser.add_argument("--output", "-o", required=True, help="Output file path")
    parser.add_argument("--manual", "-m", action="store_true", help="Manual HTML input via stdin")
    parser.add_argument("--no-preview", action="store_true", help="Skip interactive preview, auto-accept")
    args = parser.parse_args()

    # Read HTML
    if args.manual:
        html = read_manual_html()
    elif not clipboard_available():
        print("error: no clipboard tool available (need osascript on macOS, or xclip/xsel/wl-paste on Linux)", file=sys.stderr)
        print("hint: use /rich-paste --manual to paste HTML from stdin", file=sys.stderr)
        sys.exit(1)
    else:
        html = read_clipboard_html()

    # No-preview mode: convert and write immediately
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
        # Fallback message
        plain = read_clipboard_plain()
        if plain:
            print("\033[2J\033[H", end="")
            print("\033[1;33mNo HTML found in clipboard.\033[0m")
            print("\033[2mClipboard contains plain text only:\033[0m\n")
            print(plain[:500])
            if len(plain) > 500:
                print(f"\n\033[2m... ({len(plain)} chars total)\033[0m")
            print(f"\n\033[2m-------------------------------------------------------\033[0m")
            print("\033[1;32m Enter\033[0m use as-is  \033[1;33m r\033[0m re-read clipboard  \033[1;31m q/Esc\033[0m cancel")

            while True:
                key = read_single_key()
                if key in ("\r", "\n"):
                    with open(args.output, "w") as f:
                        f.write(plain)
                    return
                if key in ("r", "R"):
                    html = read_clipboard_html()
                    if html:
                        break  # fall through to the preview loop below
                    # Still no HTML — re-read plain and refresh
                    plain = read_clipboard_plain()
                    print("\033[2J\033[H", end="")
                    print("\033[1;33mNo HTML found in clipboard.\033[0m")
                    print("\033[2mClipboard contains plain text only:\033[0m\n")
                    print(plain[:500] if plain else "(empty)")
                    if plain and len(plain) > 500:
                        print(f"\n\033[2m... ({len(plain)} chars total)\033[0m")
                    print(f"\n\033[2m-------------------------------------------------------\033[0m")
                    print("\033[1;32m Enter\033[0m use as-is  \033[1;33m r\033[0m re-read clipboard  \033[1;31m q/Esc\033[0m cancel")
                    continue
                if key in ("q", "Q", "ESC", "\x1b", "\x03"):
                    return
            # If we broke out, html is now set — fall through
        else:
            print("\033[2J\033[H", end="")
            print("\033[1;31mClipboard is empty.\033[0m")
            print("\033[1;33m r\033[0m re-read clipboard  \033[1;31m q/Esc\033[0m cancel")
            while True:
                key = read_single_key()
                if key in ("r", "R"):
                    html = read_clipboard_html()
                    if html:
                        break
                    plain = read_clipboard_plain()
                    if plain:
                        print("\033[2J\033[H", end="")
                        print("\033[1;33mNo HTML found. Plain text:\033[0m\n")
                        print(plain[:500])
                        continue
                    print("\033[2J\033[H", end="")
                    print("\033[1;31mClipboard is still empty.\033[0m")
                    print("\033[1;33m r\033[0m re-read clipboard  \033[1;31m q/Esc\033[0m cancel")
                    continue
                if key in ("q", "Q", "ESC", "\x1b", "\x03"):
                    return
            # html is set if we broke out

    # Convert and preview loop
    markdown = convert_html_to_markdown(html)
    render_preview(markdown)

    while True:
        key = read_single_key()
        if key in ("\r", "\n"):
            with open(args.output, "w") as f:
                f.write(markdown)
            return
        if key in ("r", "R"):
            html = read_clipboard_html()
            if not html:
                # No HTML — show a flash message and re-render current preview
                render_preview(markdown)
                print("\033[1;33m  (no HTML in clipboard, showing previous)\033[0m")
                continue
            markdown = convert_html_to_markdown(html)
            render_preview(markdown)
            continue
        if key in ("q", "Q", "ESC", "\x1b", "\x03"):
            return


if __name__ == "__main__":
    main()
