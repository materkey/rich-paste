---
name: rich-paste
description: >
  Paste rich text from clipboard and convert HTML to Markdown via terminal overlay.
  Reads text/html from system clipboard, converts to Markdown, shows preview in overlay,
  and returns the result to the session. Activates on "rich-paste", "rp", "paste rich",
  "paste html", "paste as markdown", "rich paste".
argument-hint: 'optional: --manual (paste raw HTML), --no-preview (skip interactive preview)'
allowed-tools: [Bash]
disable-model-invocation: true
---

# /rich-paste (/rp) - Rich Text to Markdown

Read HTML from clipboard, convert to Markdown, preview in overlay, return to session.

## Workflow

### Step 1: Resolve scripts path

```bash
if [ -n "${CLAUDE_PLUGIN_ROOT:-}" ]; then
  SCRIPTS="${CLAUDE_PLUGIN_ROOT}/.claude-plugin/skills/rich-paste/scripts"
else
  SCRIPTS="$(cd "$(dirname "$(readlink -f ~/.claude/skills/rich-paste/SKILL.md)")" && pwd)/scripts"
fi
```

### Step 2: Check environment and launch

```bash
echo "OS=$(uname) DISPLAY=${DISPLAY:-} WAYLAND_DISPLAY=${WAYLAND_DISPLAY:-}"
```

- **macOS** (Darwin): always works. Run `"$SCRIPTS/launch-overlay.sh"`
- **Linux with DISPLAY or WAYLAND_DISPLAY**: works. Run `"$SCRIPTS/launch-overlay.sh"`
- **Linux without DISPLAY/WAYLAND_DISPLAY** (SSH session): clipboard NOT available. **Do NOT try wl-paste, xclip, kitten clipboard, or any clipboard tool — they will hang or fail.**

Tell the user to paste their text directly into the chat (Cmd+V). Accept whatever they paste — it will be plain text (links lost), but at least the content gets into the session. Present the pasted text back to the user as-is.

Note: for full rich-paste with links preserved, the user should run `/rich-paste` on their local machine instead.

Pass `--manual` if `$ARGUMENTS` contains `--manual`.
Pass `--no-preview` if `$ARGUMENTS` contains `--no-preview`.

### Step 3: Read Output

The script prints converted Markdown to stdout. If non-empty — present to user.
If empty — user cancelled.
