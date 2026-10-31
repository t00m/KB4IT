---
Author: Your name
Category: Record
Date: 2026-10-15 18:00
DocType: Reference
Downtime: Yes
DowntimeEnd: 2026-10-15 18:45
DowntimeStart: 2026-10-15 18:15
Environment: Quality
Priority: Normal
Product: SAP S/4HANA
SID: QAS
ScheduledEnd: 2026-10-15 19:00
ScheduledStart: 2026-10-15 18:00
Scope: SAP Basis
Server: sapqas01
Status: Planned
Summary: Update the SAP kernel of the quality system to the current patch level before production.
Tag: kernel, maintenance
Team: SAP
Topic: Software maintenance
WorkType: Change
---

# Kernel update in the quality system

This is a sample change record. `Status: Planned` keeps it under **Open items** and `Date` puts it in the calendar. The server `sapqas01` is an example name. Copy it as a starting point, or delete it.

## Overview

Update the kernel of `QAS` to the patch level planned for production. The quality system goes first so that the test teams can check it for a week.

- Type: Normal.
- Affected: `QAS` and the test users of finance and logistics.

## Impact

`QAS` is down for about 30 minutes. Test users are told one day before.

## Implementation Plan

Download the kernel archives for the target patch level and check that no background job runs at 18:15.

1. Stop `QAS` and copy the kernel folder to `exe.old`.
2. Unpack the new archives into the kernel folder and start `QAS`.

```bash
SAPCAR -xvf SAPEXE.SAR -R /usr/sap/QAS/SYS/exe/run
```

## Verification

Check the kernel patch level in `SM51`, run a test logon and look for new short dumps in `ST22`.

## Rollback

Keep a copy of the old kernel folder. If the system does not start, stop it, put the old kernel back and start it again.

## Result

Not run yet. After the change, record the outcome, the actual times and any deviation from the plan.

## References

- [Transport landscape](transport-landscape.md)
