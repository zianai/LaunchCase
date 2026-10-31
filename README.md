# LaunchCase

Independent, offline-first Amazon US product development workbench. Synthetic research,
mock concept assets and internal drafts are never real market/product validation.

Python 3.11+, uv, Node 24+ required. Install with `uv sync --extra dev`, migrate with
`uv run alembic upgrade head`, inspect `uv run launchcase doctor`, and start the API
with `uv run uvicorn launchcase.api:app --host 127.0.0.1 --port 8810`.

Run `uv run pytest -q` and `uv run ruff check .`. See docs/PHASE_REPORTS for executed evidence.
Paid calls and publication are unavailable by default. TradeCase/CreativeEngine are read-only
reference projects; LaunchCase has its own database and content store.
