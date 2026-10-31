---
Author:
Category: Record
Date: YYYY-MM-DD
DocType: Reference
Downtime:
DowntimeEnd:
DowntimeStart:
Environment:
Priority: Normal
Product:
SID:
ScheduledEnd:
ScheduledStart:
Scope:
Status: New
Summary:
Tag:
Team:
Topic:
WorkType: Change
---

# Title of the change

## Overview

Describe the change: what, where, when and why.

- Type: Standard, Normal or Emergency.
- Requested by: name the requester and the ticket.
- Affected: list the systems and services.
- Related: link the incidents, problems and changes behind it.

### Approvals

| Approval | Name | Date | Decision |
|---|---|---|---|
| Technical | Approver | YYYY-MM-DD | Approved |
| Service owner or CAB | Approver | YYYY-MM-DD | Approved |

## Impact

Describe the business and technical impact: who loses what, and for how long.
Set Downtime to Yes, with DowntimeStart and DowntimeEnd, when a service stops.

### Risks

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| What can go wrong | High, Medium or Low | High, Medium or Low | How you prevent or limit it |

List the dependencies: interfaces, jobs or teams that must be ready.

## Implementation Plan

List the prerequisites and the pre-checks, such as a recent backup and free disk space.

1. Describe the first step, with its owner and its expected result.
2. Describe the next step, with its owner and its expected result.

```bash
replace-with-the-command --and-its-options
```

## Verification

Describe the checks after the change: services up, logs clean, users confirm.

## Rollback

Say when to roll back: the decision criteria and the latest time to decide.

1. Describe the first rollback step.
2. Describe the next rollback step, up to the check that proves the old state is back.

State how long a full rollback takes.

## Result

Record the outcome: Successful, Failed or Rolled back, with the actual start and end times.

- Describe the deviations from the plan and the unexpected issues.
- [ ] Describe the follow-up action, with its owner and due date (YYYY-MM-DD).
- Name the lessons learned and the documents to update.

## References

- [SAP Note 0000000](https://me.sap.com/notes/0000000)
- Link the documents this one builds on.
