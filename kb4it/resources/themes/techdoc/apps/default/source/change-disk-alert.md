---
Author: Your name
Category: Record
Date: 2026-09-20
DocType: Reference
Priority: Normal
Scope: Infrastructure
Status: Completed
Summary: Add a disk usage alert at 80 percent on every file server.
Tag: alerting, disk
Topic: Monitoring
WorkType: Change
---

# Add a disk usage alert to the file servers

This is a sample change record. `WorkType: Change` lists it in the latest changes on the dashboard, and `Date` places it in the calendar. Copy it as a starting point, or delete it.

## Overview

After the [disk full incident](disk-full-incident.md), the monitoring tool gets a new rule: warn the operations team when a file server disk is 80 percent full, and page the on-call person at 95 percent.

## Impact

No downtime. The rule only reads disk usage.

## Rollback

Disable the rule in the monitoring tool. Nothing else changes.

## References

- [Disk full on the file server](disk-full-incident.md)
