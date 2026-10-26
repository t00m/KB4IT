---
Author: Your name
Book: Linux Basics
Chapter: 1
Command: ls, cd, pwd, mkdir
Date: 2026-10-05
Part: I
PartTitle: The shell
Status: Done
Tag: shell
---

# Files and folders

This is a sample chapter of a second book. A different `Book` value puts it on its own shelf. `Command` lists the commands the chapter teaches; each one gets a page with every chapter that uses it. Copy it as a starting point, or delete it.

## Where am I

`pwd` prints the folder you are in. `ls` lists what it holds; `ls -l` adds sizes, owners and dates.

## Moving around

`cd folder` enters a folder, `cd ..` goes up one level and `cd` alone goes back to your home folder.

## Making folders

`mkdir notes` creates a folder. `mkdir -p notes/linux/chapter1` creates every missing folder on the way.

```bash
mkdir -p ~/study/linux
cd ~/study/linux
pwd
```

Next: [Reading files](linux-reading-files.md).
