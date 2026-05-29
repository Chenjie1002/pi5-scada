# Pi5 SCADA

Raspberry Pi 5 based SCADA and traceability system for read-only Siemens PLC monitoring, local production records, and LAN web dashboards.

## Current Scope

- Read-only S7 polling from one Siemens PLC.
- Up to 100 monitored points.
- 200 ms polling for `RecordSeq` and key status points.
- Product traceability based on PLC-managed sequence numbers.
- PLC snapshot records stored locally.
- Optional MCU RAW Data associated by the same `RecordSeq`.
- SQLite first, with schema designed for future PostgreSQL migration.
- LAN web dashboard for overview, product traceability, product detail, system configuration, and event logs.

## Repository Policy

Production databases, RAW Data, logs, secrets, PLC credentials, and environment files are intentionally excluded from Git.
