"""Durable media staging, keeping the uploads mount itself in place.

The journal remains until both media replacement and the DB commit are complete.
On restart the transaction's audit marker decides whether old media must return.
An interrupted recovery is repeatable; old files are copied, never consumed.
"""
import json
import os
import shutil
from pathlib import Path
from uuid import UUID
from app.services.file_service import UPLOADS_DIR

JOURNAL = ".restore-state.json"


def recovery_pending(root=None):
    return ((root or UPLOADS_DIR) / JOURNAL).exists()


def children(root):
    return [item for item in root.iterdir() if not item.name.startswith(".restore-")]


def safe_remove(path, root):
    # Never follow a link or delete outside the explicitly verified uploads root.
    path.resolve().relative_to(root.resolve())
    if path.is_symlink():
        raise ValueError("Verknüpfungen im Medienverzeichnis sind nicht zulässig")
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


class MediaReplacement:
    def __init__(self, root, operation_id, *, entity_type="database_backup", action="RESTORED"):
        self.entity_type, self.action = entity_type, action
        self.root = Path(root).resolve()
        self.operation_id = str(UUID(operation_id))
        self.stage = self.root / (".restore-" + self.operation_id)

    def prepare(self, media):
        self.root.mkdir(parents=True, exist_ok=True)
        if recovery_pending(self.root):
            raise RuntimeError("Unabgeschlossene Medienwiederherstellung")
        self.stage.mkdir()
        (self.stage / "old").mkdir()
        (self.stage / "new").mkdir()
        for item in self.root.rglob("*"):
            if item.is_symlink():
                raise ValueError("Verknüpfungen im Medienverzeichnis sind nicht zulässig")
        for item in children(self.root):
            target = self.stage / "old" / item.name
            if item.is_dir():
                shutil.copytree(item, target)
            else:
                shutil.copy2(item, target)
        for name, content in media.items():
            target = self.stage / "new" / name
            target.resolve().relative_to((self.stage / "new").resolve())
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        for path in self.stage.rglob("*"):
            if path.is_file():
                with path.open("rb") as staged_file:
                    os.fsync(staged_file.fileno())
        journal_tmp = self.root / ".restore-journal.tmp"
        with journal_tmp.open("w", encoding="utf-8") as file:
            json.dump({"operation_id": self.operation_id, "entity_type": self.entity_type, "action": self.action}, file)
            file.flush()
            os.fsync(file.fileno())
        journal_tmp.replace(self.root / JOURNAL)

    def apply(self, source="new"):
        for item in children(self.root):
            safe_remove(item, self.root)
        for item in (self.stage / source).iterdir():
            if item.is_dir():
                shutil.copytree(item, self.root / item.name)
            else:
                shutil.copy2(item, self.root / item.name)

    def cleanup(self):
        (self.root / JOURNAL).unlink(missing_ok=True)
        if self.stage.exists():
            safe_remove(self.stage, self.root)


def recover_media(db, root=None):
    root = Path(root or UPLOADS_DIR).resolve()
    if not recovery_pending(root):
        return
    from app.models import AuditLog
    data = json.loads((root / JOURNAL).read_text(encoding="utf-8"))
    replacement = MediaReplacement(root, data["operation_id"])
    committed = db.query(AuditLog.id).filter_by(entity_type=data.get("entity_type", "database_backup"),
        action=data.get("action", "RESTORED"), entity_name=replacement.operation_id).first()
    if not committed:
        replacement.apply("old")
    replacement.cleanup()
