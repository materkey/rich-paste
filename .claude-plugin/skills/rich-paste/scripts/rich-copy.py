#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = ["markdownify>=0.14"]
# ///
"""
rich-copy: read HTML from clipboard, convert to Markdown, put Markdown back in clipboard.

Run this on macOS before pasting into SSH sessions.
After running, Cmd+V will paste Markdown with links preserved.
"""

import os
import subprocess
import sys
import tempfile


def read_clipboard_html() -> str:
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


def write_to_clipboard(text: str):
    proc = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
    proc.communicate(text.encode("utf-8"))


def main():
    html = read_clipboard_html()
    if not html:
        print("No HTML in clipboard — nothing to convert", file=sys.stderr)
        sys.exit(1)

    markdown = convert_html_to_markdown(html)
    write_to_clipboard(markdown)

    # Show brief preview
    lines = markdown.split("\n")
    preview = "\n".join(lines[:5])
    if len(lines) > 5:
        preview += f"\n... ({len(lines)} lines total)"
    print(preview)


if __name__ == "__main__":
    main()
