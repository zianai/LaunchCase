from alembic import context

from launchcase.infrastructure import models  # noqa: F401
from launchcase.infrastructure.config import Settings
from launchcase.infrastructure.db import Base, database

engine, _ = database(context.config.attributes.get("settings") or Settings.from_env())
with engine.connect() as connection:
    context.configure(connection=connection, target_metadata=Base.metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()
