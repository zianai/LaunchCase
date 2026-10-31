from typing import TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from launchcase.application.research import ResearchService
from launchcase.domain.common import DomainError, uid
from launchcase.infrastructure.tasks import TaskManager


class State(TypedDict, total=False):
    case_id: str
    task_id: str
    fence: int
    research: dict
    waiting_for: str


def build_graph(service, actor, checkpointer):
    research = ResearchService(service)
    graph = StateGraph(State)

    def validate(state):
        service.get_case(actor, state["case_id"])
        return {}

    def investigate(state):
        return {"research": research.execute(actor, state["task_id"], state["fence"])}

    def g1(state):
        if not state["research"]["sufficiency"]["draft_minimum_met"]:
            return {"waiting_for": "needs_input"}
        interrupt({"gate": "G1", "case_id": state["case_id"], "reason": "Human opportunity selection required"})
        return {"waiting_for": "G1"}

    graph.add_node("validate_brief", validate)
    graph.add_node("normalize_sources", lambda state: research.snapshot(actor, state["case_id"]) and {})
    graph.add_node("research_merge_propose", investigate)
    graph.add_node("G1", g1)
    graph.add_edge(START, "validate_brief")
    graph.add_edge("validate_brief", "normalize_sources")
    graph.add_edge("normalize_sources", "research_merge_propose")
    graph.add_edge("research_merge_propose", "G1")
    graph.add_edge("G1", END)
    return graph.compile(checkpointer=checkpointer)


def enqueue_run(service, actor, case_id, kind, key):
    if kind not in {"research", "opportunities"}:
        raise DomainError("RUN_UNAVAILABLE", "Unsupported run type")
    snapshot = ResearchService(service).snapshot(actor, case_id)
    return TaskManager(service).enqueue(actor, case_id, "research", snapshot, key)


def execute_task(service, actor, task_id):
    manager = TaskManager(service)
    task = manager.claim(actor, task_id, uid())
    if not task:
        return manager.get(actor, task_id)
    try:
        with SqliteSaver.from_conn_string(str(service.settings.data_dir / "checkpoints.db")) as saver:
            graph = build_graph(service, actor, saver)
            config = {"configurable": {"thread_id": f'{actor.tenant_id}:{task["case_id"]}:{task["input_hash"]}'}}
            state = {"case_id": task["case_id"], "task_id": task_id, "fence": task["fence"]}
            result = graph.invoke(state, config)
            result.pop("__interrupt__", None)
            return manager.finish(actor, task_id, task["fence"], {"checkpoint_thread": config["configurable"]["thread_id"], "waiting_for": "G1" if result.get("research", {}).get("sufficiency", {}).get("draft_minimum_met") else "needs_input"})
    except Exception as exc:
        code = exc.code if isinstance(exc, DomainError) else type(exc).__name__
        manager.finish(actor, task_id, task["fence"], error=code)
        raise
