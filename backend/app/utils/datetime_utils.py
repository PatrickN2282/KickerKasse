from datetime import datetime


def localize_dt(dt: datetime | None) -> datetime | None:
    """Convert a naive datetime to timezone-aware using the local system timezone.

    After tzdata is installed and TZ=Europe/Berlin is set in the container, this
    attaches the correct Berlin UTC offset so that JSON clients can interpret
    timestamps unambiguously.
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.astimezone()
    return dt
