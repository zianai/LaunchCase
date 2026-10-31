import json
import shutil
import sqlite3
from pathlib import Path

from sqlalchemy import delete, select

from launchcase.domain.common import DomainError, digest
from launchcase.infrastructure.db import Base
from launchcase.infrastructure.models import ProductCase, SourceDocument, Task, VisualAsset, VisualTask


def backup(settings, destination: Path):
    if not settings.database_url.startswith("sqlite:///"):
        raise DomainError(
            "BACKUP_MODE",
            "PostgreSQL requires a stopped-writer pg_dump plus object-store backup; see runbook",
        )
    if destination.exists() or destination.is_symlink():
        raise DomainError("OUTPUT_EXISTS", "Backup destination must be new")
    destination.mkdir(parents=True)
    files = {}
    for name, source in [
        ("launchcase.db", Path(settings.database_url.removeprefix("sqlite:///"))),
        ("checkpoints.db", settings.data_dir / "checkpoints.db"),
        ("creative-mock.db", settings.data_dir / "creative-mock.db"),
    ]:
        if source.exists():
            with sqlite3.connect(source) as src, sqlite3.connect(destination / name) as dst:
                src.backup(dst)
            files[name] = digest((destination / name).read_bytes())
    (destination / "objects").mkdir()
    for path in sorted((settings.data_dir / "objects").glob("*")):
        if path.is_symlink() or not path.is_file() or len(path.name) != 64:
            raise DomainError("UNSAFE_BACKUP", "Unexpected object store entry")
        data = path.read_bytes()
        if digest(data) != path.name:
            raise DomainError("OBJECT_CORRUPT", "Cannot back up altered object")
        shutil.copyfile(path, destination / "objects" / path.name)
        files[f"objects/{path.name}"] = path.name
    manifest = {
        "schema_version": "1.0.0",
        "files": files,
        "requires_stopped_writers": True,
        "scope": "business DB, graph cursor, local mock receipts, immutable objects",
    }
    (destination / "backup-manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest


def restore(source: Path, destination: Path):
    if destination.exists() or destination.is_symlink():
        raise DomainError("OUTPUT_EXISTS", "Restore requires a new directory")
    manifest = json.loads((source / "backup-manifest.json").read_text())
    for name, sha in manifest["files"].items():
        path = source / name
        if (
            Path(name).is_absolute()
            or ".." in Path(name).parts
            or path.is_symlink()
            or not path.resolve().is_relative_to(source.resolve())
            or digest(path.read_bytes()) != sha
        ):
            raise DomainError("BACKUP_CORRUPT", "Backup path/hash invalid; nothing restored")
    destination.mkdir(parents=True)
    for name in manifest["files"]:
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / name, path)
    return {"restored": True, "files": len(manifest["files"])}


def retention(service, actor, confirm_tenant=None):
    service.require(actor, human=True)
    if actor.role != "owner":
        raise DomainError("FORBIDDEN", "Tenant owner required", 403)
    with service.write() as s:
        active = s.scalar(
            select(Task.id).where(Task.tenant_id == actor.tenant_id, Task.status.in_(["running", "queued"]))
        )
        remote = s.scalar(
            select(VisualTask.id).where(
                VisualTask.tenant_id == actor.tenant_id,
                VisualTask.state.in_(["submitting", "reconciling", "submitted", "running"]),
            )
        )
        if active or remote:
            raise DomainError("ACTIVE_WORK", "Resolve active/unknown tasks before purging", 409)
        tables = [t for t in reversed(Base.metadata.sorted_tables) if "tenant_id" in t.c]
        counts = {
            t.name: len(s.execute(select(t.c.id).where(t.c.tenant_id == actor.tenant_id)).all())
            for t in tables
        }
        if confirm_tenant is None:
            return {"dry_run": True, "tenant_id": actor.tenant_id, "rows": counts}
        if confirm_tenant != actor.tenant_id:
            raise DomainError("CONFIRMATION_MISMATCH", "Exact tenant identity required")
        hashes = set(
            s.scalars(select(SourceDocument.sha256).where(SourceDocument.tenant_id == actor.tenant_id))
        ) | set(s.scalars(select(VisualAsset.sha256).where(VisualAsset.tenant_id == actor.tenant_id)))
        journal_path = service.settings.data_dir / f"retention-{digest(actor.tenant_id.encode())}.json"
        pending = (
            json.loads(journal_path.read_text())
            if journal_path.exists()
            else {"cases": [], "visuals": [], "hashes": []}
        )
        pending["cases"] = sorted(
            set(pending["cases"])
            | set(s.scalars(select(ProductCase.id).where(ProductCase.tenant_id == actor.tenant_id)))
        )
        pending["visuals"] = sorted(
            set(pending["visuals"])
            | set(s.scalars(select(VisualTask.id).where(VisualTask.tenant_id == actor.tenant_id)))
        )
        pending["hashes"] = sorted(set(pending["hashes"]) | hashes)
        temporary = journal_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(pending))
        temporary.replace(journal_path)
        for table in tables:
            s.execute(delete(table).where(table.c.tenant_id == actor.tenant_id))
    # Object cleanup follows committed DB deletion; unreferenced leftovers are safe after a crash.
    with service.sessions() as s:
        referenced = set(s.scalars(select(SourceDocument.sha256))) | set(
            s.scalars(select(VisualAsset.sha256))
        )
    for sha in set(pending["hashes"]) - referenced:
        service.objects.path(sha).unlink(missing_ok=True)
    checkpoint = service.settings.data_dir / "checkpoints.db"
    if checkpoint.exists():
        with sqlite3.connect(checkpoint) as conn:
            tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            for table in ["checkpoints", "writes"]:
                if table not in tables:
                    continue
                threads = [row[0] for row in conn.execute(f"SELECT DISTINCT thread_id FROM {table}")]
                for thread in threads:
                    if any(
                        thread.startswith(f"{actor.tenant_id}:{case_id}:") for case_id in pending["cases"]
                    ):
                        conn.execute(f"DELETE FROM {table} WHERE thread_id=?", (thread,))
    mock = service.settings.data_dir / "creative-mock.db"
    if mock.exists():
        project_ids = {f"project-{item}" for item in pending["visuals"]}
        with sqlite3.connect(mock) as conn:
            for item_id, payload in conn.execute("SELECT id,data FROM objects").fetchall():
                if json.loads(payload).get("project_id") in project_ids:
                    conn.execute("DELETE FROM objects WHERE id=?", (item_id,))
    journal_path.unlink()
    return {
        "dry_run": False,
        "tenant_id": actor.tenant_id,
        "rows_removed": counts,
        "local_checkpoint_and_mock_cleanup": True,
        "excluded": "Previously exported files, backups and external CreativeEngine data need separate authorized deletion",
    }
