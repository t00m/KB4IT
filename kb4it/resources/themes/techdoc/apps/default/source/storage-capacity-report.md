---
Author: Your name
Category: Report
Date: 2026-10-01
DocType: Reference
Scope: Infrastructure
Status: Draft
Summary: Disk usage of the file servers in the third quarter, and what to buy next.
Tag: capacity, disk
Topic: Storage
---

# Storage capacity report, third quarter

This is a sample report. `Status: Draft` shows a draft banner on the page until you change it. Copy it as a starting point, or delete it.

## Executive Summary

The file servers use 72 percent of their disk space and grow about 3 percent a month. At this rate they reach the 80 percent alert in three months. A disk extension should be ordered this quarter.

## Findings

| Area | Finding | Impact |
|---|---|---|
| File server 1 | 78 percent used, mostly shared folders | High |
| File server 2 | 65 percent used | Medium |
| Logs | Rotated daily since the [disk full incident](disk-full-incident.md) | Low |

## Recommendations

- Order two extra disks for file server 1 this quarter.
- Ask each department to archive shared folders older than five years.

## References

- [Add a disk usage alert to the file servers](change-disk-alert.md)
- [RAID levels in short](raid-levels.md)
