"""Helpers to run kb4it from this working tree against throwaway repositories."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures"
APPHELP = ROOT / "kb4it" / "resources" / "themes" / "apphelp"

_RUNNER = "import sys; from kb4it.core.main import main; sys.argv[0] = 'kb4it'; main()"


def run_kb4it(*args, cwd, home):
    """Run kb4it with an isolated HOME and return the finished process."""
    env = dict(os.environ, HOME=str(home), PYTHONPATH=str(ROOT), COLUMNS="1000", NO_COLOR="1")
    return subprocess.run(
        [sys.executable, "-c", _RUNNER, *map(str, args)],
        cwd=str(cwd), env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, timeout=600,
    )


def write_repo(base, theme, pages, **config):
    """Create a repository with the given source pages; return the path of repo.json."""
    (base / "config").mkdir(parents=True, exist_ok=True)
    (base / "source").mkdir(exist_ok=True)
    conf = {"title": "Test", "theme": theme, "source": "source", "target": "target"}
    conf.update(config)
    (base / "config" / "repo.json").write_text(json.dumps(conf, indent=2), encoding="utf-8")
    for name, text in pages.items():
        path = base / "source" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return base / "config" / "repo.json"


def mini_theme(dest, **theme_json):
    """Copy the mini test theme to dest, merge theme_json into its theme.json and return dest."""
    shutil.copytree(FIXTURES / "themes" / "mini", dest)
    conf_path = dest / "theme.json"
    conf = json.loads(conf_path.read_text(encoding="utf-8"))
    conf.update(theme_json)
    conf_path.write_text(json.dumps(conf, indent=2), encoding="utf-8")
    return dest


def page(title, body="Text.", **keys):
    """Return a Markdown page; pass at least one key, an empty frontmatter is invalid."""
    front = "".join(f"{key}: {value}\n" for key, value in keys.items())
    return f"---\n{front}---\n\n# {title}\n\n{body}\n"
