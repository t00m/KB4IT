---
DocType: Explanation
Feature: Development
HelpId: dev-architecture
Keyword: services, workflow, backend, processor, compiler, builder, frontend, deployer, kbdict, BuildPlan, cache
Level: advanced
Order: 710
Section: Development
Summary: How KB4IT is put together, from the command line to the files in target/, and how incremental builds work.
---

# How KB4IT is built

KB4IT is a Python package (`kb4it/`) built around a small controller and a set of services. `AGENTS.md` at the root of the repository is the full reference; this page is the map.

## The controller and the services {#services}

`KB4IT` in `kb4it/core/main.py` reads the command line, takes the process lock, sets up logging and registers the services. Each service asks the controller for the others by name.

| Service | File | Job |
|---|---|---|
| Workflow | `services/workflow.py` | Runs a command: build, create, verify, info, the lists |
| Backend | `services/backend.py` | Loads `repo.json`, resolves the folders, owns the build state |
| Database | `services/database.py` | Documents and their properties, in memory |
| Processor | `services/processor.py` | Reads the properties and decides what to compile |
| Compiler | `services/compiler.py` | Markdown to HTML, in parallel |
| Builder | `services/builder.py` | Base class of every theme: templates and pages |
| Frontend | `services/frontend.py` | Finds, checks and loads the theme |
| Deployer | `services/deployer.py` | Copies the result to `target/` |

The terminal interface (`kb4it/tui/app.py`) is a Textual application. It creates the same controller for each build and runs it on a separate thread of its own process.

## A build, stage by stage {#stages}

```text
kb4it build repo.json
  Workflow.build_website()
    1  Backend.stage_01_check_environment   folders, theme load, required templates
       Theme.generate_sources()
    2  Backend.stage_02_get_source_documents
    3  Backend.stage_03_process_sources     Processor: properties, hashes, BuildPlan
    4  Backend.stage_04_process_theme       Theme.build()
    5  Backend.stage_05_compilation         Compiler, then Theme.build_page() per page
    6  Theme.post_activities()
    7  Backend.stage_06_deploy              Deployer
    8  Theme.post_deploy_activities()
```

Each stage logs `[WORKFLOW] STAGE n=...`, and its time shows as `[PERFORMANCE]` at `DEBUG` level. Errors are typed (`ConfigError`, `ThemeError`, `CompilationError`, `KB4ITError`) and caught once in `KB4IT.run()`, which turns them into exit status 1.

## Incremental builds {#incremental}

The cache is `var/db/kbdict.json` in each knowledge base. For every document it stores two blake2b hashes: one of the body without the title, one of the properties.

- A changed body recompiles the document.
- Changed properties recompile the document and every property and value page it appears on.
- A new or removed document refreshes the pages of its properties.
- A theme whose `site_signature()` changes, or a new KB4IT version, recompiles everything.

The Processor turns this into a `BuildPlan`: the documents to compile and the property pages to refresh. Compiled HTML is kept in `var/cache/`, so unchanged pages are copied instead of rebuilt.

## Themes {#themes}

A theme's `logic/theme.py` subclasses `Builder`. The core calls its hooks at the stages above and renders its Mako templates. Template lookup tries the theme's `templates/` first, then `kb4it/resources/common/templates/`. See [Create your own theme](howto-create-theme.md).

## Where things are {#paths}

| Path | Holds |
|---|---|
| `kb4it/core/` | Controller, environment, logging, helpers, version checks |
| `kb4it/services/` | The services above |
| `kb4it/resources/themes/` | The bundled themes |
| `kb4it/resources/common/` | Shared templates and images |
| `kb4it/tui/` | The terminal interface |
| `tests/` | The test suite |
| `help/` | This help |
