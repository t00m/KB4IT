"""action.yml offers the inputs and outputs of the specification and runs the same on every runner."""

import re
import tomllib

import yaml

from tests.helpers import ROOT

ACTION = yaml.safe_load((ROOT / "action.yml").read_text(encoding="utf-8"))
RUN = (ROOT / "scripts" / "action" / "run.sh").read_text(encoding="utf-8")


def test_inputs_and_defaults():
    inputs = ACTION["inputs"]
    assert inputs["config"]["required"] is True
    defaults = {name: spec.get("default") for name, spec in inputs.items() if name != "config"}
    assert defaults == {"version": "", "python-version": "3.13", "extras": "false", "verify": "true", "force": "false"}


def test_outputs():
    assert set(ACTION["outputs"]) == {"target", "version"}


def test_marketplace_metadata():
    assert ACTION["name"] == "KB4IT site build"
    assert ACTION["description"] and ACTION["branding"]["icon"] and ACTION["branding"]["color"]


def test_every_step_runs_in_bash_from_the_action_folder():
    steps = ACTION["runs"]["steps"]
    assert ACTION["runs"]["using"] == "composite"
    for step in steps:
        if "run" in step:
            assert step["shell"] == "bash"
            assert '"$ACTION_PATH/scripts/action/run.sh"' in step["run"]
    assert [s.get("id") for s in steps if "run" in s] == ["install", "verify", "build"]


def test_setup_uv_pinned_like_the_workflows():
    pinned = [s["uses"] for s in ACTION["runs"]["steps"] if "uses" in s]
    workflow = (ROOT / ".github" / "workflows" / "kb4it.yml").read_text(encoding="utf-8")
    for uses in pinned:
        assert re.fullmatch(r"[\w-]+/[\w-]+@v\d+\.\d+\.\d+", uses), uses
        assert uses in workflow


def test_extras_match_pyproject():
    poetry = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["tool"]["poetry"]
    deps = poetry["dependencies"]
    for name in poetry["extras"]["extras"]:
        assert f'"{name}{deps[name]["version"]}"' in RUN, name


def test_action_never_deploys():
    assert "deploy" not in (ROOT / "action.yml").read_text(encoding="utf-8").lower()
