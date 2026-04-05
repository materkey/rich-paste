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

This skill CANNOT work over SSH without clipboard forwarding. Rich text (text/html) is only accessible through system clipboard APIs — regular terminal paste (Cmd+V) only gives plain text, which defeats the purpose.

Tell the user:

"rich-paste не может работать в SSH-сессии — доступ к HTML-формату буфера обмена невозможен без clipboard forwarding. Варианты:
1. Запустите `/rich-paste` на локальной машине (macOS) и скопируйте результат сюда
2. Подключайтесь через `kitten ssh` вместо `ssh` — тогда clipboard будет проброшен
3. Просто вставьте текст как есть (Cmd+V) — ссылки будут потеряны, но текст будет"

Do NOT ask the user to "paste HTML" — they cannot paste HTML in a terminal. Do NOT offer manual mode as a workaround for SSH — it requires actual HTML source code which users don't have.

### Step 3: Read Output

The script prints converted Markdown to stdout. If output is non-empty, present it to the user as the pasted content. The Markdown is ready to use in the conversation context.

If output is empty, the user cancelled — inform them.

### Step 4: Done

No looping needed. Single paste operation.
