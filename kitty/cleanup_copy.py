"""Kitty kitten: copy selection to clipboard with Claude Code cleanup.

Removes ❯ prompts, joins wrapped lines within paragraphs,
strips trailing whitespace and ANSI line-wrap artifacts.

Install: cp cleanup_copy.py ~/.config/kitty/
         Add to kitty.conf:
         map cmd+c kitten cleanup_copy.py
         map cmd+с kitten cleanup_copy.py
"""

import re


def cleanup(text: str) -> str:
    # Remove leading ❯ prompt (with optional space)
    text = re.sub(r'^❯\s*', '', text, flags=re.MULTILINE)

    lines = text.split('\n')

    # Group lines into paragraphs separated by blank lines
    paragraphs: list[list[str]] = []
    current: list[str] = []

    for line in lines:
        if line.strip() == '':
            if current:
                paragraphs.append(current)
                current = []
        else:
            current.append(line.strip())

    if current:
        paragraphs.append(current)

    # Join lines within each paragraph, collapse runs of whitespace
    return '\n\n'.join(
        re.sub(r'\s{2,}', ' ', ' '.join(p))
        for p in paragraphs
    )


def main(args):
    pass


from kittens.tui.handler import result_handler


@result_handler(no_ui=True)
def handle_result(args, data, target_window_id, boss):
    window = boss.window_id_map.get(target_window_id)
    if window is None:
        return

    text = window.text_for_selection()
    if not text:
        return

    cleaned = cleanup(text)

    from kitty.clipboard import set_clipboard_string
    set_clipboard_string(cleaned)
