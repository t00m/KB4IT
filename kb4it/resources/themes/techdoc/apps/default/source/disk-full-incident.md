---
Author: Your name
Category: Record
Date: 2026-09-18
DocType: Reference
Priority: High
Scope: Infrastructure
Status: Completed
Summary: The file server disk filled up with application logs and users could not save files for two hours.
Tag: logs
Topic: Monitoring
WorkType: Incident
---

# Disk full on the file server

This is a sample document. It is a record: `Category: Record` with `WorkType: Incident`. `WorkType` puts it in the latest incidents on the dashboard. `Priority` fills the document table, `Date` to place the incident in the calendar, and `Topic` and `Tag` to find it later. Copy it as a starting point, or delete it.

## Summary

The file server ran out of disk space. Users could not save files for about two hours.

## Timeline

- 08:40 Users report that they cannot save files.
- 09:05 The team finds the disk 100 percent full.
- 10:20 Old application logs are moved away and users can save again.

## Root Cause

The application log grew without a limit and filled the disk.

## Resolution

The log is now rotated every day, and an alert warns when a disk is 80 percent full. The alert was added with [this change](change-disk-alert.md).

## References

- [Check last night's backups](backup-check.md)
- [Weekly operations meeting](weekly-operations-meeting.md)
