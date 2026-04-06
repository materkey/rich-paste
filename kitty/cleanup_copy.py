"""Kitty kitten: copy selection to clipboard with Claude Code cleanup.

Two modes controlled by args:
  cmd+c  (no args)      — joins wrapped lines into single line per paragraph
  cmd+shift+c (--multi) — preserves multiline, only strips prompts

Install: cp cleanup_copy.py ~/.config/kitty/
         Add to kitty.conf:
         map cmd+c kitten cleanup_copy.py
         map cmd+с kitten cleanup_copy.py
         map cmd+shift+c kitten cleanup_copy.py --multi
         map cmd+shift+с kitten cleanup_copy.py --multi
"""

import re
import textwrap

from kittens.tui.handler import result_handler

_PROMPT_RE = re.compile(r'^❯\s*', re.MULTILINE)
_MULTI_SPACE_RE = re.compile(r'\s{2,}')


def cleanup(text: str, multiline: bool = False) -> str:
    text = _PROMPT_RE.sub('', text)

    if multiline:
        lines = [line.rstrip() for line in text.split('\n')]
        # collapse runs of blank lines to at most one
        result = []
        prev_blank = False
        for line in lines:
            if line == '':
                if not prev_blank:
                    result.append(line)
                prev_blank = True
            else:
                prev_blank = False
                result.append(line)
        cleaned = '\n'.join(result).strip()
        lines = cleaned.split('\n')
        if len(lines) > 1:
            # dedent all lines except first (first line often has no indent)
            rest = textwrap.dedent('\n'.join(lines[1:]))
            return lines[0] + '\n' + rest
        return cleaned

    paragraphs: list[list[str]] = []
    current: list[str] = []

    for line in text.split('\n'):
        if line.strip() == '':
            if current:
                paragraphs.append(current)
                current = []
        else:
            current.append(line.strip())

    if current:
        paragraphs.append(current)

    return '\n\n'.join(
        _MULTI_SPACE_RE.sub(' ', ' '.join(p))
        for p in paragraphs
    )


def main(args):
    pass


@result_handler(no_ui=True)
def handle_result(args, data, target_window_id, boss):
    window = boss.window_id_map.get(target_window_id)
    if window is None:
        return

    text = window.text_for_selection()
    if not text:
        return

    multi = '--multi' in args
    from kitty.clipboard import set_clipboard_string
    set_clipboard_string(cleanup(text, multiline=multi))
