import time

from sqlalchemy import or_, select, update

from launchcase.application.services import row_dict
from launchcase.domain.common import DomainError, digest
from launchcase.infrastructure.models import Attempt, Task


class TaskManager:
    """Durable work/lease authority. Queue messages are wakeups, never records."""

    def __init__(self, service):
        self.service = service

    def enqueue(self, actor, case_id, kind, input_data, key):
        def run(s):
            self.service.case_row(s, actor, case_id, True)
            hashed = digest(input_data)
            old = s.scalar(
                select(Task).where(
                    Task.tenant_id == actor.tenant_id,
                    Task.case_id == case_id,
                    Task.kind == kind,
                    Task.input_hash == hashed,
                )
            )
            if old:
                return row_dict(old)
            task = Task(
                tenant_id=actor.tenant_id,
                case_id=case_id,
                kind=kind,
                input_hash=hashed,
                input_data=input_data,
            )
            s.add(task)
            s.flush()
            self.service.event(s, actor, case_id, "task.queued", {"task_id": task.id, "kind": kind})
            return row_dict(task)

        return self.service.command(
            actor, key, {"action": "task.enqueue", "case": case_id, "kind": kind, "input": input_data}, run
        )

    def claim(self, actor, task_id, owner, lease_seconds=60):
        clock = time.time()
        with self.service.write() as s:
            self.service.get_row(s, Task, actor, task_id)
            result = s.execute(
                update(Task)
                .where(
                    Task.id == task_id,
                    Task.tenant_id == actor.tenant_id,
                    Task.attempts < 3,
                    or_(Task.status == "queued", (Task.status == "running") & (Task.lease_until < clock)),
                )
                .values(
                    status="running",
                    lease_owner=owner,
                    lease_until=clock + lease_seconds,
                    fence=Task.fence + 1,
                    attempts=Task.attempts + 1,
                )
            )
            if result.rowcount != 1:
                return None
            task = self.service.get_row(s, Task, actor, task_id)
            s.add(Attempt(tenant_id=actor.tenant_id, task_id=task.id, fence=task.fence, owner=owner))
            return row_dict(task)

    def check_fence(self, s, actor, task_id, fence):
        task = self.service.get_row(s, Task, actor, task_id)
        if task.status != "running" or task.fence != fence or task.lease_until < time.time():
            raise DomainError("LEASE_LOST", "Task lease was replaced or expired", 409)
        return task

    def finish(self, actor, task_id, fence, result=None, error=None):
        with self.service.write() as s:
            task = self.check_fence(s, actor, task_id, fence)
            task.status = "failed" if error else "succeeded"
            task.error_code = error
            task.result = result or {}
            task.lease_until = 0
            attempt = s.scalar(
                select(Attempt).where(
                    Attempt.tenant_id == actor.tenant_id, Attempt.task_id == task_id, Attempt.fence == fence
                )
            )
            attempt.status = task.status
            self.service.event(
                s, actor, task.case_id, "task.finished", {"task_id": task.id, "status": task.status}
            )
            return row_dict(task)

    def get(self, actor, task_id):
        with self.service.sessions() as s:
            return row_dict(self.service.get_row(s, Task, actor, task_id))

    def expire_exhausted(self, actor, task_id):
        with self.service.write() as s:
            task = self.service.get_row(s, Task, actor, task_id)
            if task.status == "running" and task.lease_until < time.time() and task.attempts >= 3:
                task.status, task.error_code, task.lease_until = "failed", "ATTEMPTS_EXHAUSTED", 0
                attempt = s.scalar(
                    select(Attempt).where(
                        Attempt.tenant_id == actor.tenant_id,
                        Attempt.task_id == task_id,
                        Attempt.fence == task.fence,
                    )
                )
                if attempt:
                    attempt.status = "failed"
                self.service.event(s, actor, task.case_id, "task.exhausted", {"task_id": task.id})
            return row_dict(task)
