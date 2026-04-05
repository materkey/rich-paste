"""
Kitty kitten: convert clipboard HTML to Markdown, paste into terminal.
Cmd+Shift+V = rich paste (preserves links, bold, lists from copied web content).

Install: cp rich_paste.py ~/.config/kitty/
         Add to kitty.conf:
           map cmd+shift+v kitten rich_paste.py
           map cmd+shift+м kitten rich_paste.py
"""
import os
import shutil
import subprocess


def main(args):
    pass


from kittens.tui.handler import result_handler

_HTML_MIMES = ('public.html', 'text/html')


def _build_env():
    env = os.environ.copy()
    env["PATH"] = os.pathsep.join([
        os.path.expanduser("~/.local/bin"),
        "/opt/homebrew/bin",
        "/usr/local/bin",
        env.get("PATH", ""),
    ])
    return env


def _find_rich_paste_script():
    candidates = [
        os.path.expanduser("~/.claude/plugins/marketplaces/rich-paste/"
                           ".claude-plugin/skills/rich-paste/scripts/rich-paste.py"),
        os.path.expanduser("~/projects/rich-paste/.claude-plugin/"
                           "skills/rich-paste/scripts/rich-paste.py"),
    ]
    for path in candidates:
        resolved = os.path.realpath(path)
        if os.path.isfile(resolved):
            return resolved
    return None


def _read_html(clipboard):
    """Read HTML from clipboard via kitty's native MIME API."""
    try:
        available = clipboard.get_available_mime_types_for_paste()
        for mime in _HTML_MIMES:
            if mime in available:
                data = clipboard.get_mime_data(mime)
                if data:
                    return data.decode('utf-8', 'replace')
    except Exception:
        pass
    return ''


def _convert_html_to_markdown(html, env):
    """Convert HTML to Markdown via uv + rich-paste.py."""
    uv = shutil.which("uv", path=env["PATH"])
    script = _find_rich_paste_script()
    if not uv or not script:
        return ''

    try:
        r = subprocess.run(
            [uv, "run", script, "--manual", "--no-preview", "--output", "/dev/stdout"],
            input=html, capture_output=True, text=True, timeout=15, env=env,
        )
        if r.returncode == 0:
            return r.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return ''


@result_handler(no_ui=True)
def handle_result(args, data, target_window_id, boss):
    w = boss.window_id_map.get(target_window_id)
    if w is None:
        return

    env = _build_env()

    html = _read_html(boss.clipboard)
    if html:
        md = _convert_html_to_markdown(html, env)
        if md:
            w.paste_text(md)
            return

    text = boss.clipboard.get_text()
    if text:
        w.paste_text(text)
