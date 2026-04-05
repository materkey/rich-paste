# rich-paste

Clipboard HTML → Markdown converter with terminal overlay preview.

## Structure
- `.claude-plugin/` — Claude Code plugin definition
- `.claude-plugin/skills/rich-paste/` — skill (SKILL.md + scripts)
- `scripts/rich-paste.py` — uv script: clipboard read, HTML→MD conversion, interactive preview
- `scripts/launch-overlay.sh` — overlay launcher (tmux/kitty/wezterm), same pattern as revdiff

## How it works
1. `launch-overlay.sh` opens a terminal overlay
2. Inside overlay, `rich-paste.py` reads `text/html` from macOS clipboard via osascript+Cocoa
3. Converts HTML → Markdown using `markdownify`
4. Shows preview with Enter/q confirmation
5. Writes accepted Markdown to temp file
6. `launch-overlay.sh` cats the file to stdout → Claude reads it

## Dependencies
- `uv` — runs rich-paste.py as a self-contained script (auto-installs markdownify)
- macOS — clipboard HTML reading uses AppleScript + AppKit bridge
- tmux/kitty/wezterm — for overlay display
