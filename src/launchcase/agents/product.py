import asyncio
import json

from agents import Agent, RunConfig, Runner, function_tool
from pydantic import Field

from launchcase.agents.runtime import DeterministicModel, skill_snapshot
from launchcase.domain.common import Contract


class ConceptDraft(Contract):
    title: str
    design_intent: str
    differentiators: list[str]
    risks: list[str]
    validation_plan: str


class ProductOutput(Contract):
    concepts: list[ConceptDraft] = Field(min_length=2, max_length=3)


class ProductRunner:
    def run(self, context):
        return asyncio.run(self.arun(context))

    async def arun(self, context):
        hashes, method = skill_snapshot(["product-definition", "concept-design"])
        output = ProductOutput(concepts=[
            ConceptDraft(title="Guided tool-free assembly", design_intent="Keyed panels and captive connectors to reduce alignment steps",
                differentiators=["Assembly-first interface", "Visible orientation marks", "Replaceable connectors"],
                risks=["Connector retention and pet access are untested", "Tolerance stack and tooling cost unknown"],
                validation_plan="Compare assembly errors and time on physical prototypes with target users."),
            ConceptDraft(title="Compact modular panel system", design_intent="Modular flat-pack panels with replaceable sections and smaller carry units",
                differentiators=["Carry-unit compactness", "Repairable panel modules", "Configurable assembly sequence"],
                risks=["Additional joints may reduce rigidity", "Shipping savings and assembly tradeoff unverified"],
                validation_plan="Measure packed volume, carry effort and joint performance using actual samples.")])

        @function_tool
        def list_evidence() -> str:
            """Read the approved opportunity and its references only."""
            return json.dumps(context)

        model = DeterministicModel(output.model_dump())
        result = await asyncio.wait_for(Runner.run(Agent(name="Product", instructions=method,
            model=model, tools=[list_evidence], output_type=ProductOutput), "Propose distinct internal concepts for this approved opportunity.",
            max_turns=3, run_config=RunConfig(tracing_disabled=True)), 20)
        data = result.final_output.model_dump()
        return {"concepts": data["concepts"], "run": {"provider": "fake_sdk", "role": "Product", "skill_hashes": hashes,
            "model_calls": model.calls, "paid_calls": 0, "fixture_directions": True, "status": "tested_offline"}}
