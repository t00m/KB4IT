---
DocType: Reference
Feature: Getting started, Writing, Publishing
HelpId: faq
Layout: faq
Order: 640
Section: Reference
Summary: Short answers to the questions people ask most about KB4IT.
---

# Frequently asked questions

Short answers. Each one links to the page with the details.

## Do I need a server or a database? {#server}

No. The website is plain files. Open it from disk or copy it to any web server. [Publish on any web server](howto-publish-web-server.md)

## Does it work on Windows or macOS? {#platforms}

KB4IT is developed and tested on GNU/Linux. The websites it makes work in any browser on any system.

## Can I use subfolders in source/? {#subfolders}

No. KB4IT reads the documents directly in `source/`. Use properties such as `Category` or `Topic` to group them instead; they give readers better navigation than folders. [How properties become navigation](explanation-properties.md)

## Can I write in AsciiDoc? {#asciidoc}

No. Older versions used AsciiDoc; KB4IT now reads Markdown only.

## Where do images go? {#images}

In `source/resources/images/`, linked as `resources/images/name.png`. [Add images](howto-write-documents.md#images)

## Can I keep the knowledge base in git? {#git}

Yes, and it is a good idea. Commit `config/` and `source/`, and ignore `var/` and `target/`. [Publish on GitHub Pages](howto-publish-github-pages.md)

## Can I change the theme later? {#change-theme}

Yes. Change `"theme"` in `repo.json` and build with `--force`. Your documents stay the same. [Themes](explanation-themes.md)

## Can I search the site? {#search}

Yes. techdoc and blog have document tables you can filter, bookshelf has a search box, and apphelp has a full-text search. All of it runs in the browser.

## Why did a build compile nothing? {#nothing}

Nothing changed since the last build. That is the fast path working. [Rebuild everything](howto-build.md#force) if you need to.

## How do I start over? {#start-over}

Delete the `var/` and `target/` folders of the knowledge base and build again. Your documents in `source/` are not affected.
