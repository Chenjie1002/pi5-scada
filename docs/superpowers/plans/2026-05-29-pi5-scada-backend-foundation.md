# Pi5 SCADA Backend Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first runnable backend foundation for the Raspberry Pi 5 SCADA system, including FastAPI app structure, configuration loading, SQLAlchemy models, SQLite persistence, health check, and baseline traceability APIs.

**Architecture:** This phase creates a modular monolithic Python backend under `src/pi5_scada`. The app exposes FastAPI endpoints, stores data through SQLAlchemy models, and keeps PLC/MCU communication behind interfaces that can be implemented in later phases. Tests drive each behavior before production code is written.

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy 2.x, Pydantic Settings, SQLite, pytest, httpx TestClient.

---

## File Structure

- Create `pyproject.toml`: project metadata, dependencies, pytest configuration, package discovery.
- Create `src/pi5_scada/__init__.py`: package marker.
- Create `src/pi5_scada/app.py`: FastAPI app factory and router wiring.
- Create `src/pi5_scada/config.py`: application settings and defaults.
- Create `src/pi5_scada/db.py`: SQLAlchemy engine/session helpers.
- Create `src/pi5_scada/models.py`: ORM models for product records, RAW Data metadata, metrics, config, and events.
- Create `src/pi5_scada/schemas.py`: Pydantic response/request schemas.
- Create `src/pi5_scada/repositories.py`: database access functions for records and events.
- Create `src/pi5_scada/api/__init__.py`: API package marker.
- Create `src/pi5_scada/api/health.py`: health endpoint.
- Create `src/pi5_scada/api/records.py`: traceability list/detail endpoints.
- Create `src/pi5_scada/api/dashboard.py`: summary endpoint baseline.
- Create `tests/conftest.py`: test database and app fixtures.
- Create `tests/test_config.py`: configuration default tests.
- Create `tests/test_models.py`: schema/model behavior tests.
- Create `tests/test_health_api.py`: health endpoint tests.
- Create `tests/test_records_api.py`: traceability endpoint tests.
- Create `.env.example`: safe configuration template.

## Task 1: Project Packaging And Test Baseline

**Files:**
- Create: `pyproject.toml`
- Create: `src/pi5_scada/__init__.py`
- Create: `tests/test_config.py`
- Create: `src/pi5_scada/config.py`

- [ ] **Step 1: Write the failing configuration test**

Create `tests/test_config.py`:

```python
from pi5_scada.config import Settings


def test_settings_have_safe_defaults() -> None:
    settings = Settings()

    assert settings.app_name == "Pi5 SCADA"
    assert settings.poll_interval_ms == 200
    assert settings.database_url == "sqlite:///./data/pi5_scada.sqlite3"
    assert settings.raw_data_dir == "./data/raw"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
pytest tests/test_config.py -v
```

Expected: FAIL because `pi5_scada.config` does not exist.

- [ ] **Step 3: Add packaging and minimal settings implementation**

Create `pyproject.toml`:

```toml
[project]
name = "pi5-scada"
version = "0.1.0"
description = "Raspberry Pi 5 SCADA and traceability backend"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "sqlalchemy>=2.0.0",
    "pydantic-settings>=2.4.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "httpx>=0.27.0",
]

[build-system]
requires = ["setuptools>=70.0.0"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

Create `src/pi5_scada/__init__.py`:

```python
__all__ = ["__version__"]

__version__ = "0.1.0"
```

Create `src/pi5_scada/config.py`:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Pi5 SCADA"
    poll_interval_ms: int = 200
    database_url: str = "sqlite:///./data/pi5_scada.sqlite3"
    raw_data_dir: str = "./data/raw"

    model_config = SettingsConfigDict(env_prefix="PI5_SCADA_", env_file=".env")
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```powershell
pytest tests/test_config.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add pyproject.toml src/pi5_scada/__init__.py src/pi5_scada/config.py tests/test_config.py
git commit -m "chore: add python project baseline"
```

## Task 2: Database Models And Session Helpers

**Files:**
- Create: `src/pi5_scada/db.py`
- Create: `src/pi5_scada/models.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Write failing model tests**

Create `tests/test_models.py`:

```python
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from pi5_scada.models import Base, ProductRecord, ProductRawData


def test_product_record_unique_trace_key() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    with Session() as session:
        completed_at = datetime(2026, 5, 29, 8, 0, tzinfo=timezone.utc)
        record = ProductRecord(
            line_id="line-1",
            station_id="station-1",
            record_seq=1001,
            product_id="P1001",
            result="OK",
            cycle_time_ms=1200,
            completed_at=completed_at,
            plc_snapshot_json={"pressure": 1.23},
        )
        session.add(record)
        session.commit()

        loaded = session.query(ProductRecord).one()

    assert loaded.line_id == "line-1"
    assert loaded.station_id == "station-1"
    assert loaded.record_seq == 1001
    assert loaded.plc_snapshot_json == {"pressure": 1.23}


def test_raw_data_can_reference_product_record() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    with Session() as session:
        record = ProductRecord(
            line_id="line-1",
            station_id="station-1",
            record_seq=1002,
            product_id="P1002",
            result="NG",
            cycle_time_ms=1300,
            completed_at=datetime(2026, 5, 29, 8, 1, tzinfo=timezone.utc),
            plc_snapshot_json={"temperature": 42.0},
        )
        session.add(record)
        session.flush()
        raw = ProductRawData(
            product_record_id=record.id,
            record_seq=1002,
            source_type="mcu",
            capture_seq=501,
            status="pending",
        )
        session.add(raw)
        session.commit()

        loaded = session.query(ProductRawData).one()

    assert loaded.product_record_id == record.id
    assert loaded.record_seq == 1002
    assert loaded.status == "pending"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
pytest tests/test_models.py -v
```

Expected: FAIL because `pi5_scada.models` does not exist.

- [ ] **Step 3: Implement SQLAlchemy base and models**

Create `src/pi5_scada/db.py`:

```python
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from pi5_scada.config import Settings


def make_engine(database_url: str):
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, connect_args=connect_args)


def make_session_factory(database_url: str) -> sessionmaker[Session]:
    return sessionmaker(bind=make_engine(database_url), autoflush=False, autocommit=False)


settings = Settings()
SessionLocal = make_session_factory(settings.database_url)


def get_session() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session
```

Create `src/pi5_scada/models.py`:

```python
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import JSON


class Base(DeclarativeBase):
    pass


class ProductRecord(Base):
    __tablename__ = "product_records"
    __table_args__ = (
        UniqueConstraint("line_id", "station_id", "record_seq", name="uq_product_trace_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    line_id: Mapped[str] = mapped_column(String(64), index=True)
    station_id: Mapped[str] = mapped_column(String(64), index=True)
    record_seq: Mapped[int] = mapped_column(Integer, index=True)
    product_id: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    result: Mapped[str] = mapped_column(String(16), index=True)
    cycle_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    plc_snapshot_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProductRawData(Base):
    __tablename__ = "product_raw_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_record_id: Mapped[int] = mapped_column(ForeignKey("product_records.id"), index=True)
    record_seq: Mapped[int] = mapped_column(Integer, index=True)
    source_type: Mapped[str] = mapped_column(String(32))
    capture_seq: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    file_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)
    format_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    captured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    stored_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(1024), nullable=True)


class ProductionMetric(Base):
    __tablename__ = "production_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bucket_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    bucket_seconds: Mapped[int] = mapped_column(Integer)
    line_id: Mapped[str] = mapped_column(String(64), index=True)
    station_id: Mapped[str] = mapped_column(String(64), index=True)
    total_count: Mapped[int] = mapped_column(Integer, default=0)
    ok_count: Mapped[int] = mapped_column(Integer, default=0)
    ng_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_cycle_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    planned_count: Mapped[int | None] = mapped_column(Integer, nullable=True)


class SystemConfig(Base):
    __tablename__ = "system_config"

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    value_json: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CollectorEvent(Base):
    __tablename__ = "collector_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    severity: Mapped[str] = mapped_column(String(16), index=True)
    source: Mapped[str] = mapped_column(String(32), index=True)
    event_code: Mapped[str] = mapped_column(String(64), index=True)
    message: Mapped[str] = mapped_column(String(512))
    detail_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```powershell
pytest tests/test_models.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/pi5_scada/db.py src/pi5_scada/models.py tests/test_models.py
git commit -m "feat: add persistence models"
```

## Task 3: Health API

**Files:**
- Create: `tests/conftest.py`
- Create: `tests/test_health_api.py`
- Create: `src/pi5_scada/app.py`
- Create: `src/pi5_scada/api/__init__.py`
- Create: `src/pi5_scada/api/health.py`
- Modify: `src/pi5_scada/db.py`

- [ ] **Step 1: Write failing health endpoint test**

Create `tests/conftest.py`:

```python
import pytest
from fastapi.testclient import TestClient

from pi5_scada.app import create_app
from pi5_scada.models import Base
from pi5_scada.db import make_engine


@pytest.fixture()
def client() -> TestClient:
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    app = create_app(database_url="sqlite:///:memory:")
    return TestClient(app)
```

Create `tests/test_health_api.py`:

```python
def test_health_endpoint_reports_service_and_database_status(client) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "app": "Pi5 SCADA",
        "database": "ok",
        "plc": "not_configured",
        "mcu": "not_configured",
    }
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
pytest tests/test_health_api.py -v
```

Expected: FAIL because `pi5_scada.app` does not exist.

- [ ] **Step 3: Implement FastAPI app and health router**

Modify `src/pi5_scada/db.py` to add a health helper:

```python
from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from pi5_scada.config import Settings


def make_engine(database_url: str):
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, connect_args=connect_args)


def make_session_factory(database_url: str) -> sessionmaker[Session]:
    return sessionmaker(bind=make_engine(database_url), autoflush=False, autocommit=False)


def check_database(database_url: str) -> bool:
    engine = make_engine(database_url)
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return True


settings = Settings()
SessionLocal = make_session_factory(settings.database_url)


def get_session() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session
```

Create `src/pi5_scada/app.py`:

```python
from fastapi import FastAPI

from pi5_scada.api.health import router as health_router
from pi5_scada.config import Settings


def create_app(database_url: str | None = None) -> FastAPI:
    settings = Settings()
    if database_url is not None:
        settings.database_url = database_url

    app = FastAPI(title=settings.app_name)
    app.state.settings = settings
    app.include_router(health_router, prefix="/api")
    return app
```

Create `src/pi5_scada/api/__init__.py`:

```python
__all__ = []
```

Create `src/pi5_scada/api/health.py`:

```python
from fastapi import APIRouter, Request

from pi5_scada.db import check_database

router = APIRouter()


@router.get("/health")
def get_health(request: Request) -> dict[str, str]:
    settings = request.app.state.settings
    check_database(settings.database_url)
    return {
        "status": "ok",
        "app": settings.app_name,
        "database": "ok",
        "plc": "not_configured",
        "mcu": "not_configured",
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```powershell
pytest tests/test_health_api.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/pi5_scada/app.py src/pi5_scada/api/__init__.py src/pi5_scada/api/health.py src/pi5_scada/db.py tests/conftest.py tests/test_health_api.py
git commit -m "feat: add health api"
```

## Task 4: Product Record Repository And API

**Files:**
- Create: `src/pi5_scada/schemas.py`
- Create: `src/pi5_scada/repositories.py`
- Create: `src/pi5_scada/api/records.py`
- Create: `tests/test_records_api.py`
- Modify: `src/pi5_scada/app.py`

- [ ] **Step 1: Write failing records API test**

Create `tests/test_records_api.py`:

```python
from datetime import datetime, timezone

from sqlalchemy.orm import sessionmaker

from pi5_scada.models import Base, ProductRecord
from pi5_scada.db import make_engine
from pi5_scada.app import create_app
from fastapi.testclient import TestClient


def test_records_list_returns_recent_product_records() -> None:
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    with Session() as session:
        session.add(
            ProductRecord(
                line_id="line-1",
                station_id="station-1",
                record_seq=1001,
                product_id="P1001",
                result="OK",
                cycle_time_ms=1200,
                completed_at=datetime(2026, 5, 29, 8, 0, tzinfo=timezone.utc),
                plc_snapshot_json={"pressure": 1.23},
            )
        )
        session.commit()

    app = create_app(database_url="sqlite:///:memory:")
    app.state.engine = engine
    client = TestClient(app)

    response = client.get("/api/records")

    assert response.status_code == 200
    assert response.json()["items"][0]["record_seq"] == 1001
    assert response.json()["items"][0]["result"] == "OK"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
pytest tests/test_records_api.py -v
```

Expected: FAIL because `/api/records` is not registered.

- [ ] **Step 3: Implement schemas, repository, and records router**

Create `src/pi5_scada/schemas.py`:

```python
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProductRecordOut(BaseModel):
    id: int
    line_id: str
    station_id: str
    record_seq: int
    product_id: str | None
    result: str
    cycle_time_ms: int | None
    completed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductRecordListOut(BaseModel):
    items: list[ProductRecordOut]
    total: int
```

Create `src/pi5_scada/repositories.py`:

```python
from sqlalchemy import select
from sqlalchemy.orm import Session

from pi5_scada.models import ProductRecord


def list_product_records(session: Session, limit: int = 50) -> list[ProductRecord]:
    statement = select(ProductRecord).order_by(ProductRecord.completed_at.desc()).limit(limit)
    return list(session.scalars(statement))
```

Create `src/pi5_scada/api/records.py`:

```python
from fastapi import APIRouter, Request
from sqlalchemy.orm import sessionmaker

from pi5_scada.repositories import list_product_records
from pi5_scada.schemas import ProductRecordListOut, ProductRecordOut

router = APIRouter()


@router.get("/records", response_model=ProductRecordListOut)
def get_records(request: Request, limit: int = 50) -> ProductRecordListOut:
    Session = sessionmaker(bind=request.app.state.engine)
    with Session() as session:
        records = list_product_records(session, limit=limit)
        return ProductRecordListOut(
            items=[ProductRecordOut.model_validate(record) for record in records],
            total=len(records),
        )
```

Modify `src/pi5_scada/app.py`:

```python
from fastapi import FastAPI

from pi5_scada.api.health import router as health_router
from pi5_scada.api.records import router as records_router
from pi5_scada.config import Settings
from pi5_scada.db import make_engine


def create_app(database_url: str | None = None) -> FastAPI:
    settings = Settings()
    if database_url is not None:
        settings.database_url = database_url

    app = FastAPI(title=settings.app_name)
    app.state.settings = settings
    app.state.engine = make_engine(settings.database_url)
    app.include_router(health_router, prefix="/api")
    app.include_router(records_router, prefix="/api")
    return app
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```powershell
pytest tests/test_records_api.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/pi5_scada/schemas.py src/pi5_scada/repositories.py src/pi5_scada/api/records.py src/pi5_scada/app.py tests/test_records_api.py
git commit -m "feat: add product records api"
```

## Task 5: Dashboard Summary Baseline And Environment Template

**Files:**
- Create: `src/pi5_scada/api/dashboard.py`
- Create: `tests/test_dashboard_api.py`
- Create: `.env.example`
- Modify: `src/pi5_scada/app.py`

- [ ] **Step 1: Write failing dashboard summary test**

Create `tests/test_dashboard_api.py`:

```python
def test_dashboard_summary_returns_zero_state(client) -> None:
    response = client.get("/api/dashboard/summary")

    assert response.status_code == 200
    assert response.json() == {
        "today_total": 0,
        "today_ok": 0,
        "today_ng": 0,
        "yield_rate": 0.0,
        "current_record_seq": None,
        "plc_status": "not_configured",
        "mcu_status": "not_configured",
    }
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
pytest tests/test_dashboard_api.py -v
```

Expected: FAIL because `/api/dashboard/summary` is not registered.

- [ ] **Step 3: Implement baseline dashboard router and env template**

Create `src/pi5_scada/api/dashboard.py`:

```python
from fastapi import APIRouter

router = APIRouter()


@router.get("/dashboard/summary")
def get_dashboard_summary() -> dict[str, int | float | str | None]:
    return {
        "today_total": 0,
        "today_ok": 0,
        "today_ng": 0,
        "yield_rate": 0.0,
        "current_record_seq": None,
        "plc_status": "not_configured",
        "mcu_status": "not_configured",
    }
```

Modify `src/pi5_scada/app.py`:

```python
from fastapi import FastAPI

from pi5_scada.api.dashboard import router as dashboard_router
from pi5_scada.api.health import router as health_router
from pi5_scada.api.records import router as records_router
from pi5_scada.config import Settings
from pi5_scada.db import make_engine


def create_app(database_url: str | None = None) -> FastAPI:
    settings = Settings()
    if database_url is not None:
        settings.database_url = database_url

    app = FastAPI(title=settings.app_name)
    app.state.settings = settings
    app.state.engine = make_engine(settings.database_url)
    app.include_router(health_router, prefix="/api")
    app.include_router(records_router, prefix="/api")
    app.include_router(dashboard_router, prefix="/api")
    return app
```

Create `.env.example`:

```text
PI5_SCADA_APP_NAME=Pi5 SCADA
PI5_SCADA_POLL_INTERVAL_MS=200
PI5_SCADA_DATABASE_URL=sqlite:///./data/pi5_scada.sqlite3
PI5_SCADA_RAW_DATA_DIR=./data/raw
```

- [ ] **Step 4: Run all tests**

Run:

```powershell
pytest -v
```

Expected: PASS.

- [ ] **Step 5: Commit and push**

```powershell
git add src/pi5_scada/api/dashboard.py src/pi5_scada/app.py tests/test_dashboard_api.py .env.example
git commit -m "feat: add dashboard summary baseline"
git push
```

## Self-Review

- Spec coverage: This plan covers the first backend foundation slice only: packaging, config, ORM schema, health API, traceability list baseline, and dashboard summary baseline. PLC polling, MCU RAW Data retrieval, Web UI, Alembic migrations, systemd deployment, and hardware tests are intentionally left for later focused plans.
- Placeholder scan: No placeholder tasks are present. Each implementation task includes explicit files, code, commands, expected test outcomes, and commit commands.
- Type consistency: Names used across tasks are consistent: `Settings`, `create_app`, `ProductRecord`, `ProductRawData`, `make_engine`, `check_database`, `ProductRecordOut`, and `ProductRecordListOut`.
