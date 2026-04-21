= Help

:SystemPage: Yes

// END-OF-HEADER. DO NOT MODIFY OR DELETE THIS LINE

== What is KB4IT?

KB4IT is a *static website generator* for technical knowledge bases.
It converts plain-text https://asciidoctor.org[AsciiDoc] documents into a fully
navigable HTML website — no database, no server, no login required.

Every document is a `.adoc` file in your source directory.
Every property you add to a document header (Author, Category, Status, …)
becomes a navigable index automatically.
The result is a self-contained folder of HTML files you can open in any browser,
host on any web server, or check into a Git repository.

== Writing documents

=== Document structure

Every KB4IT document has two sections separated by a mandatory marker:

. *Header* — title + properties
. *Body* — free-form AsciiDoc content

----
= Title of the document

:Author:    Jane Doe
:Category:  Runbook
:Status:    Released
:Scope:     Infrastructure
:Team:      Platform

// END-OF-HEADER. DO NOT MODIFY OR DELETE THIS LINE

== First section

Write your content here using AsciiDoc syntax.
----

The line `// END-OF-HEADER. DO NOT MODIFY OR DELETE THIS LINE` is *required*.
Everything above it is the header; everything below is the body.

=== Properties

Properties are key-value pairs enclosed in colons:

----
:PropertyName:  Value
----

You can use any property name you like.
KB4IT automatically creates an index page for every property and a
filtered page for every value — for example `:Category: Runbook` produces
`Category.html` and `Category_Runbook.html`.

Built-in properties recognised by KB4IT:

[cols="1,3", options="header"]
|===
| Property | Meaning
| `Title`       | Document title (set by the `= ...` heading)
| `Author`      | Author name(s), comma-separated
| `Date`        | Publication date used for sorting (`YYYY-MM-DD`)
| `Category`    | High-level classification
| `Scope`       | Audience or applicability
| `Status`      | Lifecycle state (e.g. Draft, Released, Archived)
| `DocType`     | Diátaxis type: Tutorial, How-to guide, Reference, Explanation
| `Bookmark`    | Set to `Yes` to pin the document in the Bookmarks page
| `SystemPage`  | Internal marker — do *not* use in your own documents
|===

Any other property you define works exactly the same way.

=== AsciiDoc quick reference

[cols="1,2", options="header"]
|===
| Element | Syntax
| Bold | `*bold text*`
| Italic | `_italic text_`
| Monospace | `\`code\``
| Link | `https://example.com[Label]`
| Section heading | `== Section` / `=== Subsection`
| Ordered list | `. Item one` / `. Item two`
| Unordered list | `* Item`
| Code block | `----` … `----`
| Note | `NOTE: your note text`
| Tip | `TIP: your tip text`
| Warning | `WARNING: your warning text`
| Image | `image::path/to/image.png[Alt text]`
| Table | See https://docs.asciidoctor.org/asciidoc/latest/tables/build-a-basic-table/[AsciiDoc tables]
|===

Full reference: https://docs.asciidoctor.org/asciidoc/latest/syntax-quick-reference/[AsciiDoc Syntax Quick Reference]

== Building the website

=== Prerequisites

* Python ≥ 3.11 on GNU/Linux
* `asciidoctor` command available in your PATH

----
# Install asciidoctor (Debian/Ubuntu/Fedora)
sudo apt install asciidoctor     # Debian/Ubuntu
sudo dnf install asciidoctor     # Fedora

# Install KB4IT
pipx install kb4it
----

=== Creating a new repository

----
kb4it create techdoc /path/to/my-kb
----

This creates a `repo.json` config file and an example source directory.

=== Building

----
kb4it build /path/to/my-kb/repo.json
----

On the first run KB4IT compiles every document.
On subsequent runs only changed documents are recompiled (incremental build).
Use `--force` to recompile everything:

----
kb4it build /path/to/my-kb/repo.json --force
----

=== Repository configuration (`repo.json`)

[cols="1,1,3", options="header"]
|===
| Key | Default | Description
| `title`    | —          | Website title
| `tagline`  | —          | Subtitle shown on the landing page
| `theme`    | `techdoc`  | Theme name
| `source`   | —          | Path to your `.adoc` files
| `target`   | —          | Output directory for the generated website
| `workers`  | `auto`     | Number of parallel compilation workers
| `force`    | `false`    | Always recompile all documents when `true`
| `datatable`| `[]`       | Columns shown in document tables (property names)
| `events`   | `[]`       | Categories treated as events on the calendar
|===

== What to expect

=== Navigation

* *Landing page* — stats, Diátaxis type cards, upcoming and recent events
* *Properties* — word cloud of all property names; click any to explore its values
* *Stats* — document and property counts with proportional bar chart
* *Bookmarks* — documents marked `:Bookmark: Yes`
* *Events* — calendar view of documents whose Category matches `repo.json → events`
* *All documents* — searchable, sortable table of every document

=== Incremental builds

KB4IT tracks a hash of every document's metadata and body separately.
Only documents that actually changed are recompiled.
Key-value index pages are rebuilt only when their document set changes,
or when any listed document's metadata changes.

=== Themes

Three built-in themes are available:

[cols="1,3", options="header"]
|===
| Theme | Description
| `techdoc` | Technical documentation — the theme you are reading now
| `book`    | Long-form book or manual layout
| `blog`    | Chronological blog with excerpts
|===

You can install custom themes in `~/.kb4it/opt/resources/themes/`.

== Frequently asked questions

*My document doesn't appear after building.*

Check that the header ends with the exact line
`// END-OF-HEADER. DO NOT MODIFY OR DELETE THIS LINE`
and that the document has a valid `:Date:` property.
Run with `--force` to rule out cache issues.

*I added a property but no index page was created.*

Make sure the property name is not listed under `ignore` or `block` in
your `repo.json`. Also check that at least one document has a non-empty
value for that property.

*The build is slow.*

Increase `workers` in `repo.json`.
On a subsequent run after the first full build, only changed files are
recompiled — the build will be much faster.

*Can I use KB4IT without Git?*

Yes. Git integration is optional.
Set `"git": false` in `repo.json` to disable the Edit button and
"New document" shortcut in the navigation bar.

*Where are the logs?*

Logs are written to `~/.kb4it/var/log/`.

*Can I override any system page?*

Yes — place a file with the same name as the system page
(e.g. `help.adoc`, `index.adoc`) in your source directory.
KB4IT will use your version instead of generating one automatically.

== Getting help & reporting issues

[cols="1,3", options="header"]
|===
| Resource | Link
| Bug reports & feature requests | https://github.com/t00m/KB4IT/issues[github.com/t00m/KB4IT/issues]
| Source code | https://github.com/t00m/KB4IT[github.com/t00m/KB4IT]
| AsciiDoc reference | https://docs.asciidoctor.org/asciidoc/latest/[docs.asciidoctor.org]
|===

When opening an issue, please include:

* KB4IT version (`kb4it --version`)
* Operating system and Python version
* The command you ran
* Relevant lines from `~/.kb4it/var/log/`
