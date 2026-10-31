from typing import TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from launchcase.application.products import ProductService
from launchcase.application.research import ResearchService
from launchcase.domain.common import DomainError, uid
from launchcase.infrastructure.tasks import TaskManager


class State(TypedDict, total=False):
    case_id: str
    task_id: str
    fence: int
    research: dict
    waiting_for: str
    concepts: dict


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
        payload = interrupt({"gate": "G1", "case_id": state["case_id"], "reason": "Human opportunity selection required"})
        ProductService(service).concept_input(actor, state["case_id"])
        return {"task_id": payload["task_id"], "fence": payload["fence"], "waiting_for": "G2"}

    def develop(state):
        return {"concepts": ProductService(service).develop(actor, state["task_id"], state["fence"])}

    def g2(state):
        interrupt({"gate": "G2", "case_id": state["case_id"], "reason": "Human concept/Spec review required"})
        return {"waiting_for": "G2"}

    graph.add_node("validate_brief", validate)
    graph.add_node("normalize_sources", lambda state: research.snapshot(actor, state["case_id"]) and {})
    graph.add_node("research_merge_propose", investigate)
    graph.add_node("G1", g1)
    graph.add_node("develop_concepts", develop)
    graph.add_node("G2", g2)
    graph.add_edge(START, "validate_brief")
    graph.add_edge("validate_brief", "normalize_sources")
    graph.add_edge("normalize_sources", "research_merge_propose")
    graph.add_edge("research_merge_propose", "G1")
    graph.add_conditional_edges("G1", lambda state: "stop" if state.get("waiting_for") == "needs_input" else "concepts", {"stop": END, "concepts": "develop_concepts"})
    graph.add_edge("develop_concepts", "G2")
    graph.add_edge("G2", END)
    return graph.compile(checkpointer=checkpointer)


def enqueue_run(service, actor, case_id, kind, key):
    if kind == "concepts":
        snapshot = ProductService(service).concept_input(actor, case_id)
        return TaskManager(service).enqueue(actor, case_id, kind, snapshot, key)
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
            from launchcase.domain.common import digest
            source_hash = digest(ResearchService(service).snapshot(actor, task["case_id"]))
            config = {"configurable": {"thread_id": f'{actor.tenant_id}:{task["case_id"]}:{source_hash}'}}
            state = {"case_id": task["case_id"], "task_id": task_id, "fence": task["fence"]}
            if task["kind"] == "concepts":
                saved = graph.get_state(config)
                if saved.next != ("G1",):
                    # New G1 selection after an earlier concept review: re-enter the same business gate.
                    graph.update_state(config, state, as_node="research_merge_propose")
                    graph.invoke(None, config)
                result = graph.invoke(Command(resume={"task_id": task_id, "fence": task["fence"]}), config)
            else:
                result = graph.invoke(state, config)
            result.pop("__interrupt__", None)
            waiting = "G2" if task["kind"] == "concepts" else "G1" if result.get("research", {}).get("sufficiency", {}).get("draft_minimum_met") else "needs_input"
            return manager.finish(actor, task_id, task["fence"], {"checkpoint_thread": config["configurable"]["thread_id"], "waiting_for": waiting})
    except Exception as exc:
        code = exc.code if isinstance(exc, DomainError) else type(exc).__name__
        manager.finish(actor, task_id, task["fence"], error=code)
        raise
