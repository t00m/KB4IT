---
Author: Your name
Category: Record
Date: 2026-10-10
DocType: Reference
DueDate: 2026-10-31
Priority: High
Scope: Security
Status: Open
Summary: Renew the TLS certificates of the intranet web servers before they expire.
Tag: certificates, tls
Team: Operations
Topic: Security
WorkType: Task
---

# Renew the web server certificates

This is a sample task record. `Status: Open` lists it under **Open items** on the dashboard until you set a final status such as `Completed`. Copy it as a starting point, or delete it.

## Objective

The TLS certificates of the intranet web servers expire at the end of the month. Renew them before users see browser warnings.

## Acceptance Criteria

- [ ] New certificates are installed on every intranet web server.
- [ ] A browser shows the new expiry date on each site.
- [ ] The expiry dates are recorded in the certificate inventory.

## Subtasks

- [ ] Request the new certificates from the certificate authority (security officer).
- [ ] Install them on each web server and restart the web service (system administrator).

## Notes

- 2026-09-22 The task was agreed in the [weekly operations meeting](weekly-operations-meeting.md).

## References

- [Weekly operations meeting](weekly-operations-meeting.md)
