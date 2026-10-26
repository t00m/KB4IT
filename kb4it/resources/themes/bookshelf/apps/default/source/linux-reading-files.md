---
Author: Your name
Book: Linux Basics
Chapter: 2
Command: cat, less, head, tail
Date: 2026-10-06
Part: I
PartTitle: The shell
Status: Reading
Tag: shell
---

# Reading files

This is a sample chapter. It shares `Book` and `Part` with [Files and folders](linux-files-and-folders.md), so both appear in the same part. Copy it as a starting point, or delete it.

## Short files

`cat file` prints a whole file. Use it for files that fit on the screen.

## Long files

`less file` opens a file page by page. Press `Space` for the next page, `/` to search and `q` to quit.

## The start and the end

`head -n 20 file` prints the first 20 lines and `tail -n 20 file` the last 20. `tail -f file` keeps printing new lines as they are written, which is useful for logs.

```bash
tail -f /var/log/messages
```
