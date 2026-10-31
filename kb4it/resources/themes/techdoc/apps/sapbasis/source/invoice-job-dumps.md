---
Author: Your name
Category: Record
Date: 2026-10-08 07:30
DetectedDate: 2026-10-08 07:30
Dump: TSV_TNEW_PAGE_ALLOC_FAILED
DocType: Reference
Job: Z_INVOICE_RUN
Priority: High
Product: SAP S/4HANA
ResolvedDate: 2026-10-08 09:15
SID: PRD
Scope: SAP Basis
Status: Completed
Summary: The nightly invoice job ran out of memory after a large month-end volume; invoices went out four hours late.
Tag: memory
Team: SAP
Topic: Background jobs
WorkType: Incident
---

# Short dumps in the nightly invoice job

This is a sample incident record. `Dump` and `Job` are properties too, so the site lists every incident with the same runtime error or job. Copy it as a starting point, or delete it.

## Summary

The nightly invoice job `Z_INVOICE_RUN` stopped with a memory short dump. Invoices of the month end went out four hours late.

## Timeline

- 02:10 The job starts.
- 02:45 The job stops with `TSV_TNEW_PAGE_ALLOC_FAILED`.
- 07:30 The morning [job check](check-failed-background-jobs.md) finds it.
- 09:15 The job is restarted in three parts and ends well.

## Investigation

`ST22` showed `TSV_TNEW_PAGE_ALLOC_FAILED` in `Z_INVOICE_RUN`, with one internal table holding most of the memory. `SM37` showed that the job volume was three times larger than on other nights.

## Root Cause

Month-end volume was three times the usual. The program reads all open items into one internal table, which needed more memory than one work process may use.

## Resolution

The job now runs per company code, which keeps each run within the memory limit. The finance team confirmed that the invoices went out.

## Follow-up Actions

- [ ] The developers change the program to read the items in packages.

## References

- [Analyse a short dump](analyse-short-dump.md)
