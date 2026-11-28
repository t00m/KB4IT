---
Author: Your name
Category: Record
Date: 2026-09-18 08:40
DetectedDate: 2026-09-18 08:40
DocType: Reference
Priority: High
ResolvedDate: 2026-09-18 10:20
Scope: Infrastructure
Status: Completed
Summary: The file server disk filled up with application logs and users could not save files for two hours.
Tag: logs
Team: Operations
Topic: Monitoring
WorkType: Incident
---

# Disk full on the file server

This is a sample document. It is a record: `Category: Record` with `WorkType: Incident`. `WorkType` puts it in the latest incidents on the dashboard. `Priority` fills the document table, `Date` to place the incident in the calendar, and `Topic` and `Tag` to find it later. Copy it as a starting point, or delete it.

## Summary

The file server ran out of disk space. Users could not save files for about two hours.

- Affected: the shared folders of the file server and every office user.
- Detected by: user calls to the service desk. No alert was set up.

## Timeline

- 08:40 Users report that they cannot save files.
- 09:05 The team finds the disk 100 percent full.
- 10:20 Old application logs are moved away and users can save again.

## Investigation

Users saw "Disk full" when saving. `df -h` showed the data disk at 100 percent, and `du` pointed to the application log folder, which held 40 GB of logs.

## Root Cause

The application log grew without a limit and filled the disk.

## Resolution

Old application logs were moved to the archive share, which freed the disk at 10:20. The log is now rotated every day. Users confirmed that they can save files again.

## Follow-up Actions

- [x] Add an alert when a disk is 80 percent full, see [the change](change-disk-alert.md).
- [ ] Write a procedure for cleaning up application logs.

## References

- [Check last night's backups](backup-check.md)
- [Weekly operations meeting](weekly-operations-meeting.md)
