"""Transaction boundary for changes whose audit record is mandatory.

Nested repositories may request commits; these become flushes until the complete
service or endpoint succeeds. An outer BookingRoute keeps ownership of its commit.
"""
from contextlib import contextmanager
from functools import wraps
import inspect


@contextmanager
def atomic_session(db):
    commit = db.commit
    db.commit = db.flush
    try:
        yield
        commit()
    except BaseException:
        db.rollback()
        raise
    finally:
        db.commit = commit


def audited_change(function):
    signature = inspect.signature(function)
    def session(args, kwargs):
        values = signature.bind(*args, **kwargs).arguments
        return values["self"].db if "self" in values else values["db"]
    if inspect.iscoroutinefunction(function):
        @wraps(function)
        async def asynchronous(*args, **kwargs):
            with atomic_session(session(args, kwargs)):
                return await function(*args, **kwargs)
        return asynchronous
    @wraps(function)
    def synchronous(*args, **kwargs):
        with atomic_session(session(args, kwargs)):
            return function(*args, **kwargs)
    return synchronous


def audited_media(directory, id_parameter=None):
    """Restore the previous entity's files if its mandatory audit/DB change fails."""
    def decorate(function):
        signature = inspect.signature(function)
        @wraps(function)
        async def wrapped(*args, **kwargs):
            from pathlib import Path
            import shutil
            from tempfile import TemporaryDirectory
            from app.services import file_service
            from contextlib import nullcontext
            from app.core.maintenance_lock import maintenance_gate
            values = signature.bind(*args, **kwargs).arguments
            db = values["self"].db if "self" in values else values["db"]
            base_folder = Path(getattr(file_service, directory.upper() + "_DIR")).resolve()
            folder = base_folder
            if id_parameter:
                identifier = int(values[id_parameter])
                if identifier < 0:
                    raise ValueError("Ungültige Medien-ID")
                folder /= str(identifier)
            folder.resolve().relative_to(base_folder)
            engine = db.get_bind()
            media_gate = maintenance_gate(engine, exclusive=True, key=716813) if engine.dialect.name == "postgresql" else nullcontext()
            # Session-level lock outlives rollback, so another writer cannot replace
            # files between the database rollback and restoration of the old image.
            with media_gate, TemporaryDirectory(prefix="kickerkasse-media-") as temporary:
                previous = Path(temporary) / "previous"
                existed = folder.exists()
                if existed:
                    shutil.copytree(folder, previous)
                try:
                    with atomic_session(db):
                        return await function(*args, **kwargs)
                except BaseException:
                    if folder.exists():
                        shutil.rmtree(folder)
                    if existed:
                        shutil.copytree(previous, folder)
                    raise
        return wrapped
    return decorate
