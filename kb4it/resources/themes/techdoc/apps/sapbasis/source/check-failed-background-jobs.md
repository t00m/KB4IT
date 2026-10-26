---
Author: Your name
Category: Procedure
Date: 2026-10-06
DocType: How-to guide
Environment: Production
Periodicity: Daily
Product: SAP S/4HANA
SID: PRD
Scope: SAP Basis
Status: Finished
Summary: Daily check of the background jobs that were cancelled since the last working day.
Tag: monitoring
Topic: Background jobs
Transaction: SM37
---

# Check failed background jobs

This is a sample procedure for an SAP Basis team. The system id `PRD` and every name in it are examples. `SID`, `Transaction` and `Environment` become pages of their own, so you can list every document about a system or a transaction. Copy it as a starting point, or delete it.

## Introduction

Run this check every working morning. It finds the jobs that were cancelled overnight before users notice missing data.

## Prerequisites

- A user in the production system with display access to all background jobs.

## Steps

1. Log on to `PRD` and start transaction `SM37`.
2. Set **Job name** and **User name** to `*`, select only the status **Canceled**, and set the start date to the last working day.
3. Run the selection.
4. For each cancelled job, open the job log and note the error message.
5. If a job failed with a short dump, follow [Analyse a short dump](analyse-short-dump.md).

## Verification

The check is done when every cancelled job has an owner, or an incident record.

## References

- [Analyse a short dump](analyse-short-dump.md)
- [Transport landscape](transport-landscape.md)
