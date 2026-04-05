#!/usr/bin/env bash
# Convert clipboard HTML→Markdown and type it into the active kitty window.
# Used as a kitty hotkey action (Cmd+Shift+V).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
UV_BIN=$(command -v uv 2>/dev/null || true)
if [ -z "$UV_BIN" ]; then exit 1; fi

# Convert clipboard HTML→Markdown→clipboard
$UV_BIN run "$SCRIPT_DIR/rich-copy.py" >/dev/null 2>&1 || exit 0

# Now paste from (updated) clipboard via kitty remote control
KITTY_SOCK="${KITTY_LISTEN_ON:-}"
if [ -n "$KITTY_SOCK" ] && command -v kitty >/dev/null 2>&1; then
    kitty @ --to "$KITTY_SOCK" paste-from-clipboard
else
    # Fallback: use OSC 52 or just let the user Cmd+V manually
    exit 0
fi
