"""The blog builds its post pages without the old sample keys sort, timeline and webserver."""

import json

from tests.helpers import run_kb4it


def test_post_layout_without_old_sample_keys(tmp_path, home):
    repo = tmp_path / "blog"
    assert run_kb4it("create", "blog", repo, cwd=tmp_path, home=home).returncode == 0
    config = repo / "config" / "repo.json"
    settings = json.loads(config.read_text(encoding="utf-8"))
    for key in ("sort", "timeline", "webserver"):
        settings.pop(key, None)
    config.write_text(json.dumps(settings, indent=4), encoding="utf-8")
    result = run_kb4it("build", config, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    post = (repo / "target" / "first-post.html").read_text(encoding="utf-8")
    assert "<!-- POST :: START -->" in post
