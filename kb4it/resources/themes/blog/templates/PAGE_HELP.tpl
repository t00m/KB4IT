## KB4IT Documents

Any KB4IT document is made of two sections:

1. Header (YAML frontmatter)
2. Body (Markdown content)

### Header

The header is YAML frontmatter delimited by `---` lines. Properties go
inside as `Key: Value` pairs.

Examples of properties: Author, Category, Scope, Status, Priority, Team,
Periodicity, etc.

**Example of a KB4IT document header:**

```markdown
---
Author:        John Doe
Category:      Help
Scope:         Technical documentation
Status:        Released
Priority:      Normal
Team:          IT Plumbers
Periodicity:   Timely
---

# How to write Markdown documents for KB4IT
```

### Body

After the header, write your document body in Markdown.

It is recommended to split your document into logical sections to make
it more readable:

```markdown
## Section 1

### Section 1.1

### Section 1.2

## Section 2

### Section 2.1
```

> **TIP:** Use the source of other KB4IT pages as templates or write your
> own page from scratch.

## References

See the [CommonMark spec](https://commonmark.org/) for a quick start or
the [Markdown Guide](https://www.markdownguide.org/) for a deeper
understanding of the Markdown format.
