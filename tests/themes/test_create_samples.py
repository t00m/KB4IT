from tests.helpers import run_kb4it


def test_create_leaves_no_empty_marker(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    assert run_kb4it("create", "techdoc", "repo", cwd=tmp_path, home=home).returncode == 0
    assert not (tmp_path / "repo" / "source" / "EMPTY").exists()
    assert not (tmp_path / "repo" / "target" / "EMPTY").exists()


def test_create_keeps_existing_user_file(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    (tmp_path / "repo" / "source").mkdir(parents=True)
    (tmp_path / "repo" / "source" / "mine.md").write_text("user text", encoding="utf-8")
    assert run_kb4it("create", "techdoc", "repo", cwd=tmp_path, home=home).returncode == 0
    assert (tmp_path / "repo" / "source" / "mine.md").read_text(encoding="utf-8") == "user text"


def test_build_with_no_documents_succeeds(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    assert run_kb4it("create", "techdoc", "repo", cwd=tmp_path, home=home).returncode == 0
    for doc in (tmp_path / "repo" / "source").glob("*.md"):
        doc.unlink()
    result = run_kb4it("build", tmp_path / "repo" / "config" / "repo.json", cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout


def test_techdoc_samples_build_and_show(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    assert run_kb4it("create", "techdoc", "repo", cwd=tmp_path, home=home).returncode == 0
    cfg = tmp_path / "repo" / "config" / "repo.json"
    assert run_kb4it("build", cfg, cwd=tmp_path, home=home).returncode == 0
    index = (tmp_path / "repo" / "target" / "index.html").read_text(encoding="utf-8")
    assert "Check last night" in index
    assert "Disk full on the file server" in index


def test_create_keeps_same_name_user_file(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    (tmp_path / "repo" / "source").mkdir(parents=True)
    (tmp_path / "repo" / "source" / "backup-check.md").write_text("my runbook", encoding="utf-8")
    assert run_kb4it("create", "techdoc", "repo", cwd=tmp_path, home=home).returncode == 0
    assert (tmp_path / "repo" / "source" / "backup-check.md").read_text(encoding="utf-8") == "my runbook"


def test_blog_samples_build_and_show(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    assert run_kb4it("create", "blog", "repo", cwd=tmp_path, home=home).returncode == 0
    cfg = tmp_path / "repo" / "config" / "repo.json"
    assert run_kb4it("build", cfg, cwd=tmp_path, home=home).returncode == 0
    index = (tmp_path / "repo" / "target" / "index.html").read_text(encoding="utf-8")
    assert "Welcome to my notes" in index


def test_bookshelf_samples_build_and_show(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    assert run_kb4it("create", "bookshelf", "repo", cwd=tmp_path, home=home).returncode == 0
    cfg = tmp_path / "repo" / "config" / "repo.json"
    assert run_kb4it("build", cfg, cwd=tmp_path, home=home).returncode == 0
    index = (tmp_path / "repo" / "target" / "index.html").read_text(encoding="utf-8")
    assert "Sample Book" in index
