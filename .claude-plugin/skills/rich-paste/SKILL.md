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
echo "DISPLAY=${DISPLAY:-} WAYLAND_DISPLAY=${WAYLAND_DISPLAY:-} TMUX=${TMUX:-} OS=$(uname)"; which kitten 2>/dev/null && echo "KITTEN=yes" || echo "KITTEN=no"
```

- **macOS** (`uname` = Darwin): always works — just launch
- **Linux with DISPLAY or WAYLAND_DISPLAY set**: works — just launch
- **Linux + kitten available + TMUX set**: works over `kitten ssh` — the overlay (tmux popup) will have /dev/tty access, and `kitten clipboard` will read the clipboard. Just launch.
- **Linux + kitten available + no TMUX**: tell the user to run Claude inside tmux: `tmux` then `claude`. Then `/rich-paste` will work.
- **Linux without any of the above**: clipboard NOT available. **Do NOT try wl-paste, xclip, or any clipboard tool — they will hang.** Go directly to Step 2b.

**Step 2a — clipboard available:**

```bash
"$SCRIPTS/launch-overlay.sh"
```

Pass `--manual` if `$ARGUMENTS` contains `--manual`.
Pass `--no-preview` if `$ARGUMENTS` contains `--no-preview`.

**Step 2b — no clipboard (SSH / headless, no kitten):**

This skill CANNOT work over SSH without clipboard forwarding. Rich text (text/html) is only accessible through system clipboard APIs — regular terminal paste (Cmd+V) only gives plain text, which defeats the purpose.

Tell the user:

"rich-paste cannot work in this session. Options:
1. Run Claude inside tmux (`tmux` → `claude`) and try again — if connected via `kitten ssh`, clipboard will be forwarded through the tmux overlay
2. Run `/rich-paste` on your local machine (macOS) and copy the result here
3. Connect via `kitten ssh` instead of `ssh` — this forwards the clipboard
4. Just paste the text as-is (Cmd+V) — links will be lost, but text will be there"

Do NOT ask the user to "paste HTML" — they cannot paste HTML in a terminal. Do NOT offer manual mode as a workaround for SSH — it requires actual HTML source code which users don't have.

### Step 3: Read Output

The script prints converted Markdown to stdout. If output is non-empty, present it to the user as the pasted content. The Markdown is ready to use in the conversation context.

If output is empty, the user cancelled — inform them.

### Step 4: Done

No looping needed. Single paste operation.
