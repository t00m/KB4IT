---
name: kb4itdoc
description: "Use this skill whenever the user asks to create, draft, convert, migrate, or review a KB4IT document in Markdown (.md) format. Triggers include: \"write a KB4IT doc\", \"convert this to KB4IT\", \"create a doc for KB4IT\", \"draft a runbook, change, incident, task, meeting minutes, note, post or report for KB4IT\", \"turn this into a KB4IT document\", \"update this old KB4IT doc to the new properties\", or any request to produce a .md file intended for a KB4IT repository (techdoc theme). Also trigger when the user asks about KB4IT document structure, property conventions, Category, WorkType, DocType, Summary, skeletons, the quality score, or YAML frontmatter usage. Do NOT use for KB4IT Python development tasks."
---

# KB4IT Document Authoring Skill

This skill governs the creation, conversion and review of KB4IT source documents in
**Markdown** (`.md`) format, as defined by the KB4IT release it ships with and its **techdoc** theme.
KB4IT reads the YAML frontmatter of each file and turns every property into navigation,
dashboard panels, a calendar and a quality score.

This skill ships with KB4IT (`kb4it/resources/skills/kb4itdoc/SKILL.md`). It follows the
rules techdoc checks when it scores a document, so a document written with it reaches the
**Exemplary** tier once its links and sources are in place (Section 17).

**Standard source format: Markdown (`.md`)**, the only supported format.

What changed from older releases, in short:

- `Category` is now the **form** of the document. The **type of work** moved to the new `WorkType` property,
  which **every** document carries: `Knowledge` for knowledge documents, `Change`, `Incident`, `Task` or `Meeting` for records.
- A fixed set of **core properties** is mandatory, plus `Summary`.
- `Version` is **no longer used**. Never write it, and remove it when converting or reviewing.
- The body of every document follows the **skeleton** of its Category (`WorkType: Knowledge`) or of its WorkType (records).

---

## 0. Mandatory pre-flight rules

Before producing, rewriting, or reviewing any KB4IT document, do both of these, in order. Skipping either step is not allowed.

1. **Read this `kb4itdoc` skill completely.** Read the whole `SKILL.md` from start to finish before writing, not just the section that looks relevant.
2. **Apply the writing rules of Section 15** to every word of the document, code comments included. If a writing-style skill such as `nonia` is installed, apply it too. The em dash ban is absolute: never use the em dash character (U+2014), not once, in any context. Replace it with a comma, a colon, a period, or rewrite the sentence.

After writing, scan the finished document for the em dash (U+2014) and remove every instance before presenting it.

---

## 1. File Naming

- Filename: **UPPERCASE**, **hyphens** as separators.
- Extension: always `.md`.
- Must be descriptive and reflect the document's content.
- Examples:
  - `INFRA-SENTINELONE-AGENT-SETUP.md`
  - `LINUX-KERNEL-UPGRADE.md`
  - `CHANGE-QAS-KERNEL-UPDATE.md`

Always suggest a filename when producing a document.

---

## 2. Document Structure

```
---
<YAML frontmatter properties>
---

# <Title>

## <Skeleton section 1>
## <Skeleton section 2>
## <Skeleton section n>
## References
```

- The **YAML frontmatter block** (between `---` delimiters) contains all KB4IT properties.
- Leave **one blank line** between the closing `---` and the level-1 title heading.
- The title is the **level-1 heading** (`# Title`). Never write a `Title:` property: KB4IT
  ignores it and warns `title_in_frontmatter_ignored`.
- Body sections use `##` (and `###`, `####` below them). The `##` sections come from the
  skeleton (Section 9).
- **There is no EOHMARK**. The closing `---` of the frontmatter is the header boundary.

---

## 3. Header Properties: General Rules

- Property names must be **singular** and **first-letter uppercase** (e.g. `Tag`, `Product`, `OS`).
  Compound names follow KB4IT's own style without spaces (e.g. `WorkType`, `DocType`).
- **Avoid property names with spaces** (e.g. prefer `OS` over `Operating System`).
  If a natural property name would contain spaces, **ask the user for their preferred name**
  before proceeding. Do not invent a short-form name on your own.
- Multiple values on one line, **comma-separated**: `Tag: invoice, printout, email`.
  KB4IT splits on commas, so a single value can never contain a comma. The only exception is
  `Summary`, which KB4IT joins back into one sentence.
- Quote a value with double quotes when YAML needs it: when it contains `: `, or starts with
  `[`, `{`, `#`, `&`, `*`, `!`, `|`, `>`, `%` or `@`. Example: `Summary: "Backups: how they run"`.
- No duplicate property keys in the same document (KB4IT keeps the last one and warns `duplicate_property`).
- **Property ordering:** all properties must be listed in **strict alphabetical order** by property name.
- **`Version` is not used anymore.** Do not add it. Remove it from any document you convert or review.
- **No cross-property value duplication (STRICT RULE):** a value must appear in **exactly one property**.
  This is non-negotiable. After drafting all properties, perform a mandatory cross-property scan
  (case-insensitive) and eliminate every duplicate, retaining the value only in the most specific
  property. `Tag` is always the least specific property.

### YAML frontmatter syntax

| Concept | Markdown (YAML frontmatter) |
|---|---|
| Property key | `Author: value` |
| Multi-value | `Tag: permission, printout` |
| Value with `: ` | `Summary: "Backups: how they run"` |
| Title | `# Title` (one blank line after closing `---`) |
| Header boundary | `---` (YAML closing delimiter) |

---

## 4. Mandatory Properties

Every document must include **all** of the following. These are the techdoc **core keys**
plus `Summary`. The quality score checks each one, and a document missing any of them is malformed
for this skill.

| Property | Description | Rule |
|---|---|---|
| Title | Document title | `# Title` heading, one blank line after frontmatter |
| `Author` | Author name | Ask if unknown |
| `Category` | Form of the document | Exactly one value, see Section 5 |
| `Date` | Creation/revision date | `YYYY-MM-DD`, `YYYY-MM-DD HH:MM` or `YYYY-MM-DD HH:MM:SS` |
| `DocType` | Diátaxis classification | Exactly one value, see Section 7 |
| `Product` | Product(s) the document is about | See Section 11; never a database engine name |
| `Scope` | Area of responsibility | See Section 12 known values |
| `Status` | Lifecycle state | One known value, see Section 8 |
| `Summary` | One line describing the document's purpose | See Section 4a |
| `Tag` | Generic keywords | At least one; see Section 10 |
| `Topic` | Subject of the document | See Section 12 known values |
| `WorkType` | Type of work | Exactly one value; `Knowledge` for every non-record document; see Section 6 |

### Filling the mandatory properties

- **Infer every value from the content first.** A document about a kernel update on RHEL has
  `Product: RHEL`, `Topic: Upgrade`, `Scope: Unix Administration` without asking.
- **If no value fits, ask the user before leaving a key empty.** Explain which key is missing a
  value and offer the candidates you considered. Only write an empty key (`Product:`) when the user
  confirms there is no meaningful value. KB4IT reads an empty key as "no values".
- Never invent a placeholder value such as `Unknown`, `N/A` or `TBD` to fill a key.

### 4a. Summary

`Summary` is shown under the title on the document page, in search results and in link previews.
It tells the reader in one line **what the document is for**.

- **One sentence, one line.** No line breaks. Aim for about 10 to 25 words.
- Describe the purpose or the outcome, not the document: "Update the SAP kernel of the quality
  system before production." not "This document describes the kernel update."
- For records, say what happened or what must happen: "The nightly invoice job ran out of memory
  after month-end; invoices went out four hours late."
- Do not repeat the title word for word.
- End with a period. Apply the writing rules of Section 15 (no em dash).
- Quote it when it contains `: ` (Section 3).
- `Summary` is free text: it is **excluded** from the cross-property deduplication scan.

---

## 5. Category: Form of the Document

`Category` is the **form** of the document, not the type of work. Exactly **one** of:

| Value | Use for | WorkType |
|---|---|---|
| `Procedure` | Operational procedure, runbook, recurring check | `Knowledge` |
| `Note` | Knowledge note: concept, background, comparison, observation | `Knowledge` |
| `Post` | Blog-style post, announcement or article | `Knowledge` |
| `Report` | Status, analysis or capacity report with findings | `Knowledge` |
| `Record` | Record of work: a change, an incident or a task | `Change`, `Incident` or `Task` |
| `Minutes` | Notes of a meeting | `Meeting` |

- `Template` exists in techdoc but is **not used** by this skill. If a document looks like a
  template, ask the user how to classify it. If the user decides to use it, it takes `WorkType: Knowledge`.
- If the document fits none of these values, ask the user before proceeding.
- **Old values are invalid.** In older releases, `Category` held the type of work
  (`Change`, `Incident`, `Task`, `Meeting`). See Section 14 for the migration.

---

## 6. WorkType: Type of Work

Every document has a `WorkType`. It separates **knowledge documents** (`WorkType: Knowledge`) from
**records** (`Change`, `Incident`, `Task`, `Meeting`). techdoc uses it for the latest changes and
incidents, **Open items**, the calendar and the choice of skeleton.

| WorkType | Category | Meaning |
|---|---|---|
| `Knowledge` | `Procedure`, `Note`, `Post`, `Report` | Knowledge to keep and reuse |
| `Change` | `Record` | Planned or completed change to a system, process or component |
| `Incident` | `Record` | Unexpected disruption or degradation of a service |
| `Task` | `Record` | Work item or action to track until done |
| `Meeting` | `Minutes` | Meeting, review or discussion |

Rules:

- `WorkType` is **mandatory** and takes exactly **one** value.
- The pairing is fixed:
  - `Procedure`, `Note`, `Post` and `Report` always go with `WorkType: Knowledge`.
  - `Change`, `Incident` and `Task` always go with `Category: Record`.
  - `Meeting` always goes with `Category: Minutes`.
- A record is any document whose `WorkType` is not `Knowledge`.
- techdoc checks both rules: a missing `WorkType` costs one point, and a `Category` that does not
  go with the `WorkType` costs three (Section 17).
- Records should carry a `Date` with time (`YYYY-MM-DD HH:MM`) when it is known: it places them in
  the calendar.

---

## 7. DocType: Diátaxis Framework

`DocType` must be exactly one of these four values:

| Value | Purpose | Shape the body must have |
|---|---|---|
| `Tutorial` | Learning-oriented | Numbered steps **and** at least one code block |
| `How-to guide` | Task-oriented | Numbered steps **or** a code block |
| `Reference` | Information-oriented | A table, or a list of five or more items |
| `Explanation` | Understanding-oriented | Three or more `##` sections |

**Start from the default DocType of the skeleton** (Section 9):

| Skeleton | Default DocType |
|---|---|
| Procedure | `How-to guide` |
| Note, Post | `Explanation` |
| Report | `Reference` |
| Change, Incident, Task, Meeting (records) | `Reference` |

- Records always keep `DocType: Reference`.
- For knowledge documents, change the default only when the content clearly fits another DocType
  (for example a Note that is a dry list of parameters is a `Reference`). The body must then also
  have the shape of the new DocType.
- If the purpose is ambiguous, ask the user before assigning a DocType.

---

## 8. Status and Priority

### Status (mandatory)

Use only these values, which techdoc knows and scores:

| Group | Values | Effect in techdoc |
|---|---|---|
| Open | `New`, `Open`, `Draft`, `Planned` | Records with an open status appear under **Open items**; `Draft` shows a draft banner |
| Final | `Completed`, `Released`, `Finished`, `Successful` | Counts as final for the quality score |
| Retired | `Deprecated`, `Obsolete`, `Withdrawn`, `Rejected` | Grey "Do not follow" banner; no quality score |

Default values from the skeletons:

- Knowledge documents (`Procedure`, `Note`, `Post`, `Report`): `Draft`.
- Records (`Change`, `Incident`, `Task`, `Meeting`): `New`.

Use the value the content implies instead when it is clear: a reviewed procedure is `Released`,
a closed incident is `Completed`, a change scheduled for next week is `Planned`.

### Priority (skeleton property)

The Procedure, Change, Incident and Task skeletons include `Priority`. Keep it in those documents.
Known values: `Critical`, `Very high`, `High`, `Medium`, `Normal`, `Low`. Default: `Normal`.
Avoid `Unknown`: techdoc shows it but the quality score does not count it as known.

---

## 9. Skeletons: Body Structure by Category and WorkType

The skeleton is chosen by **`Category`** for knowledge documents (`WorkType: Knowledge`) and by
**`WorkType`** for records.
Each skeleton fixes the frontmatter defaults and the `##` sections of the body.

### Section rules

- Use the skeleton's `##` headings **exactly as written** (same words, same capitalisation),
  **in the same order**.
- You may add extra `##` sections **after** the last skeleton section and **before** `## References`.
- `## References` is **always the last section**. List one link per line: sources (vendor notes,
  manuals, SAP Notes, tickets) and related KB4IT documents (`[Title](OTHER-DOC.md)`). Do not invent
  URLs or note numbers; if you have no real source, ask the user for one.
- **Never leave a section empty** and **never leave the skeleton's example text** in the document
  (lines such as "Describe the first step." or `SAP Note 0000000`). techdoc subtracts points for both.
- `###` subsections inside a skeleton section are fine.

### Skeleton overview

| Skeleton | Category | WorkType | DocType | Status | Priority | `##` sections, in order |
|---|---|---|---|---|---|---|
| Procedure | `Procedure` | `Knowledge` | `How-to guide` | `Draft` | `Normal` | Introduction, Prerequisites, Steps, Verification, References |
| Note | `Note` | `Knowledge` | `Explanation` | `Draft` | none | Overview, Details, References |
| Post | `Post` | `Knowledge` | `Explanation` | `Draft` | none | Overview, Details, References |
| Report | `Report` | `Knowledge` | `Reference` | `Draft` | none | Executive Summary, Findings, Recommendations, References |
| Change | `Record` | `Change` | `Reference` | `New` | `Normal` | Overview, Impact, Rollback, References |
| Incident | `Record` | `Incident` | `Reference` | `New` | `Normal` | Summary, Timeline, Root Cause, Resolution, References |
| Task | `Record` | `Task` | `Reference` | `New` | `Normal` | Objective, Acceptance Criteria, Notes, References |
| Meeting | `Minutes` | `Meeting` | `Reference` | `New` | none | Objective, Attendees, Agenda, Notes, Action Items, References |

### What each section holds

**Procedure**
- `## Introduction`: what the procedure achieves and when to use it.
- `## Prerequisites`: bullet list of access, roles, authorisations, systems, tools or files needed.
- `## Steps`: numbered list of steps, with the commands in fenced code blocks.
- `## Verification`: how to check that the procedure worked.

**Note** and **Post**
- `## Overview`: what it is about and why it matters (for a Post: who should read it).
- `## Details`: the body: background, how it works, what to keep in mind. Use `###` subsections.
  An Explanation needs three or more `##` sections in total, so the default
  Overview, Details, References already meets the shape; add sections after Details when the topic needs them.

**Report**
- `## Executive Summary`: main findings and the decision needed, in a few lines.
- `## Findings`: a table, typically `| Area | Finding | Impact |`, Impact being High, Medium or Low.
- `## Recommendations`: bullet list of actions, each with an owner and a date.

**Change** (record)
- `## Overview`: what changes, where, when and why.
- `## Impact`: systems and users affected, downtime.
- `## Rollback`: how to undo the change if it fails.

**Incident** (record)
- `## Summary`: what failed, for whom and for how long.
- `## Timeline`: bullet list `- HH:MM Event`, from the first alert to recovery.
- `## Root Cause`: why it failed.
- `## Resolution`: what fixed it and what prevents it from happening again.

**Task** (record)
- `## Objective`: what the task must achieve and why.
- `## Acceptance Criteria`: task list (`- [ ]` / `- [x]`) of the conditions for done.
- `## Notes`: decisions, findings and links gathered while working.

**Meeting** (minutes)
- `## Objective`: why the meeting took place and what it had to decide.
- `## Attendees`: bullet list, each attendee with their role.
- `## Agenda`: bullet list of agenda items.
- `## Notes`: discussion and decisions taken.
- `## Action Items`: task list (`- [ ]`), each with owner and due date.

### Length guidance

techdoc scores length against a word target. Write enough to be useful; never pad.

| Document | Target words (body) |
|---|---|
| Records (Change, Incident, Task, Meeting) | 60 |
| How-to guide | 150 |
| Reference | 200 |
| Explanation | 500 |
| Tutorial | 800 |

### Skeleton frontmatter

Every skeleton carries the full set of mandatory properties. Shown here in the alphabetical order
the document must use. Fill every value following Section 4.

Knowledge document (Procedure shown; Note, Post and Report drop `Priority` and use their own
`Category` and `DocType`):

```yaml
---
Author: <Author>
Category: Procedure
Date: <YYYY-MM-DD>
DocType: How-to guide
Priority: Normal
Product: <Product>
Scope: <Scope>
Status: Draft
Summary: <One line describing the purpose>
Tag: <tag1>, <tag2>
Topic: <Topic>
WorkType: Knowledge
---
```

Record (Change shown; Incident and Task change only `WorkType`; Meeting uses `Category: Minutes`,
`WorkType: Meeting` and has no `Priority`):

```yaml
---
Author: <Author>
Category: Record
Date: <YYYY-MM-DD HH:MM>
DocType: Reference
Priority: Normal
Product: <Product>
Scope: <Scope>
Status: New
Summary: <One line describing what happened or must happen>
Tag: <tag1>, <tag2>
Topic: <Topic>
WorkType: Change
---
```

---

## 10. Tag Rules

- `Tag` values must be **singular** and **lowercase**: `Tag: backup, migration, housekeeping`
- Tags are generic. When a tag has a specific semantic meaning, **promote it to a dedicated
  semantic property** instead (see Section 11).
- Keep `Tag` for values that don't fit **any** semantic property.
- **A tag must not be a product name** (e.g. `SAP`, `Docker`, `Oracle` → use `Product` or `Database` instead).
- **A tag must not duplicate the value of another property. This is an absolute prohibition.**
  If a value belongs to a semantic property (e.g. `linux`, `windows` → `OS`; `Oracle` → `Database`;
  `Infrastructure` → `Scope`; `backup` → `Topic`; `change`, `incident`, `knowledge` → `WorkType`;
  `procedure`, `report` → `Category`), it **must be removed from `Tag`**, not kept in both.
- **Exclusion is mandatory, not optional.** Only values with no semantic home should remain in `Tag`.
- `Tag` is mandatory, so at least one value with no other home must remain. If deduplication empties
  it, find a genuinely generic keyword in the content; ask the user if none exists.
- **Final check:** before writing the header, read every value in `Tag` and verify it does not
  appear in any other property (case-insensitive). If it does, delete it from `Tag`.

---

## 11. Semantic Properties

When document content implies a well-defined category, create a dedicated property rather
than relying on `Tag`. The values of semantic properties **preserve natural case**
(e.g. `Linux`, `Windows`, `Unix`, `RHEL`, `SQL Plus`, `Oracle`).

**Process:**
1. Identify concepts in the content that belong to a named category
   (OS, product, database, environment, SID, transaction, protocol, etc.).
2. If the natural property name is a single word → use it directly (e.g. `Database`, `Environment`).
3. If the natural property name would contain spaces → **ask the user for their preferred name**.
4. Infer and create new semantic properties freely; there is no fixed vocabulary.

**Properties techdoc groups on the document page** (prefer these names when they fit):

| Group | Properties |
|---|---|
| Classification | `DocType`, `Category`, `WorkType`, `Topic`, `Scope`, `Handover` |
| Systems | `Product`, `SID`, `Environment`, `Database`, `OS`, `Stack`, `Server`, `Kernel` |
| Technical objects | `Transaction`, `Command`, `Program`, `Table`, `Job`, `RFC`, `Component`, `User`, `Role`, `Filesystem` |
| Organisation | `Author`, `Team`, `Project`, `Milestone`, `Company` |
| Lifecycle | `Status`, `Priority`, `Date`, `Periodicity`, `Public` |

**Common examples** (illustrative, not exhaustive):

| Property | Example values |
|---|---|
| `OS` | `Linux`, `Windows`, `Unix` |
| `Product` | `SAP S/4HANA`, `Docker`, `SentinelOne`, `RHEL` |
| `Database` | `HANA`, `PostgreSQL`, `Oracle`, `MySQL` |
| `Environment` | `Production`, `Quality`, `Development`, `Sandbox` |
| `SID` | `PRD`, `QAS`, `DEV` |
| `Transaction` | `SM37`, `ST22`, `STMS` |

`Environment: Production` makes techdoc show a red "This document changes production systems"
banner, with the `SID` values. Set it only when the document really acts on production.

**OS family vs. specific distro/product rule:**
`OS` holds **generic OS families only** (`Linux`, `Windows`, `Unix`). When a specific OS distribution
or flavour is named in the document, use **both** properties:
- `OS` → the generic family (e.g. `Linux`)
- `Product` → the specific distro or flavour (e.g. `RHEL`, `AIX`, `Solaris`)

**Database special case:**
`Database` values (`DB2`, `HANA`, `MaxDB`, `Oracle`, `SQL Server`) are database engine names and must
**not** be duplicated in `Product`. The database engine name lives exclusively in `Database`.
`Product` is still mandatory: use the product that runs on the database (e.g. `SAP S/4HANA`), or ask
the user if the document is only about the database engine.

---

## 12. Known Property Vocabulary (Suggested)

Draw values from these lists whenever possible. New values may be added if none fits.
`Category`, `WorkType`, `DocType`, `Status` and `Priority` are **closed** lists (Sections 5 to 8).

| Property | Known values |
|---|---|
| `Periodicity` | Biannual, Daily, Monthly, On demand, Quarterly, Weekly, Yearly |
| `Scope` | Application Management, Architecture, Change management, Cloud Administration, Controlling, Database Administration, Development, Service Desk, HR Administration, Infrastructure, Knowledge Management, Oracle Administration, SAP Basis, Unix Administration, Windows Administration |
| `Team` | Application Management, Audit, Controlling, CRM, DB Administration, Development, ETL, FI, Helpdesk, HR, Infrastructure, IT Architect, IT Change Management, Linux, Network, Payroll, Permanence, SAP, Web, Windows, Unix |
| `Topic` | Administration, Analysis, Architecture, Archiving, Audit, Authoring, Backup, Cloud, Configuration, Connectivity, Customizing, Development, Documentation, ETL, Finance, Generic, Housekeeping, Infrastructure, Installation, Licensing, Maintenance, Middleware, Migration, Monitoring, Network, Operation, Performance, Printing, Refresh, Rename, Reorganization, Restore, Security, SSO, System Copy, Troubleshooting, Uninstall, Upgrade, User, Virtualization |
| `Product` | Apache, Putty, Git, Docker |
| `Protocol` | HTTPS, SSH, SFTP |
| `Database` | DB2, HANA, MaxDB, Oracle, SQL Server *(engine names, not duplicated in `Product`)* |
| `Command` | apachectl, awk, brconnect, brdb6brt, brspace, brtools, cat, cd, cdexe, chmod, chown, cleanipc, configure, cp, crontab, cupsenable, curl, db2, db2admin, db2start, db2stop, dbanalyzer, dbmcli, dd, df, dipgntab, disp+work, dnf, EMCtrl.sh, export, find, firewall-cmd, getent, git, grep, guiconsole, hostname, hostnamectl, ipcrm, ipcs, jmson, journalctl, jsmon, keytool, kill, ksh, ldap_rfc, loadercli, lpstat, ls, lsnrctl, mailx, make, mkdir, mminfo, mount, mstsc, multipass, nc, netstat, niserver, nohup, nslookup, nsr_render_log, nsrladb, openssl, pageant, pandoc, print, prstat, ps, puppet, putty, pwd, python, R3load, R3trans, recover, rfcexec, rm, rpm, rsecssfx, rsync, scp, sdbregview, sftp, smdsetup.sh, sqlplus, SQLPlus, ssh, ssh-keygen, sshpass, svcadm, svcadmin, svcs, systemctl, tail, tar, telnet, tp, uftp, unzip, uptime, wget, x_server, xargs, xinstinfo, xming, xsltproc, yum, zonestat |
| `Filesystem` | /app, /bin, /boot, /dev, /etc, /home, /lib, /media, /misc, /mnt, /net, /nsr, /opt, /proc, /root, /run, /sbin, /srv, /sys, /tmp, /usr, /var |
| `Server` | *(no pre-seeded values; always extracted from document content)* |

Monitoring documents: `Topic: Monitoring` together with `Periodicity` lists the document in the
techdoc **Monitoring** panel. Add `Periodicity` to recurring checks.

> **Note on `Scope` and `Team`:** these property names contain no spaces but their values often do
> (e.g. `DB Administration`, `Change management`). This is correct. The restriction on spaces applies
> to **property names**, not values.

> **Note on `Command`, `Filesystem` and `Server`:** these are auto-extracted from document content.
> See Section 13.

---

## 13. Auto-Extracted Properties

### `Command`

Captures every CLI command, executable, or script referenced in the document body.

- **Extraction:** scan the body for commands used in code blocks, inline code, and prose references.
- **Matching:** prefer values from the known vocabulary in Section 12; append new values if not listed.
- **Format:** comma-separated, preserve original casing (e.g. `SAPCAR`, `sqlplus`, `EMCtrl.sh`).

Example: `Command: ssh, systemctl, sapcontrol, SAPCAR, EMCtrl.sh`

### `Filesystem`

Captures every absolute directory path referenced in the document body.

- **Extraction:** scan for paths starting with `/`. Split the absolute path and assign the **directory
  portion only** to `Filesystem` and the `<filename.extension>` to `Filename`.
  - `/etc/security/access.conf` gives `Filesystem: /etc/security` and `Filename: access.conf`.
- **Specificity rule:** use the most specific path that is still a real, static directory boundary.
- **Trailing slash rule:** values must **never** end with a slash.
- **Format:** comma-separated.

Example: `Filesystem: /etc/security, /usr/sap, /var/log`

### `Server`

Captures every hostname or IP address referenced in the document body.

- **Extraction:** scan for hostnames (short or FQDN) and IP addresses (IPv4/IPv6).
- **Exclusions:** do not capture `localhost`, `127.0.0.1`, `::1`, or placeholders like `<hostname>`.
- **Format:** comma-separated, preserve original casing.

Example: `Server: app.svr.acme, router-1p, 192.168.1.5, app01.example.com`

---

## 14. Converting and Reviewing Older Documents

When you convert or review an existing KB4IT document, bring it to the current model:

1. **Split `Category`** into form and type of work:

   | Old | New |
   |---|---|
   | `Category: Change` | `Category: Record` + `WorkType: Change` |
   | `Category: Incident` | `Category: Record` + `WorkType: Incident` |
   | `Category: Task` | `Category: Record` + `WorkType: Task` |
   | `Category: Meeting` | `Category: Minutes` + `WorkType: Meeting` |
   | `Category: Procedure`, `Note`, `Post` or `Report` without WorkType | Same Category + `WorkType: Knowledge` |
   | `Category: Report, Incident` (two values) | Ask the user: a Report about an incident, or an Incident record |

2. **Remove `Version`**.
3. **Add every missing mandatory property** (Section 4), including `Summary`.
4. **Check `Status` and `Priority`** against the known values (Section 8). Map near-misses
   (`Done` → `Completed`, `WIP` → `Open`) and ask when the intent is unclear.
5. **Rename sections to the skeleton** of the document's Category (Knowledge) or WorkType (records), in order, with
   `## References` last (Section 9). Keep the content; only move or rename headings. If content
   has no home in the skeleton, put it in an extra section before References.
6. **Remove a `Title:` property** if present; the title is the `# ` heading.
7. Run the full workflow checklist (Section 16) on the result.

KB4IT has a script for step 1: `scripts/conv/split_category.py` in the KB4IT source tree. It moves
the type of work from `Category` to `WorkType` and adds `WorkType: Knowledge` to documents whose
`Category` is only Procedure, Note, Post, Report or Template. Run it with `--dry-run --csv FILE`
first. It picks the record type for `Category: Report, Incident`; check those documents by hand.

When reviewing, report each problem found and the fix applied, then present the corrected document.

---

## 14a. Admonitions

KB4IT uses the **Python-Markdown `admonition` extension**. Use admonition blocks for
notes, warnings, tips, and other callouts. Do **not** use blockquotes (`>`) for this purpose.

### Syntax

```markdown
!!! type "Optional title"
    Indented content (4 spaces). Any standard Markdown is allowed here.

    A second paragraph is fine too.
```

- `type` is a single lowercase word; it becomes the CSS class and the default title (auto-capitalised).
- The title is optional. Omit it to use the default, or pass `""` to suppress it entirely.
- Content must be indented with **4 spaces**.
- Code inside an admonition or a list item: indent it by four more spaces instead of fencing it
  (a fence there only works with `pymdownx.superfences`).

### Recommended types

| Type | When to use |
|---|---|
| `note` | General informational callout |
| `tip` | Helpful suggestion or shortcut |
| `hint` | Subtle guidance the reader might miss |
| `important` | Must-read information for correctness |
| `warning` | Risk of data loss, downtime, or security issue |
| `danger` | Severe risk; do not proceed without reading |
| `caution` | Proceed carefully; reversible but costly mistake possible |
| `error` | Documents a known error or failed state |
| `attention` | Draws the reader's eye to a critical detail |

### Examples

```markdown
!!! warning "Backup before proceeding"
    This procedure modifies live data. Take a full backup first.

!!! tip ""
    No title, content only.
```

### Rules

- Prefer admonitions over inline bold warnings such as `**NOTE:**`.
- One key message per admonition block. Do not stack multiple warnings inside one block.
- Do not nest admonition blocks.
- Place admonitions **after** the paragraph they relate to, not before it.

### Other content blocks

- Code: fenced blocks with a language (` ```bash `), at the start of a line.
- Task lists: `- [ ]` and `- [x]` (used by Task and Meeting skeletons).
- Diagrams: a ` ```mermaid ` fence at the start of a line.
- Images: `![Descriptive alt text](resources/images/file.png)`. A descriptive alt text becomes the
  figure caption; a file-name-like alt text gives no caption.

---

## 15. Writing Style Rules

Apply these rules to every word written in the document body, `Summary`, admonitions, and code comments.

### Prohibited characters and words

**No em dash.** Never use the em dash character (U+2014). Replace it with a comma, a colon, a period, or rewrite the sentence.

**No inflated vocabulary.** Use the simplest word that is still accurate:

| Avoid | Use instead |
|---|---|
| utilize | use |
| leverage | use, apply |
| facilitate | help, allow |
| endeavor | try |
| commence | start |
| optimal | best, good |
| pertaining to | about |
| in order to | to |
| it is worth noting that | *(just state it)* |
| it is important to note | *(just state it)* |
| as mentioned previously | *(cut it)* |

### Sentence construction

One idea per sentence. Short sentences. No padding.

If something is complex, split it into steps or short paragraphs. Do not try to cover everything in one dense block.

### Patterns to remove

- Filler openers: "Certainly!", "Absolutely!", "Of course!", "Great question!"
- Meta-commentary: "Let me explain...", "I will now...", "Here is a summary of..."
- Hollow affirmations: "This is a great approach", "Excellent choice"
- Excessive hedging: "It's worth mentioning that...", "One might argue that..."
- Redundant closers: "I hope this helps!", "Feel free to ask if you have more questions!"

### Tone

Plain. Direct. Professional.

Write as if explaining something to a colleague, not presenting to an audience.

### Code comments

These rules apply inside code blocks too.

- Write comments immediately after the function, method, or line they describe.
- Inline comments go on the same line as the code they annotate.
- Never use decorative separator lines (`# ---`, `# ===`, `# ***`). Use blank lines or docstring headers for grouping.
- Do not restate what the code already says. Comment on *why*, not *what*.

### What these rules do not change

- Technical accuracy. Never simplify to the point of being wrong.
- Completeness. All needed information stays in.

---

## 16. Workflow Checklist

When asked to create, convert or review a document, follow this order:

1. **Determine the form and the type of work.** Is it a record (change, incident, task, meeting) or a
   knowledge document (procedure, note, post, report)? Set `Category` and `WorkType`
   (`Knowledge` for knowledge documents) (Sections 5 and 6). Ask if unclear.
2. **Pick the skeleton** from Category (Knowledge) or WorkType (records) (Section 9). Take its defaults for
   `DocType`, `Status` and `Priority`.
3. **Confirm DocType** (Section 7). Keep the skeleton default unless the content clearly fits another.
4. **Fill every mandatory property** (Section 4): Author, Category, Date, DocType, Product, Scope,
   Status, Summary, Tag, Topic and WorkType. Infer from content; ask before leaving a key empty.
5. **Write the Summary** (Section 4a): one line, the purpose of the document.
6. **Identify semantic properties.** Promote relevant tags; ask for the name if it would contain spaces.
7. **Extract `Command`, `Filesystem` (+ `Filename`) and `Server`** values (Section 13).
8. **Deduplicate values across ALL properties (MANDATORY).** `Tag` always loses. `Summary` is excluded
   from the scan. A document with the same value in two properties is malformed. Do not skip this step.
9. **Remove forbidden properties:** no `Version`, no `Title`.
10. **Draft the YAML frontmatter** in **strict alphabetical order**: open `---`, write `Key: value`
    properties alphabetically, quote values that need it, close `---`.
11. **Leave one blank line** after the closing `---`, then write `# Title`.
12. **Write the body** with the skeleton's `##` sections, exact names, in order; extra sections only
    before `## References`, which is last. Satisfy the DocType shape (Section 7). No empty sections,
    no leftover skeleton text. Use admonitions (Section 14a), never blockquotes. Apply the writing
    rules (Section 15).
13. **Suggest a filename** following Section 1 (always `.md`).
14. **Self-check before presenting:** all mandatory keys present; Category/WorkType pairing valid;
    closed-list values valid; alphabetical order; no duplicates; skeleton sections complete.
15. **Run the quality check** of Section 17 and fix what it finds.
16. **Present the complete document** ready to save.

---

## 17. Quality Score: What techdoc Checks

techdoc scores every document from 0 to 100 and shows the result in the **Quality** tab of the
document page. The site also has a `quality-guide.html` page with every check and an example.
The score has five dimensions:

| Dimension | Points | What earns them |
|---|---|---|
| Findable | 15 | The ten core keys (1 each), known values (2), a `Summary` (3) |
| Structured | 25 | Two or more sections, context first, the DocType shape, the skeleton sections |
| Complete | 25 | Words in the body, up to the target of the type (Section 9) |
| Connected | 15 | Backlinks, a link to another document, a cited source, a References section, an image or diagram |
| Current | 20 | A final `Status`; for knowledge documents also a recent `Date` |

Tiers: **Exemplary** from 75, **Complete** from 60, **Basic** from 40, **Stub** below. A retired
`Status` (Section 8) gives the **Retired** tier and leaves the document out of the peer comparison.

The core keys are `Author`, `Category`, `Date`, `DocType`, `Product`, `Scope`, `Status`, `Tag`,
`Topic` and `WorkType`. Known values are the closed lists of Sections 5 to 8. The thresholds and
lists come from the `quality` block of the theme's `theme.json`.

### Records and knowledge documents

- **Knowledge documents** (`WorkType: Knowledge`) are judged by the skeleton of their `Category`,
  the shape of their `DocType`, the word target of their `DocType` and the age of their `Date`.
  Points for freshness halve every 3 years (How-to guide, Tutorial), 4 years (Reference) or 8 years
  (Explanation).
- **Records** (`WorkType: Change`, `Incident`, `Task` or `Meeting`) are judged by the skeleton of their
  `WorkType`, a 60-word target and a final status. Their age does not count.
- Each document is compared with its peers: knowledge documents with the same `DocType`, records
  with the same `WorkType`.

### Points lost

| Problem | Cost |
|---|---|
| Category does not go with WorkType (Section 6) | 3 points |
| An empty section | 3 points each, at most two |
| Skeleton example text left in the body | 6 points |
| A link to a document that does not exist | 3 points each |
| An image file that is missing | 3 points each |
| Fewer than 20 words (records) or 50 words (knowledge) | Complete capped at 3 |

### Quality advice

Apply this when you write, convert or review a document:

1. **Fill every core key and the Summary.** Ten keys plus `Summary` give the full 15 Findable
   points. An old `Category: Change` is not a known value: migrate it (Section 14).
2. **Open with context.** The first `##` section of every skeleton gives context. Keep it first.
3. **Give the body the shape of its DocType.** A How-to guide without numbered steps or a code
   block loses 8 points. Check the table of Section 7.
4. **Reach the word target.** Write until the content is complete, not until the number is reached.
   Code blocks do not count as words. If the topic is short, a shorter document is fine; never pad.
5. **Link it into the knowledge base.** Link at least one related KB4IT document by file name
   (`[Restore the database](RESTORE-DB.md)`), cite one external source, and end with
   `## References`. Ask the user which related documents exist; do not invent file names.
   A backlink needs a link **to** this document from another one: suggest where to add it.
6. **Add an image or a diagram** when it helps the reader. A ` ```mermaid ` diagram counts.
7. **Set a final status when the work is done.** `Released` for a reviewed knowledge document,
   `Completed` for a closed record. `Draft` and `New` keep points out of reach on purpose.
8. **Review old knowledge documents.** When a review confirms the content, set `Date` to the
   review date; freshness points come back.

### Quality check before presenting

Estimate the score dimension by dimension and report it with the document:

- Findable: every core key, `Summary`, known values, valid Category/WorkType pair.
- Structured: skeleton sections present and in order, DocType shape met, no empty section,
  no skeleton text.
- Complete: body words against the target of Section 9.
- Connected: which of internal link, source, References section, image or diagram are present;
  backlinks are outside the author's control.
- Current: final status or not; for knowledge documents, the age of `Date`.

List what keeps the document from the Exemplary tier and what the user can do about it.
