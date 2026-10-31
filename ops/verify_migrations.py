"""Disposable SQLite upgrade/check/downgrade, never the operator's database."""

import tempfile
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from launchcase.infrastructure.config import Settings
from launchcase.infrastructure.db import database

root = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix="launchcase-migration-") as temporary:
    folder = Path(temporary)
    config = Config()
    config.set_main_option("script_location", str(root / "migrations"))
    settings = Settings(folder, f"sqlite:///{folder}/test.db")
    config.attributes["settings"] = settings
    command.upgrade(config, "head")
    command.check(config)
    engine, _ = database(settings)
    assert "visual_assets" in inspect(engine).get_table_names()
    command.downgrade(config, "base")
    assert inspect(engine).get_table_names() == ["alembic_version"]
    command.upgrade(config, "head")
    command.check(config)
    print("Five revisions upgraded, no metadata drift, downgraded to base, re-upgraded.")
