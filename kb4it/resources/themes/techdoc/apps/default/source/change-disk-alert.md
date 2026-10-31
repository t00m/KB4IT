---
Author: Your name
Category: Record
Date: 2026-09-20 14:00
DocType: Reference
Downtime: No
Priority: Normal
ScheduledEnd: 2026-09-20 15:00
ScheduledStart: 2026-09-20 14:00
Scope: Infrastructure
Status: Completed
Summary: Add a disk usage alert at 80 percent on every file server.
Tag: alerting, disk
Team: Operations
Topic: Monitoring
WorkType: Change
---

# Add a disk usage alert to the file servers

This is a sample change record. `WorkType: Change` lists it in the latest changes on the dashboard, and `Date` places it in the calendar. Copy it as a starting point, or delete it.

## Overview

After the [disk full incident](disk-full-incident.md), the monitoring tool gets a new rule: warn the operations team when a file server disk is 80 percent full, and page the on-call person at 95 percent.

- Type: Standard.
- Requested by: the operations lead, after the incident review in the [weekly operations meeting](weekly-operations-meeting.md).
- Affected: the monitoring tool and every file server.

## Impact

No downtime. The rule only reads disk usage. The on-call person may get a page the first night, if a disk is already above 95 percent.

## Implementation Plan

Check first that every file server reports disk usage to the monitoring tool.

1. Create the rule: warning at 80 percent, critical at 95 percent, on every file server disk.
2. Send warnings to the operations team mailbox and critical alerts to the on-call phone.

## Verification

Fill a test disk on one server above 80 percent and check that the team mailbox gets the warning. Remove the test file afterwards.

## Rollback

Disable the rule in the monitoring tool. Nothing else changes.

## Result

Successful, from 14:00 to 14:40. The test warning arrived within two minutes. No deviation from the plan.

## References

- [Disk full on the file server](disk-full-incident.md)
