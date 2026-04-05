---
name: rich-paste
description: >
  Paste rich text from clipboard and convert HTML to Markdown via terminal overlay.
  Reads text/html from system clipboard, converts to Markdown, shows preview in overlay,
  and returns the result to the session. Activates on "rich-paste", "rp", "paste rich",
  "paste html", "paste as markdown", "вставить как markdown", "rich paste".
argument-hint: 'optional: --manual (paste raw HTML instead of reading clipboard)'
allowed-tools: [Bash]
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

### Step 1: Launch Overlay

```bash
~/.claude/skills/rich-paste/scripts/launch-overlay.sh
```

If `$ARGUMENTS` contains `--manual` or `manual`, pass `--manual` flag:

```bash
~/.claude/skills/rich-paste/scripts/launch-overlay.sh --manual
```

### Step 2: Read Output

The script prints converted Markdown to stdout. If output is non-empty, present it to the user as the pasted content. The Markdown is ready to use in the conversation context.

If output is empty, the user cancelled — inform them.

### Step 3: Done

No looping needed. Single paste operation.
