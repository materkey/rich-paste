#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = ["markdownify>=0.14"]
# ///
"""
rich-copy: read HTML from clipboard, convert to Markdown, put Markdown back in clipboard.

Run on macOS before pasting into SSH sessions.
After running, Cmd+V will paste Markdown with links preserved.
"""

import os
import subprocess
import sys

# Import shared functions from rich-paste.py (same directory)
sys.path.insert(0, os.path.dirname(__file__))
from importlib import import_module
_rp = import_module("rich-paste")

read_clipboard_html = _rp.read_clipboard_html
convert_html_to_markdown = _rp.convert_html_to_markdown


def main():
    html = read_clipboard_html()
    if not html:
        print("No HTML in clipboard — nothing to convert", file=sys.stderr)
        sys.exit(1)

    markdown = convert_html_to_markdown(html)

    proc = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
    proc.communicate(markdown.encode("utf-8"))

    lines = markdown.split("\n")
    preview = "\n".join(lines[:5])
    if len(lines) > 5:
        preview += f"\n... ({len(lines)} lines total)"
    print(preview)


if __name__ == "__main__":
    main()
