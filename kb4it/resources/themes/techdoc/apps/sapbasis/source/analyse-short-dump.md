---
Author: Your name
Category: Procedure
Date: 2026-10-07
DocType: How-to guide
Product: SAP S/4HANA
SID: PRD
Scope: SAP Basis
Status: Finished
Summary: Find out why an ABAP program ended with a short dump, and who should fix it.
Tag: troubleshooting
Topic: Runtime errors
Transaction: ST22
---

# Analyse a short dump

This is a sample procedure. Copy it as a starting point, or delete it.

## Introduction

A short dump is the record the system writes when an ABAP program stops with a runtime error. Use this procedure to decide whether the error is technical (Basis) or in the application (developers or functional team).

## Prerequisites

- Display access to transaction `ST22` in the system where the dump happened.

## Steps

1. Start transaction `ST22` and select the dumps of today or yesterday.
2. Open the dump and read **Short text** and **What happened?**.
3. Note the runtime error name, the program and the user.
4. Memory errors such as `TSV_TNEW_PAGE_ALLOC_FAILED` usually need a Basis check of the memory parameters. Errors in customer programs (names starting with `Z` or `Y`) go to the developers.
5. If the dump stopped a business process, open an incident record.

## Verification

The dump is assigned to a team, and the user who hit it knows who will answer.

## References

- [Short dumps in the nightly invoice job](invoice-job-dumps.md)
