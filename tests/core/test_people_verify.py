"""kb4it verify: profile errors fail it, profile warnings and information do not."""

from tests.helpers import page, run_kb4it, write_repo


def doc(title, **keys):
    keys.setdefault("Category", "Note")
    keys.setdefault("DocType", "Reference")
    keys.setdefault("Tag", "x")
    return page(title, **keys)


def verify(tmp_path, home, pages, **config):
    cfg = write_repo(tmp_path / "repo", "techdoc", pages, **config)
    return run_kb4it("verify", cfg, cwd=tmp_path, home=home)


def test_verify_profile_errors_fail(tmp_path, home):
    result = verify(tmp_path, home, {"a.md": doc("Alpha", Author="Jane Doe"),
                                     "PERSON-JANE-DOE.md": page("Jane", Person="Doe, Jane")})
    assert result.returncode != 0
    assert "Theme checks:" in result.stdout
    assert "PROFILE_INVALID doc=PERSON-JANE-DOE.md" in result.stdout


def test_verify_bad_people_setting_fails(tmp_path, home):
    result = verify(tmp_path, home, {"a.md": doc("Alpha")}, people={"keys": []})
    assert result.returncode != 0
    assert "must name at least one key" in result.stdout


def test_verify_notices_do_not_fail(tmp_path, home):
    result = verify(tmp_path, home, {"a.md": doc("Alpha", Author="Bob"),
                                     "PERSON-JANE-DOE.md": page("Jane", Person="Jane Doe")})
    assert result.returncode == 0, result.stdout
    warnings = result.stdout.split("People (warnings):", 1)[1]
    assert "PROFILE_NO_CONTACT person=Jane Doe" in warnings
    information = result.stdout.split("People (information):", 1)[1]
    assert "AUTHOR_NO_PROFILE person=Bob docs=1" in information
    assert "PROFILE_UNUSED person=Jane Doe" in information


def test_verify_contact_public_only_when_indexed(tmp_path, home):
    pages = {"a.md": doc("Alpha", Author="Jane Doe"), "PERSON-JANE-DOE.md": page("Jane", Person="Jane Doe",
                                                                                 Email="j@x.org")}
    public = verify(tmp_path / "public", home, pages, seo={"index": True})
    assert "PROFILE_CONTACT_PUBLIC person=Jane Doe key=Email" in public.stdout
    hidden = verify(tmp_path / "hidden", home, pages, seo={"index": False})
    assert "PROFILE_CONTACT_PUBLIC" not in hidden.stdout


def test_profile_is_not_non_conformant(tmp_path, home):
    result = verify(tmp_path, home, {"a.md": doc("Alpha", Author="Jane Doe"),
                                     "PERSON-JANE-DOE.md": page("Jane", Person="Jane Doe", Email="j@x.org")})
    assert result.returncode == 0, result.stdout
    assert "Non-conformant" not in result.stdout
