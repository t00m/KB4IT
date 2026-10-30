---
DocType: How-to guide
Feature: Writing
HelpId: profile
Keyword: person, profile, author, alias, team, role, email, contact, people, tooltip, schema.org
Level: basic
Order: 218
Related: reference-repo-json.md, reference-log-codes.md, reference-theme-techdoc.md
Section: Guides
Summary: Write a profile so the name in Author leads readers to the person's role, team and contact details.
---

# Describe a person with a profile

`Author: Jane Doe` is only a name. A profile says who Jane is and how to reach her. KB4IT shows it on her page (`Author_Jane_Doe.html`), as a tooltip on her name in documents, and in the structured data of the site.

## Write the profile {#write}

1. Create a file in `source/` whose name starts with `PERSON-`, such as `PERSON-JANE-DOE.md`. The prefix makes it a profile; upper or lower case does not matter.
2. Write the name as the title (`# Jane Doe`), exactly as documents write it in `Author`, and the other spellings in `Alias`.
3. Add what readers need: `Role`, `Team`, and at least one way to reach the person, such as `Email`.
4. Under the title, say in a few lines what the person works on and when to ask them.

```markdown
---
Alias: J. Doe, jdoe
Email: jane.doe@example.org
Location: Madrid
Phone: +34 600 000 000
Role: Basis administrator
Team: SAP Basis
---

# Jane Doe

Runs the SAP Basis on-call rota. Ask her about system copies and kernel upgrades.
```

The title holds one name without a comma. A comma splits `Author` values, so a profile titled `# Doe, Jane` could never match and is left out with `PROFILE_INVALID`.

A file without the `PERSON-` prefix is always a document, whatever its properties. `Person` is an ordinary property there, such as the people a change involves.

With the editor on, the person's page has a **Create profile** button that opens this skeleton with the name filled in and proposes the file name `person-jane-doe.md`, or **Edit profile** when the profile exists.

## What readers see {#result}

- **The person's page** shows the profile above the list of their documents: name, role, team, contact rows (email and phone as links) and the text. A page for an alias shows the same profile and links to the main page.
- **Document pages** show the role and team as a tooltip on the name: in the techdoc Details tab, the blog post header and the bookshelf chapter details.
- **Links** to the profile file, such as `[Jane](PERSON-JANE-DOE.md)`, lead to the person's page.
- **Structured data**: every document points to one schema.org `Person` per person, with aliases resolved, and the person's page describes that person as a `ProfilePage`. With `site_url` set, the person gets the address `Author_Jane_Doe.html#person`.

## Keep details private {#private}

A property listed in `people.private` in `repo.json` stays out of the pages, the tooltips and the structured data:

```json
"people": {
  "private": ["Phone"]
}
```

A private property does not count as a contact detail, because readers cannot see it. On a site that search engines index, `kb4it verify` lists every email address or phone number a profile shows (`PROFILE_CONTACT_PUBLIC`).

## Check the profiles {#check}

```bash
kb4it verify config/repo.json
```

`verify` reports profiles that are left out (`PROFILE_INVALID`, `PROFILE_DUPLICATE`, `PROFILE_ALIAS_IS_PERSON`), profiles without contact details (`PROFILE_NO_CONTACT`), profiles nobody names (`PROFILE_UNUSED`), documents titled like a person who has no profile, which may be profiles that lost their prefix (`PROFILE_NO_PREFIX`), and, once you have one profile, the people documents name who have none (`AUTHOR_NO_PROFILE`). See the [log codes](reference-log-codes.md#people).

In techdoc, the first profile also turns on two quality checks: a document loses 2 points for each person it names without a profile and 1 point for each person whose profile has no contact details, at most 4 points. See the [quality score](reference-theme-techdoc.md#quality).
