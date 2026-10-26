---
Author: Your name
Category: Record
Date: 2026-10-15 18:00
DocType: Reference
Environment: Quality
Priority: Normal
Product: SAP S/4HANA
SID: QAS
Scope: SAP Basis
Server: sapqas01
Status: Planned
Summary: Update the SAP kernel of the quality system to the current patch level before production.
Tag: kernel, maintenance
Topic: Software maintenance
WorkType: Change
---

# Kernel update in the quality system

This is a sample change record. `Status: Planned` keeps it under **Open items** and `Date` puts it in the calendar. The server `sapqas01` is an example name. Copy it as a starting point, or delete it.

## Overview

Update the kernel of `QAS` to the patch level planned for production. The quality system goes first so that the test teams can check it for a week.

## Impact

`QAS` is down for about 30 minutes. Test users are told one day before.

## Rollback

Keep a copy of the old kernel folder. If the system does not start, stop it, put the old kernel back and start it again.

## References

- [Transport landscape](transport-landscape.md)
