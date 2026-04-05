#!/usr/bin/env bash
# Launch rich-paste in a terminal overlay (tmux/kitty/wezterm).
# Reads HTML from clipboard, converts to Markdown, shows preview.
# usage: launch-overlay.sh [--manual]
# output: Markdown text (empty if cancelled)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RICH_PASTE_PY="$SCRIPT_DIR/rich-paste.py"

# resolve uv to absolute path so overlay shells can find it
UV_BIN=$(command -v uv 2>/dev/null || true)
if [ -z "$UV_BIN" ]; then
    echo "error: uv not found in PATH" >&2
    exit 1
fi

OUTPUT_FILE=$(mktemp /tmp/rich-paste-output-XXXXXX)
LOG_FILE=$(mktemp /tmp/rich-paste-log-XXXXXX)
trap 'rm -f "$OUTPUT_FILE" "$LOG_FILE"' EXIT

EXTRA_ARGS=""
NO_PREVIEW=0
for arg in "$@"; do
    case "$arg" in
        --manual|-m) EXTRA_ARGS="$EXTRA_ARGS --manual" ;;
        --no-preview) NO_PREVIEW=1 ;;
    esac
done

# If --no-preview passed, skip overlay entirely
if [ "$NO_PREVIEW" -eq 1 ]; then
    $UV_BIN run "$RICH_PASTE_PY" --output "$OUTPUT_FILE" --no-preview $EXTRA_ARGS 2>"$LOG_FILE"
    if [ ! -s "$OUTPUT_FILE" ] && [ -s "$LOG_FILE" ]; then
        cat "$LOG_FILE" >&2
    fi
    cat "$OUTPUT_FILE"
    exit 0
fi

# Build command with proper quoting — all paths are absolute
CMD="$UV_BIN run $RICH_PASTE_PY --output $OUTPUT_FILE $EXTRA_ARGS 2>$LOG_FILE"
CWD="$(pwd)"
OVERLAY_TITLE="rich-paste"

# popup size
POPUP_W="${RICH_PASTE_POPUP_WIDTH:-80%}"
POPUP_H="${RICH_PASTE_POPUP_HEIGHT:-70%}"

# tmux: display-popup -E blocks until command exits
if [ -n "${TMUX:-}" ] && command -v tmux >/dev/null 2>&1; then
    tmux display-popup -E -w "$POPUP_W" -h "$POPUP_H" -T " $OVERLAY_TITLE " -d "$CWD" -- sh -c "$CMD"
    if [ ! -s "$OUTPUT_FILE" ] && [ -s "$LOG_FILE" ]; then
        cat "$LOG_FILE" >&2
    fi
    cat "$OUTPUT_FILE"
    exit 0
fi

# kitty: overlay with sentinel file for blocking
KITTY_SOCK="${KITTY_LISTEN_ON:-}"
if [ -n "$KITTY_SOCK" ] && command -v kitty >/dev/null 2>&1; then
    SENTINEL=$(mktemp /tmp/rich-paste-done-XXXXXX)
    rm -f "$SENTINEL"

    KITTY_ARGS=(kitty @ --to "$KITTY_SOCK" launch --type=overlay --title="$OVERLAY_TITLE" --cwd="$CWD")
    if [ -n "${KITTY_WINDOW_ID:-}" ]; then
        KITTY_ARGS+=(--match "id:${KITTY_WINDOW_ID}")
    fi
    KITTY_ARGS+=(sh -c "$CMD; touch $SENTINEL")

    "${KITTY_ARGS[@]}" >/dev/null 2>&1

    while [ ! -f "$SENTINEL" ]; do
        sleep 0.3
    done
    rm -f "$SENTINEL"

    # If script failed, show log
    if [ ! -s "$OUTPUT_FILE" ] && [ -s "$LOG_FILE" ]; then
        cat "$LOG_FILE" >&2
    fi

    cat "$OUTPUT_FILE"
    exit 0
fi

# wezterm: split-pane with sentinel file for blocking
if [ -n "${WEZTERM_PANE:-}" ] && command -v wezterm >/dev/null 2>&1; then
    SENTINEL=$(mktemp /tmp/rich-paste-done-XXXXXX)
    rm -f "$SENTINEL"

    WEZTERM_PCT="${RICH_PASTE_POPUP_HEIGHT:-70%}"
    WEZTERM_PCT="${WEZTERM_PCT%%%}"
    wezterm cli split-pane --bottom --percent "$WEZTERM_PCT" \
        --pane-id "$WEZTERM_PANE" --cwd "$CWD" -- sh -c "$CMD; touch $SENTINEL" >/dev/null 2>&1

    while [ ! -f "$SENTINEL" ]; do
        sleep 0.3
    done
    rm -f "$SENTINEL"
    cat "$OUTPUT_FILE"
    exit 0
fi

# fallback: run directly without overlay (no interactive preview, auto-accept)
$UV_BIN run "$RICH_PASTE_PY" --output "$OUTPUT_FILE" --no-preview $EXTRA_ARGS 2>"$LOG_FILE"
if [ ! -s "$OUTPUT_FILE" ] && [ -s "$LOG_FILE" ]; then
    cat "$LOG_FILE" >&2
fi
cat "$OUTPUT_FILE"
exit 0
