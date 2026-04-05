---
name: rich-paste
description: >
  Paste rich text from clipboard and convert HTML to Markdown via terminal overlay.
  Reads text/html from system clipboard, converts to Markdown, shows preview in overlay,
  and returns the result to the session. Activates on "rich-paste", "rp", "paste rich",
  "paste html", "paste as markdown", "вставить как markdown", "rich paste".
argument-hint: 'optional: --manual (paste raw HTML), --no-preview (skip interactive preview)'
allowed-tools: [Bash]
disable-model-invocation: true
---

# /rich-paste (/rp) - Rich Text to Markdown

Read HTML from clipboard, convert to Markdown, preview in overlay, return to session.

## How It Works

1. User copies text from a web page, Google Docs, ChatGPT, etc.
2. Invokes `/rp` (or `/rich-paste`)
3. Overlay opens, reads `text/html` from system clipboard
4. Converts HTML to Markdown (preserving links, formatting, lists, headers)
5. Shows preview — user presses Enter to accept or q to cancel
6. Markdown is returned to the Claude session

## Workflow

### Step 1: Resolve scripts path and launch overlay

First, determine the scripts directory. Use this exact bash snippet:

```bash
if [ -n "${CLAUDE_PLUGIN_ROOT:-}" ]; then
  SCRIPTS="${CLAUDE_PLUGIN_ROOT}/.claude-plugin/skills/rich-paste/scripts"
else
  SCRIPTS="$(cd "$(dirname "$(readlink -f ~/.claude/skills/rich-paste/SKILL.md)")" && pwd)/scripts"
fi
"$SCRIPTS/launch-overlay.sh"
```

If `$ARGUMENTS` contains `--manual` or `manual`, pass `--manual` flag:

```bash
"$SCRIPTS/launch-overlay.sh" --manual
```

If `$ARGUMENTS` contains `--no-preview`, pass `--no-preview` flag (skips overlay, auto-accepts):

```bash
"$SCRIPTS/launch-overlay.sh" --no-preview
```

### Step 2: Read Output

The script prints converted Markdown to stdout. If output is non-empty, present it to the user as the pasted content. The Markdown is ready to use in the conversation context.

If output is empty, the user cancelled — inform them.

### Step 3: Done

No looping needed. Single paste operation.
