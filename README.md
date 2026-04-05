# rich-paste

Claude Code skill that reads rich text (HTML) from your clipboard, converts it to Markdown, and returns the result to your session — all through a terminal overlay preview.

## What it does

1. You copy text from a web page, Google Docs, ChatGPT, etc.
2. Run `/rp` (or `/rich-paste`) in Claude Code
3. Overlay opens with a Markdown preview
4. Press **Enter** to accept or **q** to cancel
5. Markdown appears in your Claude session with links, formatting, and structure preserved

## Installation

### Via `/plugin` slash commands

Inside Claude Code session:

```
/plugin marketplace add https://github.com/materkey/rich-paste.git
/plugin install rich-paste@rich-paste
```

### Via CLI

```bash
claude plugin marketplace add https://github.com/materkey/rich-paste.git
claude plugin install rich-paste@rich-paste
```

### Manual

```bash
git clone git@github.com:materkey/rich-paste.git ~/.claude/skills/rich-paste-repo
ln -s ~/.claude/skills/rich-paste-repo/.claude-plugin/skills/rich-paste ~/.claude/skills/rich-paste
```

## Requirements

- **macOS** or **Linux** — clipboard reading via AppKit (macOS) or xclip/xsel/wl-paste (Linux)
- **[uv](https://docs.astral.sh/uv/)** — runs the Python script with auto-installed dependencies
- **Terminal overlay** — one of: tmux, kitty, or wezterm

## Usage

### Claude Code skill

```
/rich-paste              # overlay: preview + confirm
/rich-paste --no-preview # instant conversion, no overlay
/rich-paste --manual     # paste raw HTML via stdin
```

### Standalone CLI

```bash
rich-copy   # convert clipboard HTML→Markdown in-place (macOS)
```

After running `rich-copy`, your clipboard contains Markdown. Regular Cmd+V will paste text with `[links](url)` preserved. Useful before pasting into SSH sessions, Slack, etc.

### Kitty hotkey (Cmd+Shift+V)

Copy the kitten and add mapping to `kitty.conf`:

```bash
cp kitty/rich_paste.py ~/.config/kitty/rich_paste.py
```

Add to `kitty.conf`:

```
map cmd+shift+v kitten rich_paste.py
map cmd+shift+м kitten rich_paste.py
```

Then reload kitty config (Cmd+Ctrl+,).

**Cmd+Shift+V** converts clipboard HTML→Markdown and pastes in one keystroke. Works everywhere including SSH sessions — the conversion happens on your local Mac before the text reaches the terminal.

The second mapping (`cmd+shift+м`) makes the hotkey work on Russian keyboard layout — kitty resolves key identity from the current layout, so a separate mapping is needed for Cyrillic.

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

When you copy text from a web page, the clipboard contains two formats: `text/plain` and `text/html`. Regular paste gives you plain text only. This skill reads the hidden `text/html` format — via macOS `NSPasteboard` API or Linux `xclip`/`wl-paste` — converts it to Markdown using [markdownify](https://github.com/matthewwithanm/python-markdownify), and feeds the result back to Claude.

The overlay mechanism (tmux popup / kitty overlay / wezterm split-pane) follows the same pattern as [revdiff](https://github.com/umputun/revdiff).
