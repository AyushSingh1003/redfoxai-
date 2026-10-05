from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker
from config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


SQLITE_COMPAT_COLUMNS = {
    "assessments": {
        "error": "TEXT",
        "started_at": "DATETIME",
        "completed_at": "DATETIME",
        "plan_json": "TEXT",
    },
    "assessment_events": {
        "event_type": "VARCHAR",
        "message": "VARCHAR",
        "metadata_json": "TEXT",
        "timestamp": "DATETIME",
    },
}


def ensure_sqlite_compat_schema(bind=engine):
    """
    Keep older local prototype databases compatible with the current models.

    SQLAlchemy's create_all creates missing tables, but it does not add columns
    to tables that already exist. This app ships as a lightweight SQLite demo,
    so a narrow additive guard is enough to prevent stale local DB startup
    failures without introducing a migration dependency.
    """
    if bind.dialect.name != "sqlite":
        return

    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())

    with bind.begin() as conn:
        for table_name, columns in SQLITE_COMPAT_COLUMNS.items():
            if table_name not in existing_tables:
                continue

            existing_columns = {
                column["name"] for column in inspector.get_columns(table_name)
            }
            for column_name, column_type in columns.items():
                if column_name in existing_columns:
                    continue
                conn.execute(
                    text(
                        f"ALTER TABLE {table_name} "
                        f"ADD COLUMN {column_name} {column_type}"
                    )
                )

        inspector = inspect(bind)
        if "assessment_events" in existing_tables:
            event_columns = {
                column["name"] for column in inspector.get_columns("assessment_events")
            }
            if {"kind", "title", "occurred_at"}.issubset(event_columns):
                conn.execute(text("DROP TABLE IF EXISTS assessment_events_new"))
                conn.execute(
                    text(
                        """
                        CREATE TABLE assessment_events_new (
                            id VARCHAR NOT NULL,
                            assessment_id VARCHAR NOT NULL,
                            "order" INTEGER NOT NULL,
                            event_type VARCHAR NOT NULL,
                            message VARCHAR NOT NULL,
                            detail TEXT,
                            metadata_json TEXT,
                            timestamp DATETIME NOT NULL,
                            PRIMARY KEY (id),
                            FOREIGN KEY(assessment_id) REFERENCES assessments (id)
                        )
                        """
                    )
                )
                conn.execute(
                    text(
                        """
                        INSERT INTO assessment_events_new (
                            id,
                            assessment_id,
                            "order",
                            event_type,
                            message,
                            detail,
                            metadata_json,
                            timestamp
                        )
                        SELECT
                            id,
                            assessment_id,
                            "order",
                            COALESCE(event_type, kind, 'info'),
                            COALESCE(message, title, 'Assessment Event'),
                            detail,
                            metadata_json,
                            COALESCE(timestamp, occurred_at, CURRENT_TIMESTAMP)
                        FROM assessment_events
                        """
                    )
                )
                conn.execute(text("DROP TABLE assessment_events"))
                conn.execute(
                    text("ALTER TABLE assessment_events_new RENAME TO assessment_events")
                )
                conn.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS ix_assessment_events_assessment_id "
                        "ON assessment_events (assessment_id)"
                    )
                )
            else:
                if {"kind", "event_type"}.issubset(event_columns):
                    conn.execute(
                        text(
                            "UPDATE assessment_events "
                            "SET event_type = COALESCE(event_type, kind)"
                        )
                    )
                if {"title", "message"}.issubset(event_columns):
                    conn.execute(
                        text(
                            "UPDATE assessment_events "
                            "SET message = COALESCE(message, title)"
                        )
                    )
                if {"occurred_at", "timestamp"}.issubset(event_columns):
                    conn.execute(
                        text(
                            "UPDATE assessment_events "
                            "SET timestamp = COALESCE(timestamp, occurred_at)"
                        )
                    )


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
