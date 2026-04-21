KB4IT — Turn your AsciiDoc files into a browsable knowledge base
==================================================================

.. image:: https://img.shields.io/pypi/v/KB4IT
   :target: https://pypi.org/project/KB4IT/
   :alt: PyPI

.. image:: https://img.shields.io/pypi/pyversions/KB4IT
   :target: https://pypi.org/project/KB4IT/
   :alt: Python versions

.. image:: https://img.shields.io/badge/license-GPL--3.0--or--later-blue
   :alt: License

.. image:: https://img.shields.io/badge/platform-GNU%2FLinux-lightgrey
   :alt: Platform

**KB4IT** turns a folder of AsciiDoc (``.adoc``) files into a fast, static,
property-indexed website — no database, no JavaScript framework, no runtime.
Write in plain text, commit to git, generate the site, serve the static
files anywhere.

* **Serverless output** — plain HTML/CSS, host on GitHub Pages, S3, nginx,
  or just open ``index.html``
* **Smart incremental builds** — only changed documents are recompiled
  (content-hash based)
* **Property-driven navigation** — every document attribute becomes a
  filterable index page
* **Three themes out of the box** — ``techdoc``, ``book``, ``blog`` — plus
  a theming system if you want your own

Demos: https://github.com/t00m/kb4it-adocs

Quick start
-----------

.. code-block:: bash

    # 1. Install
    pipx install KB4IT

    # 2. Create a new knowledge base
    kb4it create techdoc ~/mykb

    # 3. Build the website
    kb4it build ~/mykb/config/repo.json

    # 4. Open it
    xdg-open ~/mykb/target/index.html

You'll also need the ``asciidoctor`` command on your system.

Why KB4IT?
----------

If you've tried MkDocs, Hugo, Sphinx, or Docusaurus and felt any of:

* "I just want to drop ``.adoc`` files in a folder"
* "I want my metadata (Author, Category, Status…) to become navigation
  automatically"
* "I want the *output* to be static HTML I can rsync anywhere"
* "I don't want Node, Ruby gems, or a 200-plugin config"

…then KB4IT is built for you. It's opinionated, single-purpose, and tries
to stay out of your way.

Installation
------------

KB4IT ships through several channels:

* **pipx** (recommended): ``pipx install KB4IT``
* **pip**: ``pip install --user KB4IT``
* **Docker**: ``docker pull ghcr.io/t00m/kb4it:latest`` *(once published)*
* **Debian/Ubuntu**: ``sudo dpkg -i kb4it_<version>_all.deb``
* **Fedora/RHEL**: ``sudo dnf install kb4it-<version>.noarch.rpm``
* **From source**:
  ``git clone https://github.com/t00m/KB4IT && cd KB4IT && pipx install . --force``

Release artefacts are built with the scripts under ``scripts/distribution/``.

Requirements
------------

* GNU/Linux (tested on Debian, Ubuntu, Fedora)
* Python ≥ 3.11
* ``asciidoctor`` (install via your package manager):

.. code-block:: bash

    sudo apt install asciidoctor    # Debian/Ubuntu
    sudo dnf install asciidoctor    # Fedora

Usage
-----

.. code-block:: bash

    kb4it create <theme> <repo_path>   # scaffold a new repo
    kb4it build <config.json>          # build the site
    kb4it info <config.json>           # show repo stats
    kb4it themes                       # list available themes
    kb4it apps <theme>                 # list theme apps
    kb4it --version                    # show version

A KB4IT repository is just three directories and a config file:

.. code-block::

    mykb/
    ├── config/
    │   └── repo.json       # title, theme, source, target, workers, sort
    ├── source/             # your .adoc files
    └── target/             # generated static website (output)

A minimal ``repo.json``:

.. code-block:: json

    {
      "title":   "My Knowledge Base",
      "tagline": "Notes I don't want to lose",
      "theme":   "techdoc",
      "sort":    "Date",
      "force":   false,
      "workers": 4,
      "source":  "/home/me/mykb/source",
      "target":  "/home/me/mykb/target"
    }

Themes
------

* **techdoc** — Technical documentation, runbooks, knowledge bases.
  Dense, searchable, property-heavy navigation.
* **book** — Long-form structured content. Chapter/section layout.
* **blog** — Chronological posts with tags/categories.

Custom themes live in ``~/.kb4it/opt/resources/themes/``.

Contributing
------------

Contributions are very welcome — especially bug reports with a minimal
reproducing repo, new themes, documentation improvements, and performance
work on the compiler / builder.

.. code-block:: bash

    git clone https://github.com/t00m/KB4IT
    cd KB4IT
    pipx install . --force
    kb4it --version

Open an issue before starting a large change so we can align on the
approach.

Roadmap / known limitations
---------------------------

* Documentation is thinner than the code deserves — help wanted
* No online editor by design — use your preferred editor
* No dynamic search — KB4IT aims to stay small and serverless
* API is still evolving; minor releases may change internals
* When a linked document's properties change, related property pages may
  need a ``--force`` rebuild to refresh titles

Credits
-------

* `Python <http://www.python.org/>`_ — the language KB4IT is written in
* `Asciidoctor <https://asciidoctor.org>`_ — text processor and publishing
  toolchain
* `UIKit <https://getuikit.com>`_ — the front-end framework used by the
  default themes
* `Geany <https://www.geany.org/>`_ — the editor used to build KB4IT

License
-------

KB4IT is released under the `GNU GPL v3 or later <LICENSE>`_.

Contact
-------

Tomás Vírseda (aka **t00m**) — tomasvirseda@gmail.com

If KB4IT is useful to you, star the repo — it genuinely helps me decide
where to spend time. Issues, ideas, and PRs are all welcome.
