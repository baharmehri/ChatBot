from __future__ import annotations

import os
from typing import AsyncGenerator, Dict, Iterable

from google.adk.agents import Agent, BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events.event import Event
from google.adk.events.event_actions import EventActions
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import FunctionTool
from google.adk.utils.context_utils import Aclosing
from google.genai import types

from chatbot_agent.agents.supervisor_routing import (
    ROUTING_FALLBACK_MESSAGE,
    route_for_query,
)
from chatbot_agent.prompts.multi_agent_prompts import (
    HISTORY_LIFESTYLE_AGENT_PROMPT,
    LABS_AGENT_PROMPT,
    MEDICATION_AGENT_PROMPT,
    PROFILE_AGENT_PROMPT,
    VITALS_AGENT_PROMPT,
)
from chatbot_agent.tools.medical_tools_web_mock import (
    add_blood_pressure_measurement,
    add_blood_sugar_measurement,
    add_weight_measurement,
    get_labs,
    get_lifestyle_summary,
    get_measurements,
    get_medical_history_summary,
    get_medication_schedule,
    get_user_profile_summary,
    get_weight_trend,
)

DEFAULT_MODEL = "gpt-4o-mini"


class SupervisorRouterAgent(BaseAgent):
    """
    Rule-based supervisor for the ADK web runtime. Delegates execution to specialized
    LLM workers and never performs medical reasoning directly.
    """

    def __init__(self, *, workers: Dict[str, Agent]):
        super().__init__(
            name="SupervisorAgent",
            description="Routes Persian medical questions to specialized workers.",
        )
        self._workers = workers
        self.sub_agents = []
        for worker in workers.values():
            worker.parent_agent = self
            self.sub_agents.append(worker)

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        query = _content_to_text(ctx.user_content)
        route = route_for_query(query)
        if not route:
            yield self._build_text_event(ctx, ROUTING_FALLBACK_MESSAGE)
            return

        worker = self._workers.get(route)
        if not worker:
            yield self._build_text_event(ctx, ROUTING_FALLBACK_MESSAGE)
            return

        async with Aclosing(worker.run_async(ctx)) as agen:
            async for event in agen:
                yield event

    async def _run_live_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        async with Aclosing(self._run_async_impl(ctx)) as agen:
            async for event in agen:
                yield event

    def _build_text_event(self, ctx: InvocationContext, message: str) -> Event:
        content = types.Content(role=self.name, parts=[types.Part(text=message)])
        return Event(
            invocation_id=ctx.invocation_id,
            author=self.name,
            content=content,
            actions=EventActions(),
            branch=ctx.branch,
        )


def _build_llm():
    model_name = os.getenv("OPENAI_MODEL_NAME", DEFAULT_MODEL)
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY must be set to run the PersianMedicalWebAgent."
        )
    api_base = os.getenv("OPENAI_API_BASE")

    return LiteLlm(model=model_name, api_key=api_key, api_base=api_base)


def _worker(name: str, instruction: str, tool_fns: Iterable):
    return Agent(
        name=name,
        description=name,
        model=_build_llm(),
        instruction=instruction,
        tools=[FunctionTool(func) for func in tool_fns],
    )


def _create_workers() -> Dict[str, Agent]:
    return {
        "profile": _worker(
            "ProfileAgent",
            PROFILE_AGENT_PROMPT,
            [get_user_profile_summary],
        ),
        "history": _worker(
            "HistoryLifestyleAgent",
            HISTORY_LIFESTYLE_AGENT_PROMPT,
            [get_medical_history_summary, get_lifestyle_summary],
        ),
        "vitals": _worker(
            "VitalsAgent",
            VITALS_AGENT_PROMPT,
            [
                get_measurements,
                get_weight_trend,
                add_blood_pressure_measurement,
                add_blood_sugar_measurement,
                add_weight_measurement,
            ],
        ),
        "labs": _worker(
            "LabsAgent",
            LABS_AGENT_PROMPT,
            [get_labs],
        ),
        "medication": _worker(
            "MedicationAgent",
            MEDICATION_AGENT_PROMPT,
            [get_medication_schedule],
        ),
    }


def _content_to_text(content: types.Content | None) -> str:
    if not content or not content.parts:
        return ""
    lines = []
    for part in content.parts:
        if part.text:
            lines.append(part.text)
    return "\n".join(lines)


def create_web_agent():
    workers = _create_workers()
    return SupervisorRouterAgent(workers=workers)
