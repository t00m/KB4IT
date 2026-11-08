"""kb4it.theme: BaseTheme, features and the engine that runs them."""

import json
import textwrap

import pytest

from kb4it.core.exceptions import ThemeError
from kb4it.theme import BaseTheme, Feature
from kb4it.theme.feature import apply_theme_json, resolve, theme_json_keys
from tests.helpers import page, run_kb4it, write_repo


class A(Feature):
    name = "a"


class B(Feature):
    name = "b"
    requires = ("a",)


class C(Feature):
    name = "c"
    uses = ("d",)


class D(Feature):
    name = "d"
    assets = ("gallery",)
    theme_json = {"x": 1}


REGISTRY = {cls.name: cls for cls in (A, B, C, D)}
BUNDLES = {"ab": ("a", "b")}


def names(declared):
    return [cls.name for cls in resolve(declared, REGISTRY, BUNDLES)]


def test_requirements_come_first_and_bundles_expand():
    assert names(["b"]) == ["a", "b"]
    assert names(["ab"]) == ["a", "b"]


def test_uses_orders_only_when_enabled():
    assert names(["c", "d"]) == ["d", "c"]
    assert names(["c"]) == ["c"]


def test_theme_local_feature_class():
    class Local(Feature):
        name = "local"
        requires = ("a",)
    assert names([Local]) == ["a", "local"]


def test_unknown_and_cyclic_features_are_errors():
    with pytest.raises(ThemeError, match="unknown feature 'zzz'"):
        names(["zzz"])

    class X(Feature):
        name = "x"
        requires = ("y",)

    class Y(Feature):
        name = "y"
        requires = ("x",)
    with pytest.raises(ThemeError, match="require each other"):
        resolve(["x"], {"x": X, "y": Y}, {})

    class OtherA(Feature):
        name = "a"
    with pytest.raises(ThemeError, match="two features"):
        names(["a", OtherA])


def test_features_fill_theme_json_and_refuse_a_contradiction():
    keys = theme_json_keys(resolve(["d"], REGISTRY, BUNDLES), document_pages=False)
    assert keys == {"metadata_pages": False, "x": 1, "assets": ["gallery"]}
    theme = {"id": "t", "assets": ["search"]}
    apply_theme_json(theme, keys, "t")
    assert theme["assets"] == ["search", "gallery"] and theme["x"] == 1
    with pytest.raises(ThemeError, match="theme.json 'x' is 2"):
        apply_theme_json({"x": 2}, keys, "t")


def test_hook_is_the_theme_method_else_the_feature_default():
    class Hooked(Feature):
        name = "hooked"
        hooks = ("greet",)

        def greet(self):
            return "feature"

    class Theme(BaseTheme):
        def greet(self):
            return "theme"

    assert Hooked(Theme(), None).hook("greet")() == "theme"
    assert Hooked(BaseTheme(), None).hook("greet")() == "feature"


# A whole theme on the public API: the "hello theme" of "Write a theme".
HELLO = '''
from kb4it.theme import BaseTheme


class Theme(BaseTheme):
    features = ("search",)

    def prepare(self, site):
        self.log.info(f"[HELLO] STAGE name=prepare documents={len(site.documents)}")

    def build(self, site):
        self.log.info("[HELLO] STAGE name=build")
        items = [{"title": doc.title, "url": doc.url} for doc in site.documents]
        site.page("index", "Home", self.render("PAGE_INDEX", documents=items))

    def page_context(self, doc, var):
        var["tags"] = doc.values("Tag")
        return var

    def after_deploy(self, site):
        self.log.info(f"[HELLO] STAGE name=after_deploy index={(site.paths.target or '') != ''}")

    def after_checks(self, site):
        self.log.info("[HELLO] STAGE name=after_checks")
'''

TEMPLATES = {
    "HTML_HEADER_COMMON.tpl": "<!DOCTYPE html><html lang=\"${var['lang']}\"><head><title>${var['page']['title']}"
                              "</title></head><body>${var['search_box'] | n}",
    "HTML_BODY.tpl": "<main><h1>${var['page']['title']}</h1><p class=\"tags\">${', '.join(var['tags'])}</p>"
                     "${var['source_html'] | n}</main>",
    "HTML_FOOTER.tpl": "</body></html>",
    "PAGE_INDEX.tpl": "<ul>\n% for item in var['documents']:\n<li><a href=\"${item['url']}\">${item['title']}</a></li>\n"
                      "% endfor\n</ul>",
}


def make_theme(folder, code=HELLO, **theme_json):
    (folder / "logic").mkdir(parents=True)
    (folder / "templates").mkdir()
    (folder / "logic" / "theme.py").write_text(textwrap.dedent(code), encoding="utf-8")
    for name, text in TEMPLATES.items():
        (folder / "templates" / name).write_text(text, encoding="utf-8")
    conf = {"id": "hello", "name": "Hello", "version": "1.0.0", "kb4it": ">=0.12.0", "autoescape": True}
    conf.update(theme_json)
    (folder / "theme.json").write_text(json.dumps(conf), encoding="utf-8")
    return folder


@pytest.fixture(scope="module")
def hello(tmp_path_factory):
    base = tmp_path_factory.mktemp("hello")
    theme = make_theme(base / "hello")
    cfg = write_repo(base / "repo", "hello", {"one.md": page("One", Tag="alpha, beta", Date="2026-01-02"),
                                              "two.md": page("Two", Tag="beta")}, theme_path=str(theme))
    result = run_kb4it("build", cfg, cwd=base, home=base)
    return {"result": result, "target": base / "repo" / "target"}


def test_hello_theme_builds_cleanly(hello):
    assert hello["result"].returncode == 0, hello["result"].stdout
    assert " WARNING " not in hello["result"].stdout and " ERROR " not in hello["result"].stdout


def test_hello_theme_hooks_run_in_stage_order(hello):
    out = hello["result"].stdout
    stages = ["name=prepare documents=2", "name=build", "name=after_deploy index=True", "name=after_checks"]
    positions = [out.index(stage) for stage in stages]
    assert positions == sorted(positions)


def test_hello_theme_pages(hello):
    index = (hello["target"] / "index.html").read_text(encoding="utf-8")
    assert 'href="one.html"' in index and 'href="two.html"' in index
    one = (hello["target"] / "one.html").read_text(encoding="utf-8")
    assert '<p class="tags">alpha, beta</p>' in one
    # The search feature: page, box and index, without "search" in theme.json.
    assert (hello["target"] / "search.html").exists() and (hello["target"] / "search-index.js").exists()
    assert "search" in one.lower()


def test_hook_of_a_feature_that_is_off_is_reported(tmp_path):
    code = HELLO.replace('features = ("search",)', "features = ()") + '''
    def search_record(self, doc):
        return {}
'''
    theme = make_theme(tmp_path / "hello", code)
    cfg = write_repo(tmp_path / "repo", "hello", {"one.md": page("One", Tag="a")}, theme_path=str(theme))
    result = run_kb4it("build", cfg, cwd=tmp_path, home=tmp_path)
    assert result.returncode == 0, result.stdout
    assert 'THEME_HOOK_UNUSED theme=' in result.stdout and 'hook=search_record feature=search' in result.stdout


def test_theme_json_contradicting_a_feature_stops_the_build(tmp_path):
    theme = make_theme(tmp_path / "hello", search=False)
    cfg = write_repo(tmp_path / "repo", "hello", {"one.md": page("One", Tag="a")}, theme_path=str(theme))
    result = run_kb4it("build", cfg, cwd=tmp_path, home=tmp_path)
    assert result.returncode == 1
    assert "theme.json 'search' is False, but its features need True" in result.stdout


def test_theme_info_shows_the_public_api(tmp_path):
    theme = make_theme(tmp_path / "hello")
    result = run_kb4it("theme-info", str(theme), "--json", cwd=tmp_path, home=tmp_path)
    assert result.returncode == 0, result.stdout
    info = json.loads(result.stdout[result.stdout.index("{"):])
    assert info["api"] == "BaseTheme" and info["features"] == ["search"]
    assert "missing" not in {t["origin"] for t in info["templates"]}
    hooks = {h["hook"]: h for h in info["hooks"]}
    assert hooks["page_context"]["where"].startswith("logic/theme.py:")
