"""
Kitty kitten: convert clipboard HTML to Markdown, paste into terminal.
Cmd+Shift+V = rich paste (preserves links, bold, lists from copied web content).

Install: cp rich_paste.py ~/.config/kitty/
         echo 'map cmd+shift+v kitten rich_paste.py' >> ~/.config/kitty/kitty.conf
"""
import os
import shutil
import subprocess


def main(args):
    pass


from kittens.tui.handler import result_handler


def _find_rich_copy():
    # Prefer PATH-installed binary
    on_path = shutil.which("rich-copy")
    if on_path:
        return on_path
    candidates = [
        os.path.expanduser("~/.local/bin/rich-copy"),
        os.path.expanduser("~/.claude/plugins/marketplaces/rich-paste/"
                           ".claude-plugin/skills/rich-paste/scripts/rich-copy.py"),
        os.path.expanduser("~/projects/rich-paste/.claude-plugin/"
                           "skills/rich-paste/scripts/rich-copy.py"),
    ]
    for path in candidates:
        resolved = os.path.realpath(path)
        if os.path.isfile(resolved):
            return resolved
    return None


@result_handler(no_ui=True)
def handle_result(args, data, target_window_id, boss):
    env = os.environ.copy()
    env["PATH"] = os.path.expanduser("~/.local/bin") + ":" + \
                  os.path.expanduser("~/.cargo/bin") + ":" + \
                  "/opt/homebrew/bin:/usr/local/bin:" + env.get("PATH", "")

    uv = shutil.which("uv", path=env["PATH"])
    script = _find_rich_copy()
    if not uv or not script:
        boss.show_error("rich-paste", f"Cannot find uv ({uv}) or rich-copy script ({script})")
        return

    try:
        r = subprocess.run(
            [uv, "run", script],
            capture_output=True, text=True, timeout=15, env=env,
        )
        # rich-copy.py converts HTML→Markdown and also writes to clipboard via pbcopy.
        # If it failed (no HTML), clipboard is unchanged — paste as-is.
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Paste from clipboard (either converted Markdown or original text)
    try:
        r = subprocess.run(["pbpaste"], capture_output=True, text=True, timeout=5)
        text = r.stdout if r.returncode == 0 else ""
    except (subprocess.TimeoutExpired, FileNotFoundError):
        text = ""

    if text:
        w = boss.window_id_map.get(target_window_id)
        if w is not None:
            w.paste_text(text)
