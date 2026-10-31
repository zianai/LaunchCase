from pathlib import Path

from alembic import command
from alembic.config import Config


def migrate(settings, revision="head"):
    folder = Path(__file__).resolve().parents[3] / "migrations"
    if not folder.is_dir():
        folder = Path(__file__).resolve().parents[1] / "migration_resources"
    config = Config()
    config.set_main_option("script_location", str(folder))
    config.attributes["settings"] = settings
    command.upgrade(config, revision)
