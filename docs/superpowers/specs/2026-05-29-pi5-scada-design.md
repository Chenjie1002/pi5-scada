# Pi5 SCADA Project Design

## Goal

Build a Raspberry Pi 5 based SCADA system for read-only monitoring and product traceability. The system reads selected Siemens PLC data, stores product records locally, provides a LAN web dashboard, and leaves room for later parameter management and MCU RAW Data analysis.

## Confirmed Scope

- Target hardware: Raspberry Pi 5.
- PLC family: Siemens S7-300, S7-1200, S7-1500, and ET200 series, depending on site equipment.
- PLC access mode: S7 protocol read-only polling for the first version.
- PLC count: 1 PLC in the first version.
- Data points: up to 100 points.
- Polling cycle: 200 ms for `RecordSeq` and key status data.
- Traceability model: one product completion snapshot per product.
- Future expansion: MCU RAW Data collection and later parameter management.
- Frontend: LAN web dashboard accessed from workshop PCs or tablets.
- Database: SQLite first, with SQLAlchemy/Alembic and PostgreSQL migration compatibility.

## Architecture

The first version is a single FastAPI application deployed as one `systemd` service on the Raspberry Pi 5. Internally, the code should stay modular so the collector can be split into a separate service later.

Core modules:

- `PLC Collector`: polls Siemens PLC data through an S7 client.
- `Snapshot Reader`: detects `RecordSeq` changes and reads product snapshots.
- `MCU Collector`: later retrieves MCU RAW Data by `RecordSeq`.
- `Storage`: manages database writes and RAW Data files.
- `API`: provides dashboard, traceability, configuration, and health endpoints.
- `Web Dashboard`: browser UI for operators and engineers.
- `Config Manager`: manages PLC addresses, point mapping, polling cycle, RAW Data paths, and retention policy.

## PLC Data Contract

PLC is the authoritative source for product completion events.

Recommended PLC-side data:

- `RecordSeq`: PLC-managed product sequence number, incremented once per completed product.
- `ProductId`: product identifier if available.
- `Result`: OK/NG result.
- `CycleTimeMs`: product cycle time.
- `SCADA_Snapshot_DB`: locked product completion snapshot.

Recommended PLC behavior:

1. When a product is complete, copy stable process data into `SCADA_Snapshot_DB`.
2. Increment `RecordSeq`.
3. Continue production without waiting for SCADA confirmation.

The first version should not write a read-complete acknowledgement back to PLC. Future parameter management or handshake features can add controlled write access with timeout and fail-safe logic.

For higher reliability, PLC should eventually expose a snapshot ring buffer:

- `RecordSeq`: total completed count.
- `SnapshotRing[N]`: recent product snapshots.
- `WriteIndex`: derived from `RecordSeq % N`.

This allows SCADA to detect and recover from short delays or skipped polling windows.

## MCU RAW Data Expansion

MCU is a secondary data source, not the source of product records.

PLC and MCU share the same PLC-managed `RecordSeq`. MCU performs acquisition tasks and makes RAW Data available to SCADA.

Recommended MCU fields or API response:

- `RecordSeq`
- `CaptureSeq`
- `CaptureStatus`: `idle`, `capturing`, `ready`, `error`, or `expired`
- `RawDataLength`
- `Checksum`
- `CompletedAt`

SCADA flow:

1. Detect new PLC `RecordSeq`.
2. Read PLC snapshot and create product record.
3. Create pending RAW Data task.
4. Query MCU by `RecordSeq`.
5. If ready, download RAW Data, save file, calculate checksum, and update database.
6. If delayed, retry in background.
7. If timeout expires, mark RAW Data as `timeout` without affecting the product record.

RAW Data should be stored as files, not inside the main product table.

## Data Model

### `product_records`

- `id`
- `line_id`
- `station_id`
- `record_seq`
- `product_id`
- `result`
- `cycle_time_ms`
- `started_at`
- `completed_at`
- `plc_snapshot_json`
- `created_at`

Unique constraint:

- `(line_id, station_id, record_seq)`

### `product_raw_data`

- `id`
- `product_record_id`
- `record_seq`
- `source_type`
- `capture_seq`
- `status`: `pending`, `ready`, `missing`, `timeout`, or `error`
- `file_path`
- `size_bytes`
- `checksum`
- `format_version`
- `captured_at`
- `stored_at`
- `error_message`

### `production_metrics`

- `id`
- `bucket_start`
- `bucket_seconds`
- `line_id`
- `station_id`
- `total_count`
- `ok_count`
- `ng_count`
- `avg_cycle_time_ms`
- `planned_count`

### `system_config`

- `key`
- `value_json`
- `updated_at`

### `collector_events`

- `id`
- `severity`
- `source`: `plc`, `mcu`, `storage`, or `system`
- `event_code`
- `message`
- `detail_json`
- `created_at`

## RAW Data Storage

Recommended file path:

```text
data/raw/<line_id>/<station_id>/<yyyy>/<mm>/<dd>/<record_seq>_<capture_seq>.bin
```

Write strategy:

1. Write to a temporary `.tmp` file.
2. Calculate checksum.
3. Rename to `.bin` after the write is complete.
4. Update database status to `ready`.

## Web Pages

### Real-Time Overview

Shows:

- PLC connection status.
- MCU connection status.
- Collector status.
- Current `RecordSeq`.
- Today output, OK count, NG count.
- Yield rate.
- Current and average cycle time.
- Actual vs planned output curve.
- Recent product records.
- Recent collector events.

### Product Traceability List

Filters:

- Time range.
- `RecordSeq`.
- `ProductId`.
- OK/NG result.
- RAW Data status.
- Line and station.

### Product Detail

Shows:

- Line, station, sequence number, product ID, completion time, result, and cycle time.
- PLC snapshot parameters and original snapshot JSON.
- RAW Data status, file size, checksum, capture time, and format version.
- Future action: analyze RAW Data on demand.

### System Configuration

Configures:

- PLC IP, rack, and slot.
- Polling cycle, default 200 ms.
- `RecordSeq` address.
- Snapshot DB address, length, and field mapping.
- MCU connection settings.
- RAW Data save path.
- RAW Data timeout.
- Data retention policy.
- Planned output or takt-time parameters.

### Event Log

Shows PLC reconnects, sequence gaps, RAW Data timeout, storage errors, configuration reloads, and system events.

## API Surface

Dashboard:

- `GET /api/dashboard/summary`
- `GET /api/dashboard/output-curve?range=today`
- `GET /api/records/recent?limit=20`
- `GET /api/events/recent?limit=20`

Traceability:

- `GET /api/records`
- `GET /api/records/{id}`
- `GET /api/records/{id}/snapshot`
- `GET /api/records/{id}/raw-data`
- `POST /api/records/{id}/raw-data/analyze`

Configuration:

- `GET /api/config`
- `PUT /api/config`
- `POST /api/config/test-plc`
- `POST /api/config/test-mcu`
- `POST /api/config/reload`

Health:

- `GET /api/health`

## Runtime Behavior

PLC polling:

- Poll `RecordSeq` and key status data every 200 ms.
- On `RecordSeq` increment, read the product snapshot and write a product record.
- If `RecordSeq` jumps, record a `record_seq_gap` event.
- If a PLC ring buffer exists, attempt to recover intermediate records.

Reconnect behavior:

- PLC disconnects should not stop the web dashboard.
- Collector enters reconnect loop.
- History remains queryable.
- All connection state changes are written to `collector_events`.

Restart behavior:

- On service startup, load the last processed `RecordSeq` from the database.
- Continue monitoring from the current PLC sequence.
- Detect and log reset, rollback, or jump conditions.

## Testing Strategy

Unit tests:

- PLC data parsing.
- `RecordSeq` normal increment.
- `RecordSeq` gap detection.
- Idempotent product record insert.
- RAW Data file write and checksum.
- MCU timeout handling.
- Configuration load and save.

Integration tests:

- Mock PLC sequence changes.
- Mock MCU ready, delayed, missing, and error states.
- API query behavior.
- Dashboard summary calculations.

Hardware tests:

1. Connect to PLC test DB only.
2. Read `RecordSeq`.
3. Read a small snapshot.
4. Verify no PLC cycle time impact.
5. Enable full snapshot reading.
6. Validate product records against real production events.

## Git And Data Policy

Commit source code, docs, configuration templates, migrations, and tests.

Do not commit:

- Production SQLite databases.
- RAW Data files.
- Logs.
- `.env` files.
- PLC credentials.
- GitHub tokens.
- Real production data.
