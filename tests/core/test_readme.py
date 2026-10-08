"""The README's Usage block lists every kb4it command, so the two cannot drift apart."""

import re

from tests.helpers import ROOT, run_kb4it


def test_every_command_is_in_the_readme_usage(tmp_path, home):
    help_text = run_kb4it("--help", cwd=tmp_path, home=home).stdout
    commands = set(re.search(r"\{([a-z,]+)\}", help_text).group(1).split(","))
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    usage = readme.split("## Usage", 1)[1].split("```", 2)[1]
    listed = set(re.findall(r"^kb4it ([a-z]+)", usage, re.M))
    assert commands, help_text
    assert commands <= listed, f"missing from README Usage: {sorted(commands - listed)}"


def test_readme_has_no_em_dash():
    assert "\u2014" not in (ROOT / "README.md").read_text(encoding="utf-8")
