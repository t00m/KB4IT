---
DocType: How-to guide
Feature: Writing
HelpId: skill
Keyword: ai, assistant, claude, skill, kb4itdoc, quality, techdoc, worktype
Level: basic
Order: 217
Related: reference-theme-techdoc.md, howto-write-documents.md
Section: Guides
Summary: Give an AI assistant the kb4itdoc skill so the techdoc documents it writes have the right properties, sections and quality.
---

# Write with an AI assistant

KB4IT ships a skill for AI assistants: `kb4itdoc`. It is one Markdown file with the rules of a techdoc document: the mandatory properties, the `Category` and `WorkType` pairs, the skeleton sections, the writing style and what the [quality score](reference-theme-techdoc.md#quality) checks. With it, an assistant can write a new document, convert an old one or review one, and tell you what keeps it from the Exemplary tier.

## Find the skill {#find}

The file is `kb4it/resources/skills/kb4itdoc/SKILL.md`, in the KB4IT source tree and in every installed copy. To find the installed one:

```bash
python3 -c "import kb4it, os; print(os.path.join(os.path.dirname(kb4it.__file__), 'resources', 'skills', 'kb4itdoc'))"
```

Use the `python3` of the environment KB4IT is installed in.

## Install it in Claude Code {#claude-code}

Copy the `kb4itdoc` folder to one of the skill folders of Claude Code:

1. For every project: `~/.claude/skills/kb4itdoc/`.
2. For one knowledge base only: `.claude/skills/kb4itdoc/` at the top of its repository.

```bash
cp -r "$(python3 -c "import kb4it, os; print(os.path.join(os.path.dirname(kb4it.__file__), 'resources', 'skills', 'kb4itdoc'))")" ~/.claude/skills/
```

Claude Code loads it when you ask for a KB4IT document, for example "write a KB4IT procedure to renew the web certificates" or "review INCIDENT-DISK-FULL.md for KB4IT".

Copy it again after you upgrade KB4IT: the skill follows the rules of the version it ships with.

## Use it with another assistant {#other}

Give the assistant the content of `SKILL.md` as instructions, then ask for the document. Ask it to read the whole file first: the checklist at the end depends on every section.

## What to check in the result {#check}

The skill asks the assistant for information it cannot infer, such as the author or a source, instead of inventing it. Still check these before you save:

- `Category` and `WorkType` go together: `WorkType: Knowledge` with Procedure, Note, Post or Report; `Change`, `Incident` or `Task` with `Category: Record`; `Meeting` with `Category: Minutes`.
- Links to other documents point to files that exist. A broken link costs 3 points.
- The References section lists real sources.

Then build the site and open the **Quality** tab of the document to see its score.
