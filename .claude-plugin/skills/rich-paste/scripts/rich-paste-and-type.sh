#!/usr/bin/env bash
# Convert clipboard HTML→Markdown, put back in clipboard.
# After this script exits, kitty pastes from clipboard.
set -uo pipefail

export PATH="$HOME/.local/bin:$HOME/.cargo/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"

UV_BIN=$(command -v uv 2>/dev/null || true)
[ -z "$UV_BIN" ] && exit 0

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
$UV_BIN run "$SCRIPT_DIR/rich-copy.py" >/dev/null 2>&1 || true
