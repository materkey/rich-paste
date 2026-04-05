#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = ["markdownify>=0.14"]
# ///
"""
rich-paste: read HTML from clipboard, convert to Markdown, preview and confirm.

Modes:
  default  — read text/html from macOS clipboard via osascript
  --manual — read raw HTML from stdin (paste + Ctrl-D)
"""

import argparse
import os
import subprocess
import sys
import tempfile
import tty
import termios


def read_clipboard_html() -> str:
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


def read_clipboard_plain() -> str:
    """Fallback: read plain text from clipboard."""
    result = subprocess.run(["pbpaste"], capture_output=True, text=True, timeout=5)
    return result.stdout.strip() if result.returncode == 0 else ""


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


def show_preview(markdown: str) -> bool:
    """Show Markdown preview, return True if accepted."""
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
    print("\033[1;32m Enter\033[0m accept  \033[1;31m q/Esc\033[0m cancel")
    print()

    while True:
        key = read_single_key()
        if key in ("\r", "\n"):
            return True
        if key in ("q", "Q", "ESC", "\x1b", "\x03"):
            return False


def main():
    parser = argparse.ArgumentParser(description="rich-paste: HTML clipboard to Markdown")
    parser.add_argument("--output", "-o", required=True, help="Output file path")
    parser.add_argument("--manual", "-m", action="store_true", help="Manual HTML input via stdin")
    args = parser.parse_args()

    # Read HTML
    if args.manual:
        html = read_manual_html()
    else:
        html = read_clipboard_html()

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
            print("\033[1;32m Enter\033[0m use as-is  \033[1;31m q/Esc\033[0m cancel")

            while True:
                key = read_single_key()
                if key in ("\r", "\n"):
                    with open(args.output, "w") as f:
                        f.write(plain)
                    return
                if key in ("q", "Q", "ESC", "\x1b", "\x03"):
                    return
        else:
            print("\033[1;31mClipboard is empty.\033[0m", file=sys.stderr)
            read_single_key()
            return

    # Convert
    markdown = convert_html_to_markdown(html)

    # Preview and confirm
    if show_preview(markdown):
        with open(args.output, "w") as f:
            f.write(markdown)


if __name__ == "__main__":
    main()
