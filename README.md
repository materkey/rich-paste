# rich-paste

Claude Code skill that reads rich text (HTML) from your clipboard, converts it to Markdown, and returns the result to your session — all through a terminal overlay preview.

## What it does

1. You copy text from a web page, Google Docs, ChatGPT, etc.
2. Run `/rp` (or `/rich-paste`) in Claude Code
3. Overlay opens with a Markdown preview
4. Press **Enter** to accept or **q** to cancel
5. Markdown appears in your Claude session with links, formatting, and structure preserved

## Installation

### Via `/install-plugin` slash command (recommended)

Inside Claude Code session:

```
/install-plugin materkey/rich-paste
```

### Via CLI

```bash
claude skills add materkey/rich-paste
```

### Via Claude Code plugin registry

```bash
claude plugin install rich-paste@materkey-rich-paste
```

### Manual

```bash
git clone git@github.com:materkey/rich-paste.git ~/.claude/skills/rich-paste-repo
ln -s ~/.claude/skills/rich-paste-repo/.claude-plugin/skills/rich-paste ~/.claude/skills/rich-paste
```

## Requirements

- **macOS** — clipboard HTML reading uses AppleScript + AppKit
- **[uv](https://docs.astral.sh/uv/)** — runs the Python script with auto-installed dependencies
- **Terminal overlay** — one of: tmux, kitty, or wezterm

## Usage

```
/rp              # read HTML from clipboard
/rich-paste      # same thing
/rp --manual     # paste raw HTML manually (stdin)
```

## Why

When you copy text from ChatGPT, a browser, or Google Docs and paste it into Claude Code, you get plain text — all links are lost. The text says "check the docs" but the URL that was behind it is gone.

With `/rp`, the hidden HTML from your clipboard is preserved — links, formatting, structure all come through as proper Markdown.

## Before / After

Suppose you copy this ChatGPT response and paste it into Claude Code:

### Before (regular Ctrl+V)

```
Use the migration guide and update your config file.
See the API reference for details on authentication.

Key changes:
- Updated OAuth flow
- New rate limits
- Deprecated endpoints removed
```

All links, bold text, and structure — gone. Just flat text.

### After (`/rp`)

```markdown
Use the [migration guide](https://docs.example.com/v2/migrate) and update your **config** file.
See the [API reference](https://docs.example.com/v2/api) for details on **authentication**.

**Key changes:**
- Updated [OAuth flow](https://docs.example.com/v2/oauth)
- New rate limits
- Deprecated endpoints removed
```

Links are preserved as `[text](url)`, bold stays as `**bold**`, lists keep their structure.

## How it works

When you copy text from a web page, the clipboard contains two formats: `text/plain` and `text/html`. Regular paste gives you plain text only. This skill reads the hidden `text/html` format via macOS `NSPasteboard` API, converts it to Markdown using [markdownify](https://github.com/matthewwithanm/python-markdownify), and feeds the result back to Claude.

The overlay mechanism (tmux popup / kitty overlay / wezterm split-pane) follows the same pattern as [revdiff](https://github.com/umputun/revdiff).
