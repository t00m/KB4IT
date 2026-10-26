---
DocType: How-to guide
Feature: Development
HelpId: dev-release
Keyword: release, version, tag, pypi, ghcr, container, deb, rpm, changelog, release notes, semver, build version, theme version, build stamp, doctor
Level: advanced
Order: 730
Section: Reference
Summary: Cut a KB4IT release, from the changelog to PyPI, the container image and the GitHub release.
---

# Release a version

This is for maintainers. `RELEASING.md` in the repository has every detail and the reasons behind each step.

## How versions work {#versions}

- `kb4it/VERSION` names the release being prepared, for example `X.Y.Z`. Only `scripts/release.sh` changes it.
- KB4IT follows [Semantic Versioning](https://semver.org/). While the major number is 0, a change that breaks sites or themes raises the minor number.
- Every build knows its commit. `kb4it --version` prints `KB4IT X.Y.Z` for the clean commit of tag `vX.Y.Z` and `KB4IT X.Y.Z-dev+<n>.g<sha7>` for any other commit (`.dirty` with uncommitted changes), then the full commit and build date. Packages carry it in `kb4it/BUILD.json`, written by `scripts/devel/stamp_build.py` before the build.
- A site built by another build, even another commit of the same version, is rebuilt once on its next build.
- Each theme has its own `version` in `theme.json`, independent of KB4IT's. Raise it (patch, minor or major) once per release in which the theme's files changed. CI warns about a theme that changed without a new version; the release refuses it.

## Steps {#steps}

1. Fetch the release tags, which the theme version check needs, and see what would happen; this writes nothing:

        git fetch --tags
        scripts/release.sh --dry-run

2. Prepare: set the version, date the changelog and draft the notes:

        scripts/release.sh

3. If a bundled theme started using new core features since the last release, raise its `kb4it` requirement in `theme.json` to the new version now, and commit only those files. It cannot be done earlier, because the version files still name the previous release until step 2. `RELEASING.md` has the commands.

   Then raise the `version` of every theme that changed since the last release, and commit only the `theme.json` files. This lists them:

        ./scripts/devel/check_themes.sh --worktree --changed

4. Edit `releases/X.Y.Z.md` for someone deciding whether to update: one sentence, then the changes they would notice, with what can break a script, a site or a custom theme under "Before you upgrade". Delete the `TODO` line.

5. Check and commit. This runs the tests, the theme check (a changed theme needs a new version) and the wheel check (themes, offline help and build stamp), and commits `chore(release): X.Y.Z` only if all pass:

        scripts/release.sh --commit

6. Open a pull request to `master`, let CI pass and merge it. Then tag the merge commit:

        git checkout master && git pull --ff-only
        git tag vX.Y.Z && git push origin vX.Y.Z

7. The tag starts `.github/workflows/publish.yml`. It checks that the tag, the version files, the changelog and the notes agree, runs the tests and the theme check, stamps the build and refuses a wheel without the release stamp, and publishes to PyPI. From the same wheel it pushes the container image `ghcr.io/t00m/kb4it` (amd64 and arm64) and builds the `.deb` and `.rpm`. When all of that succeeded it creates the GitHub release with the packages attached. If a job fails for a transient reason, use **Re-run failed jobs** on that run; if the cause is in the tagged code, fix it and release the next patch version. Never move a tag.

8. Install the new version from PyPI in a new virtual environment and check it: the first line of `kb4it --version` must be exactly `KB4IT X.Y.Z`, and this must pass, which runs `kb4it doctor` and builds every sample app of every theme from the installed package:

        python3 scripts/devel/smoke_build.py --doctor --all-apps

   Then open the next cycle:

        scripts/release.sh --open X.Y.Z

!!! note "Once, after the first release with an image"
    New packages on GitHub are private. Open your profile, **Packages**, `kb4it`, **Package settings**, and change the visibility to **Public**, so everyone can pull the image. `RELEASING.md` has the details.

!!! important "Themes declare the KB4IT they need"
    When a theme starts using something new from the core, raise the `kb4it` requirement in its `theme.json` in the same change. The theme check refuses a release whose themes need a newer KB4IT.
