import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from arq import create_pool
from arq.connections import RedisSettings
from arq.worker import Worker

from launchcase.application.services import CaseService
from launchcase.infrastructure.config import Settings
from launchcase.infrastructure.migrate import migrate
from launchcase.infrastructure.tasks import TaskManager
from launchcase.workflow.graph import enqueue_run
from launchcase.workflow.worker import wakeup

pytestmark = pytest.mark.skipif(
    not os.getenv("LAUNCHCASE_TEST_POSTGRES"),
    reason="Isolated PostgreSQL/Redis not configured; run ops/verify_infrastructure.py",
)


def test_postgresql_migration_concurrent_idempotency_lease_and_arq(tmp_path, brief, monkeypatch):
    database_url = os.environ["LAUNCHCASE_TEST_POSTGRES"]
    settings = Settings(tmp_path, database_url)
    migrate(settings)
    svc = CaseService(settings)
    _, actor = svc.provision("infra-" + uuid4().hex, "infra fixture", "owner", True)
    with ThreadPoolExecutor(max_workers=2) as pool:
        cases = list(pool.map(lambda _: svc.create_case(actor, brief, "same-key"), range(2)))
    assert cases[0]["id"] == cases[1]["id"]
    assert len(svc.list_cases(actor)) == 1
    task = enqueue_run(svc, actor, cases[0]["id"], "research", "research")
    manager = TaskManager(svc)
    with ThreadPoolExecutor(max_workers=2) as pool:
        claims = list(pool.map(lambda owner: manager.claim(actor, task["id"], owner), ["a", "b"]))
    assert sum(c is not None for c in claims) == 1
    from sqlalchemy import update

    from launchcase.infrastructure.models import Task

    with svc.write() as session:
        session.execute(update(Task).where(Task.id == task["id"]).values(lease_until=0))
    monkeypatch.setenv("LAUNCHCASE_DATABASE_URL", database_url)
    monkeypatch.setenv("LAUNCHCASE_DATA_DIR", str(tmp_path))

    async def check():
        redis_settings = RedisSettings(host="127.0.0.1", port=int(os.environ["LAUNCHCASE_TEST_REDIS_PORT"]))
        pool = await create_pool(redis_settings)
        job = await pool.enqueue_job("wakeup", _job_id="fixture-wakeup")
        await pool.enqueue_job("wakeup", _job_id="fixture-wakeup")
        worker = Worker(functions=[wakeup], redis_pool=pool, burst=True, handle_signals=False, max_jobs=1)
        await worker.async_run()
        result = await job.result(timeout=10)
        assert len(result) == 1 and result[0]["status"] == "succeeded"
        await worker.close()

    asyncio.run(check())
    assert manager.get(actor, task["id"])["attempts"] == 2
