# KB4IT help center design

Status: draft, waiting for approval.
Date: 2026-10-20

## Intent

KB4IT already ships a help site: the `help/` folder, built with the apphelp theme and published to GitHub Pages. It is not yet the single place users and developers go for information, doubts, tricks and questions. This design makes it that place.

The help center is the official documentation. It ships inside the installed package, so it works offline, and it is also published online. Every release updates it.

## Why

- A user who installs KB4IT gets no pointer to the docs. The first useful thing (where the docs are) is missing.
- Docs that live only online fail for users without a connection, on servers and on air-gapped machines.
- Docs that drift from the code mislead people. The docs must be built and checked with each version.

## Goals

1. Full coverage: every command, option, `repo.json` key, document property, theme and error code that a user can meet has a page.
2. Four kinds of page, each with one job: learn by doing, solve a task, look up facts, understand why. Each kind is clearly labeled. The site never uses the name of the framework behind the split.
3. One place for questions: a page for common questions, tips, and known problems, each with a path to ask for more help.
4. Offline copy in the installed package. Opening it needs no network and no extra tools.
5. Online copy on GitHub Pages, built from the same source as the offline copy.
6. A first-run notice tells the user the help center exists and how to open it.
7. Each release rebuilds and republishes the help center, and the site shows the version it documents.

## Non-goals

- A search server or any service outside GitHub Pages.
- Translations. English only for this version.
- Rewriting the apphelp theme. Changes to it are allowed only when a page needs one.
- Docs for the internals of KB4IT beyond what a contributor needs to start. Contributor pages already exist under `dev-*`; they stay, but they are not the focus.

## Anti-goals

- A help center that is complete on paper but wrong about the code. Every page that names a command, key or property must match the code. The build checks this.
- Notices that cannot be dismissed, or that print on every command. The notice stops once the user dismisses it.
- Hidden network calls. The help never phones home.

## Constraints

- pip and uv do not run code after install. The first-run notice therefore appears the first time a user runs `kb4it`.
- The offline copy must be inside the wheel and the sdist (`pyproject.toml` already includes `kb4it/resources/**`).
- The online copy must work on GitHub Pages with the existing `help.yml` workflow. Settings > Pages > Source stays "GitHub Actions".
- The build must not need network access. Search and links work with plain files.
- Phone-width layout is not a goal for the help, but nothing may break at phone width.

## Decisions

### Decided by the user

- Both an online copy (GitHub Pages) and an offline copy (inside the package).
- The notice shows on every `kb4it` start until the user dismisses it.

### Decided by me (my call)

- **Section names.** The sections are plain names for the four kinds: "Start here" (learn by doing), "Guides" (solve a task), "Reference" (look up facts), "Concepts" (understand why). The site does not name any framework.
- **Questions.** A "Questions" section holds the FAQ, tips, troubleshooting and a link to GitHub issues. These pages already exist and move there.
- **Offline build.** A build script runs the apphelp theme over `help/` and writes the result to `kb4it/resources/help/`. The output is committed for releases only, so a normal commit does not carry it. Release tooling runs the script and includes the output in the wheel and sdist. (Alternative: generate it at install time. Rejected: the install step has no hook.)
- **Dismiss.** The notice ends with the command `kb4it help --dismiss`. A marker file under `KB4IT_HOME` (or `~/.kb4it`) records the choice. Until then, every `kb4it` start prints one notice line with the path to the offline copy and the online URL. The TUI shows the same text as a banner until dismissed.
- **Open.** `kb4it help` opens the offline copy in the browser. `kb4it help --url` prints the online URL only.
- **Version.** Each page of the site shows the version it documents, read from `kb4it/VERSION` at build time. The online copy at master shows the development version. The release build shows the release version.
- **Coverage check.** A test lists every CLI command, every key in the repo.json reference, every bundled theme and every error code, and fails when a name has no page. It checks names only, not prose.
- **Diataxis labels.** The four kinds map to the four section names above. A test fails if the built site contains the framework name.

## Open items for the builder

- The exact coverage gap list. This comes from the first run of the coverage check, not from this spec.
- Size of the offline copy. Measure it on the first build. Report it to the user if it adds more than 5 MB to the wheel.
- Whether the apphelp theme needs a version field. Check first; add one only if the page cannot show the version another way.

## Done when

- `kb4it help` opens the offline copy with no network, on Linux, macOS and Windows.
- A fresh install prints the notice on the first `kb4it` run and stops after `kb4it help --dismiss`.
- The GitHub Pages site builds from the same source on each push to master and on each release.
- The coverage test passes. Every command, key, theme and error code has a page.
- The site has no framework name in any page, and every page names its section.
