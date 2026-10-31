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
    feasibility: dict
    pack_id: str


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
        payload = interrupt({"gate": "G2", "case_id": state["case_id"], "reason": "Human concept/Spec review required"})
        with service.sessions() as s:
            if not ProductService(service).current(s, actor, state["case_id"], "G2", {"select"}):
                raise DomainError("GATE_BLOCKED", "Current G2 required", 409)
        return {"task_id": payload["task_id"], "fence": payload["fence"]}

    def feasibility(state):
        from launchcase.application.feasibility import FeasibilityService
        with service.sessions() as s:
            TaskManager(service).check_fence(s, actor, state["task_id"], state["fence"])
        result = FeasibilityService(service).evaluate(actor, state["case_id"], None, "task-feasibility-"+state["task_id"])
        return {"feasibility": result}

    def g3(state):
        payload = interrupt({"gate": "G3", "case_id": state["case_id"], "reason": "Sample investigation requires a human decision; unknown costs remain unknown"})
        with service.sessions() as s:
            if not ProductService(service).current(s, actor, state["case_id"], "G3", {"sample_validation"}):
                raise DomainError("GATE_BLOCKED", "Current G3 required", 409)
        return {"task_id": payload["task_id"], "fence": payload["fence"]}

    def draft(state):
        from launchcase.application.launchpacks import LaunchPackService
        result = LaunchPackService(service).build(actor, state["case_id"], "task-pack-"+state["task_id"])
        return {"pack_id": result["id"]}

    def g4(state):
        interrupt({"gate": "G4", "case_id": state["case_id"], "reason": "Real sample evidence required; internal draft does not pass this gate"})
        with service.sessions() as s:
            if not ProductService(service).current(s, actor, state["case_id"], "G4", {"verify_sample"}):
                raise DomainError("GATE_BLOCKED", "Real G4 required", 409)
        return {}

    def g5(state):
        interrupt({"gate": "G5", "case_id": state["case_id"], "reason": "Launch review requires verified truth and current rules; no publication"})
        return {}

    graph.add_node("validate_brief", validate)
    graph.add_node("normalize_sources", lambda state: research.snapshot(actor, state["case_id"]) and {})
    graph.add_node("research_merge_propose", investigate)
    graph.add_node("G1", g1)
    graph.add_node("develop_concepts", develop)
    graph.add_node("G2", g2)
    graph.add_node("calculate_feasibility", feasibility)
    graph.add_node("G3", g3)
    graph.add_node("build_internal_draft", draft)
    graph.add_node("G4", g4)
    graph.add_node("G5", g5)
    graph.add_edge(START, "validate_brief")
    graph.add_edge("validate_brief", "normalize_sources")
    graph.add_edge("normalize_sources", "research_merge_propose")
    graph.add_edge("research_merge_propose", "G1")
    graph.add_conditional_edges("G1", lambda state: "stop" if state.get("waiting_for") == "needs_input" else "concepts", {"stop": END, "concepts": "develop_concepts"})
    graph.add_edge("develop_concepts", "G2")
    graph.add_edge("G2", "calculate_feasibility")
    graph.add_edge("calculate_feasibility", "G3")
    graph.add_edge("G3", "build_internal_draft")
    graph.add_edge("build_internal_draft", "G4")
    graph.add_edge("G4", "G5")
    graph.add_edge("G5", END)
    return graph.compile(checkpointer=checkpointer)


def enqueue_run(service, actor, case_id, kind, key):
    if kind in {"feasibility", "launch_draft"}:
        from launchcase.application.feasibility import FeasibilityService
        with service.sessions() as s:
            service.case_row(s, actor, case_id)
            gate = ProductService(service).current(s, actor, case_id, "G2" if kind == "feasibility" else "G3", {"select"} if kind == "feasibility" else {"sample_validation"})
            if not gate:
                raise DomainError("GATE_BLOCKED", "Current prior gate required", 409)
            valid, invalid = FeasibilityService(service).source_validity(s, actor, case_id)
            snapshot = {"gate_id": gate.id, "gate_hash": gate.subject_hash, "valid_cost_sources": valid, "invalid_cost_sources": invalid}
        return TaskManager(service).enqueue(actor, case_id, kind, snapshot, key)
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
            if task["kind"] in {"concepts", "feasibility", "launch_draft"}:
                saved = graph.get_state(config)
                gate, prior = {"concepts": ("G1", "research_merge_propose"), "feasibility": ("G2", "develop_concepts"), "launch_draft": ("G3", "calculate_feasibility")}[task["kind"]]
                if saved.next != (gate,):
                    # New G1 selection after an earlier concept review: re-enter the same business gate.
                    graph.update_state(config, state, as_node=prior)
                    graph.invoke(None, config)
                result = graph.invoke(Command(resume={"task_id": task_id, "fence": task["fence"]}), config)
            else:
                result = graph.invoke(state, config)
            result.pop("__interrupt__", None)
            waiting = {"concepts": "G2", "feasibility": "G3", "launch_draft": "G4"}.get(task["kind"], "G1" if result.get("research", {}).get("sufficiency", {}).get("draft_minimum_met") else "needs_input")
            return manager.finish(actor, task_id, task["fence"], {"checkpoint_thread": config["configurable"]["thread_id"], "waiting_for": waiting, "pack_id": result.get("pack_id")})
    except Exception as exc:
        code = exc.code if isinstance(exc, DomainError) else type(exc).__name__
        manager.finish(actor, task_id, task["fence"], error=code)
        raise
