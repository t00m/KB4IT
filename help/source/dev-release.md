---
DocType: How-to guide
Feature: Development
HelpId: dev-release
Keyword: release, version, tag, pypi, changelog, release notes, semver
Level: advanced
Order: 730
Section: Development
Summary: Cut a KB4IT release, from the changelog to PyPI and the GitHub release.
---

# Release a version

This is for maintainers. `RELEASING.md` in the repository has every detail and the reasons behind each step.

## How versions work {#versions}

- `kb4it/VERSION` names the release being prepared, for example `0.8.0`. Only `scripts/release.sh` changes it.
- KB4IT follows [Semantic Versioning](https://semver.org/). While the major number is 0, a change that breaks sites or themes raises the minor number.
- A build from a clone adds `git describe` to `kb4it --version`, so development builds need no extra numbering.

## Steps {#steps}

1. See what would happen; this writes nothing:

    ```bash
    scripts/release.sh --dry-run
    ```

2. Prepare: set the version, date the changelog and draft the notes:

    ```bash
    scripts/release.sh
    ```

3. Edit `releases/X.Y.Z.md` for someone deciding whether to update: one sentence, then the changes they would notice. Delete the `TODO` line.

4. Check and commit. This runs the tests, the theme check and the wheel check, and commits `chore(release): X.Y.Z` only if all pass:

    ```bash
    scripts/release.sh --commit
    ```

5. Open a pull request to `master`, let CI pass and merge it. Then tag the merge commit:

    ```bash
    git checkout master && git pull --ff-only
    git tag vX.Y.Z && git push origin vX.Y.Z
    ```

6. The tag starts `.github/workflows/publish.yml`. It checks that the tag, the version files, the changelog and the notes agree, runs the tests and the theme check, publishes to PyPI and creates the GitHub release.

7. Install the new version from PyPI to check it, then open the next cycle:

    ```bash
    scripts/release.sh --open 0.9.0
    ```

!!! important "Themes declare the KB4IT they need"
    When a theme starts using something new from the core, raise the `kb4it` requirement in its `theme.json` in the same change. The theme check refuses a release whose themes need a newer KB4IT.
