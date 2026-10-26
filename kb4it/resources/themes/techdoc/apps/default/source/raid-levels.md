---
Author: Your name
Category: Note
Date: 2026-09-05
DocType: Explanation
Scope: Infrastructure
Status: Finished
Summary: What RAID 1, 5, 6 and 10 protect against, and what they cost in disk space.
Tag: raid, storage
Topic: Storage
---

# RAID levels in short

This is a sample note. `DocType: Explanation` marks it as background reading rather than a procedure. Copy it as a starting point, or delete it.

## Overview

RAID spreads data over several disks so that one failed disk does not stop a server. It is not a backup: a deleted file is deleted on every disk. Backups are still needed, see [Check last night's backups](backup-check.md).

## Details

| Level | Survives | Usable space with 4 disks of 1 TB |
|---|---|---|
| RAID 1 | One disk of each mirrored pair | 2 TB |
| RAID 5 | One disk | 3 TB |
| RAID 6 | Two disks | 2 TB |
| RAID 10 | One disk in each mirror | 2 TB |

RAID 5 rebuilds slowly on large disks, and a second failure during the rebuild loses the array. For large disks, RAID 6 or RAID 10 is the safer choice.

## References

- [Disk full on the file server](disk-full-incident.md)
