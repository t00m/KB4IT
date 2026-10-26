---
Author: Your name
Category: Procedure
Date: 2026-10-03
DocType: How-to guide
Scope: Infrastructure
Status: Finished
Summary: Daily check that every backup job of last night ended well.
Tag: nightly
Topic: Backup
---

# Check last night's backups

This is a sample document. It uses `Category` to group it with other procedures, `Date` to place it in the calendar, `DocType` for the dashboard card, and `Scope`, `Status`, `Tag` and `Topic` to filter the document table. Copy it as a starting point, or delete it.

## Introduction

Run this check every working morning. It finds failed backups while last night's data can still be saved again.

## Prerequisites

- Read access to the backup tool's job report.

## Steps

1. Open the backup report for last night.
2. Check that every job ended with status OK.
3. For each job that did not end with OK, open a change or incident record and note the job name.

## Verification

The check is done when every job is OK, or has a record. Read [RAID levels in short](raid-levels.md) to see why RAID does not replace these backups.

## References

- [Disk full on the file server](disk-full-incident.md)
- [Storage capacity report, third quarter](storage-capacity-report.md)
