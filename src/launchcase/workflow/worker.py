"""DB recovery worker; ARQ only provides optional wakeups."""

import time

from sqlalchemy import or_, select

from launchcase.application.services import Actor, CaseService
from launchcase.infrastructure.config import Settings
from launchcase.infrastructure.models import Identity, Task
from launchcase.infrastructure.tasks import TaskManager
from launchcase.workflow.graph import execute_task


def recover_once(service):
    with service.sessions() as s:
        pending = list(
            s.scalars(
                select(Task)
                .where(
                    or_(
                        Task.status == "queued", (Task.status == "running") & (Task.lease_until < time.time())
                    ),
                )
                .order_by(Task.created_at)
                .limit(20)
            )
        )
        work = []
        for task in pending:
            identity = s.scalar(
                select(Identity).where(Identity.tenant_id == task.tenant_id, Identity.role == "owner")
            )
            if identity:
                # Worker executes already-persisted bounded work, never gate mutations.
                work.append((Actor(identity.id, identity.tenant_id, "agent", identity.synthetic), task.id))
    results = []
    for actor, task_id in work:
        try:
            task = TaskManager(service).expire_exhausted(actor, task_id)
            results.append(task if task["status"] == "failed" else execute_task(service, actor, task_id))
        except Exception as exc:
            results.append({"task_id": task_id, "error": type(exc).__name__})
    return results


async def wakeup(ctx):
    import asyncio

    return await asyncio.to_thread(recover_once, CaseService(Settings.from_env()))


class WorkerSettings:
    functions = [wakeup]
    max_jobs = 1
