---
Author: Your name
Category: Incident
Date: 2026-09-18
DocType: Explanation
Priority: High
Scope: Infrastructure
Status: Completed
Tag: logs
Topic: Monitoring
---

# Disk full on the file server

This is a sample document. It uses `Category` and `Priority` for the document table, `Date` to place the incident in the calendar, and `Topic` and `Tag` to find it later. Copy it as a starting point, or delete it.

## What happened

The file server ran out of disk space. Users could not save files for about two hours.

## Cause

The application log grew without a limit and filled the disk.

## Fix

The log is now rotated every day, and an alert warns when a disk is 80 percent full.
