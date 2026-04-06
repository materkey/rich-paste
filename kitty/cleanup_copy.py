"""Kitty kitten: copy selection to clipboard with Claude Code cleanup.

Removes ❯ prompts, joins wrapped lines within paragraphs,
and collapses excess whitespace.

Install: cp cleanup_copy.py ~/.config/kitty/
         Add to kitty.conf:
         map cmd+c kitten cleanup_copy.py
         map cmd+с kitten cleanup_copy.py
"""

import re

from kittens.tui.handler import result_handler

_PROMPT_RE = re.compile(r'^❯\s*', re.MULTILINE)
_MULTI_SPACE_RE = re.compile(r'\s{2,}')


def cleanup(text: str) -> str:
    text = _PROMPT_RE.sub('', text)

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

    from kitty.clipboard import set_clipboard_string
    set_clipboard_string(cleanup(text))
