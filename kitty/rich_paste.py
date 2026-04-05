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
    """Find rich-copy.py script in standard locations."""
    candidates = [
        # Next to this kitten (if repo cloned)
        os.path.join(os.path.dirname(__file__), "..", ".claude-plugin",
                     "skills", "rich-paste", "scripts", "rich-copy.py"),
        # Installed via symlink in ~/.local/bin
        os.path.expanduser("~/.local/bin/rich-copy"),
        # Plugin install
        os.path.expanduser("~/.claude/plugins/marketplaces/rich-paste/"
                           ".claude-plugin/skills/rich-paste/scripts/rich-copy.py"),
        # Manual clone
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
        return

    try:
        subprocess.run(
            [uv, "run", script],
            capture_output=True, timeout=15, env=env,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    try:
        r = subprocess.run(["pbpaste"], capture_output=True, text=True, timeout=5)
        text = r.stdout if r.returncode == 0 else ""
    except (subprocess.TimeoutExpired, FileNotFoundError):
        text = ""

    if text:
        w = boss.window_id_map.get(target_window_id)
        if w is not None:
            w.paste_text(text)
