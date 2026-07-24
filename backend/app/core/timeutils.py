from datetime import datetime, timezone


def ensure_utc(dt: datetime) -> datetime:
    """Normalize a datetime to timezone-aware UTC.

    Postgres preserves tzinfo on `DateTime(timezone=True)` columns; SQLite
    (used in the test suite) silently drops it on round-trip. Comparing a
    naive value loaded from SQLite against `datetime.now(timezone.utc)`
    raises TypeError, so every comparison against a DB-loaded datetime goes
    through this first.
    """
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)
