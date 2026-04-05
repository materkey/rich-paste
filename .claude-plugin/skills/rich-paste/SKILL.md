---
name: rich-paste
description: >
  Paste rich text from clipboard and convert HTML to Markdown via terminal overlay.
  Reads text/html from system clipboard, converts to Markdown, shows preview in overlay,
  and returns the result to the session. Activates on "rich-paste", "rp", "paste rich",
  "paste html", "paste as markdown", "rich paste".
argument-hint: 'optional: --manual (paste raw HTML), --no-preview (skip interactive preview)'
allowed-tools: [Bash, AskUserQuestion]
disable-model-invocation: true
---

# /rich-paste (/rp) - Rich Text to Markdown

Read HTML from clipboard, convert to Markdown, preview in overlay, return to session.

## Workflow

### Step 1: Resolve scripts path

Determine the scripts directory. Use this exact bash snippet:

```bash
if [ -n "${CLAUDE_PLUGIN_ROOT:-}" ]; then
  SCRIPTS="${CLAUDE_PLUGIN_ROOT}/.claude-plugin/skills/rich-paste/scripts"
else
  SCRIPTS="$(cd "$(dirname "$(readlink -f ~/.claude/skills/rich-paste/SKILL.md)")" && pwd)/scripts"
fi
```

### Step 2: Check environment and launch

**IMPORTANT: Before launching, check if clipboard is available:**

```bash
echo "DISPLAY=${DISPLAY:-} WAYLAND_DISPLAY=${WAYLAND_DISPLAY:-} OS=$(uname)"
```

- **macOS** (`uname` = Darwin): clipboard always available via osascript
- **Linux with DISPLAY or WAYLAND_DISPLAY set**: clipboard available
- **Linux without DISPLAY/WAYLAND_DISPLAY** (e.g. SSH session): clipboard NOT available. **Do NOT try wl-paste, xclip, or any clipboard tool — they will hang.** Go directly to Step 2b.

**Step 2a — clipboard available:**

```bash
"$SCRIPTS/launch-overlay.sh"
```

Pass `--manual` if `$ARGUMENTS` contains `--manual`.
Pass `--no-preview` if `$ARGUMENTS` contains `--no-preview`.

**Step 2b — no clipboard (SSH / headless):**

Ask the user to paste HTML content directly using AskUserQuestion:
"Clipboard недоступен (SSH-сессия). Вставьте скопированный HTML-контент сюда (Cmd+V), и я конвертирую его в Markdown."

Then take the pasted text and run:

```bash
echo '<pasted content>' | "$SCRIPTS/launch-overlay.sh" --manual --no-preview
```

Or if the pasted text looks like plain text (no HTML tags), just use it as-is — no conversion needed.

### Step 3: Read Output

The script prints converted Markdown to stdout. If output is non-empty, present it to the user as the pasted content. The Markdown is ready to use in the conversation context.

If output is empty, the user cancelled — inform them.

### Step 4: Done

No looping needed. Single paste operation.
