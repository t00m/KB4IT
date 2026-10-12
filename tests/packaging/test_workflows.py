"""The release and CI workflows publish and test what the distribution spec asks for."""

import yaml

from tests.helpers import ROOT

WORKFLOWS = ROOT / ".github" / "workflows"


def load(name):
    return yaml.safe_load((WORKFLOWS / name).read_text(encoding="utf-8"))


def steps_text(job):
    return "\n".join(str(step) for step in job["steps"])


def test_image_job_pushes_to_ghcr_after_a_smoke_test():
    jobs = load("publish.yml")["jobs"]
    image = jobs["image"]
    assert image["needs"] == "check"
    assert image["permissions"]["packages"] == "write"
    assert image["permissions"]["attestations"] == "write"
    text = steps_text(image)
    assert "linux/amd64,linux/arm64" in text
    assert text.index("smoke.sh") < text.index("docker/login-action")
    assert "edge" not in text  # D-3: release tags only
    assert "actions/attest-build-provenance" in text and "'sbom': True" in text


def test_release_waits_for_pypi_and_the_image():
    needs = load("publish.yml")["jobs"]["release"]["needs"]
    assert "publish" in needs and "image" in needs


def test_release_attaches_the_linux_packages():
    jobs = load("publish.yml")["jobs"]
    packages = steps_text(jobs["packages"])
    for arch in ("amd64 arm64", "x86_64 aarch64"):
        assert arch in packages
    assert "test_packages.sh all" in packages
    assert "packages" in jobs["release"]["needs"]
    assert "linux-packages" in steps_text(jobs["release"])


def test_ci_builds_and_tests_the_packages():
    job = load("kb4it.yml")["jobs"]["packages"]
    text = steps_text(job)
    for needed in ("shellcheck", "build_python.sh", "build_tarball.sh", "test_packages.sh all", "smoke.sh",
                   "podman", "retention-days': 7"):
        assert needed in text, needed
