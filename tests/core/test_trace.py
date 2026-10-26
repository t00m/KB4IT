"""kb4it build --trace times the build in var/log/trace.json, apart from the log."""

import json
import threading

from kb4it.core import trace
from tests.core.test_deploy_incremental import _repo
from tests.helpers import run_kb4it


def test_span_does_nothing_without_a_trace(tmp_path):
    with trace.span("idle"):
        pass
    assert not trace.active()
    assert trace.stop(str(tmp_path)) is None
    assert not (tmp_path / trace.TRACE_FILE).exists()


def test_trace_file_holds_nested_spans(tmp_path):
    trace.start()
    with trace.span("outer"):
        with trace.span("inner", doc="a.md"):
            pass
    path, events = trace.stop(str(tmp_path / "log"))
    assert not trace.active()
    data = json.loads((tmp_path / "log" / trace.TRACE_FILE).read_text(encoding="utf-8"))
    assert path == str(tmp_path / "log" / trace.TRACE_FILE)
    assert [e["name"] for e in data["traceEvents"]] == ["outer", "inner"]
    assert all(e["ph"] == "X" and e["dur"] >= 0 for e in data["traceEvents"])
    assert data["traceEvents"][1]["args"] == {"doc": "a.md"}
    assert [e["depth"] for e in events] == [0, 1]


def test_summary_groups_worker_threads(tmp_path):
    trace.start()
    with trace.span("build"):
        def job():
            with trace.span("compile"):
                pass

        workers = [threading.Thread(target=job) for _ in range(3)]
        for worker in workers:
            worker.start()
        for worker in workers:
            worker.join()
    _path, events = trace.stop(str(tmp_path))
    lines = trace.summary(events, min_share=0)
    assert lines[1].endswith("  build")
    assert lines[-1].startswith("compile in worker threads: n=3 ")
    assert not any(line.endswith("  compile") for line in lines)


def test_build_with_trace_writes_the_trace_file(tmp_path, home):
    cfg, repo, _theme = _repo(tmp_path)
    result = run_kb4it("-L", "DEBUG", "build", "--trace", cfg, cwd=repo, home=home)
    assert result.returncode == 0, result.stdout
    data = json.loads((repo / "var" / "log" / trace.TRACE_FILE).read_text(encoding="utf-8"))
    names = {e["name"] for e in data["traceEvents"]}
    assert {"build", "1 check_environment", "5 compilation", "7 deploy", "step_08_copy_global_resources_to_target",
            "compile"} <= names
    assert "Trace: " in result.stdout
    # The timings stay out of the log, even at DEBUG.
    assert "[PERFORMANCE]" not in result.stdout


def test_build_without_trace_writes_no_trace_file(tmp_path, home):
    cfg, repo, _theme = _repo(tmp_path)
    result = run_kb4it("build", cfg, cwd=repo, home=home)
    assert result.returncode == 0, result.stdout
    assert not (repo / "var" / "log" / trace.TRACE_FILE).exists()
    assert "Trace: " not in result.stdout
