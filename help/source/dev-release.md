---
DocType: How-to guide
Feature: Development
HelpId: dev-release
Keyword: release, version, tag, pypi, ghcr, container, deb, rpm, changelog, release notes, semver
Level: advanced
Order: 730
Section: Development
Summary: Cut a KB4IT release, from the changelog to PyPI, the container image and the GitHub release.
---

# Release a version

This is for maintainers. `RELEASING.md` in the repository has every detail and the reasons behind each step.

## How versions work {#versions}

- `kb4it/VERSION` names the release being prepared, for example `0.8.0`. Only `scripts/release.sh` changes it.
- KB4IT follows [Semantic Versioning](https://semver.org/). While the major number is 0, a change that breaks sites or themes raises the minor number.
- A build from a clone adds `git describe` to `kb4it --version`, so development builds need no extra numbering.

## Steps {#steps}

1. See what would happen; this writes nothing:

        scripts/release.sh --dry-run

2. Prepare: set the version, date the changelog and draft the notes:

        scripts/release.sh

3. If a bundled theme started using new core features since the last release, raise its `kb4it` requirement in `theme.json` to the new version now, and commit only those files. It cannot be done earlier, because the version files still name the previous release until step 2. `RELEASING.md` has the commands.

4. Edit `releases/X.Y.Z.md` for someone deciding whether to update: one sentence, then the changes they would notice. Delete the `TODO` line.

5. Check and commit. This runs the tests, the theme check and the wheel check, and commits `chore(release): X.Y.Z` only if all pass:

        scripts/release.sh --commit

6. Open a pull request to `master`, let CI pass and merge it. Then tag the merge commit:

        git checkout master && git pull --ff-only
        git tag vX.Y.Z && git push origin vX.Y.Z

7. The tag starts `.github/workflows/publish.yml`. It checks that the tag, the version files, the changelog and the notes agree, runs the tests and the theme check, and publishes to PyPI. From the same wheel it pushes the container image `ghcr.io/t00m/kb4it` (amd64 and arm64) and builds the `.deb` and `.rpm`. When all of that succeeded it creates the GitHub release with the packages attached. If a job fails for a transient reason, use **Re-run failed jobs** on that run; if the cause is in the tagged code, fix it and release the next patch version. Never move a tag.

8. Install the new version from PyPI to check it, then open the next cycle:

        scripts/release.sh --open 0.9.0

!!! note "Once, after the first release with an image"
    New packages on GitHub are private. Open your profile, **Packages**, `kb4it`, **Package settings**, and change the visibility to **Public**, so everyone can pull the image. `RELEASING.md` has the details.

!!! important "Themes declare the KB4IT they need"
    When a theme starts using something new from the core, raise the `kb4it` requirement in its `theme.json` in the same change. The theme check refuses a release whose themes need a newer KB4IT.
