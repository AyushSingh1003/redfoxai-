from sqlalchemy import create_engine, inspect, text

from database import ensure_sqlite_compat_schema


def test_sqlite_compat_schema_adds_missing_assessment_columns(tmp_path):
    db_path = tmp_path / "old_redfox.db"
    engine = create_engine(f"sqlite:///{db_path}")

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE assessments (
                    id VARCHAR PRIMARY KEY,
                    target VARCHAR NOT NULL,
                    profile VARCHAR NOT NULL,
                    status VARCHAR NOT NULL,
                    authorized BOOLEAN NOT NULL,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL
                )
                """
            )
        )

    ensure_sqlite_compat_schema(engine)

    columns = {column["name"] for column in inspect(engine).get_columns("assessments")}
    assert {"error", "started_at", "completed_at", "plan_json"}.issubset(columns)


def test_sqlite_compat_schema_backfills_old_event_columns(tmp_path):
    db_path = tmp_path / "old_redfox.db"
    engine = create_engine(f"sqlite:///{db_path}")

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE assessment_events (
                    id VARCHAR PRIMARY KEY,
                    assessment_id VARCHAR NOT NULL,
                    "order" INTEGER NOT NULL,
                    kind VARCHAR NOT NULL,
                    title VARCHAR NOT NULL,
                    detail TEXT,
                    occurred_at DATETIME NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO assessment_events
                    (id, assessment_id, "order", kind, title, detail, occurred_at)
                VALUES
                    ('evt-1', 'asm-1', 1, 'info', 'Started', 'Old row', '2026-01-01 00:00:00')
                """
            )
        )

    ensure_sqlite_compat_schema(engine)

    columns = {
        column["name"] for column in inspect(engine).get_columns("assessment_events")
    }
    assert {"event_type", "message", "metadata_json", "timestamp"}.issubset(columns)
    assert {"kind", "title", "occurred_at"}.isdisjoint(columns)

    with engine.connect() as conn:
        row = conn.execute(
            text(
                "SELECT event_type, message, timestamp "
                "FROM assessment_events WHERE id = 'evt-1'"
            )
        ).one()

    assert row.event_type == "info"
    assert row.message == "Started"
    assert str(row.timestamp) == "2026-01-01 00:00:00"

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO assessment_events
                    (id, assessment_id, "order", event_type, message, timestamp)
                VALUES
                    ('evt-2', 'asm-1', 2, 'success', 'Created', '2026-01-01 00:00:01')
                """
            )
        )
