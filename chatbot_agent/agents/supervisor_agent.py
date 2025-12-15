from __future__ import annotations

from typing import Dict, Optional, Type

from chatbot_agent.agents.base_agent import BaseAgent
from chatbot_agent.agents.medical_workers import (
    HistoryLifestyleAgent,
    LabsAgent,
    MedicationAgent,
    ProfileAgent,
    VitalsAgent,
)
from chatbot_agent.agents.supervisor_routing import (
    ROUTING_FALLBACK_MESSAGE,
    route_for_query,
)


class SupervisorAgent:
    """
    Lightweight rule-based supervisor that routes requests to specialized agents.
    """

    _WORKER_MAP: Dict[str, Type[BaseAgent]] = {
        "profile": ProfileAgent,
        "history": HistoryLifestyleAgent,
        "vitals": VitalsAgent,
        "labs": LabsAgent,
        "medication": MedicationAgent,
    }

    def __init__(self, user_id: str, session_id: str):
        self.user_id = user_id
        self.session_id = session_id
        self._agents: Dict[str, BaseAgent] = {}
        self._has_seen_user_question = False
        self._last_route: Optional[str] = None

    @classmethod
    async def create(cls, user_id: str, session_id: str) -> "SupervisorAgent":
        return cls(user_id=user_id, session_id=session_id)

    async def call_agent_async(self, query: str) -> str:
        normalized = (query or "").strip()

        # FIRST TURN → greet and wait (only once)
        if not self._has_seen_user_question:
            self._has_seen_user_question = True
            return (
                "سلام 👋\n"
                "من دستیار سلامت شما هستم.\n"
                "می‌توانید درباره آزمایش‌ها، علائم حیاتی، داروها "
                "یا پروفایل پزشکی خود سوال بپرسید."
            )

        # Ignore empty inputs after greeting
        if not normalized:
            return ""

        # Try explicit routing based on current message
        route = self._route(normalized)
        if route:
            self._last_route = route
            agent = await self._get_agent(route)
            return await agent.call_agent_async(normalized)

        # If no explicit route, but we have conversation context
        if self._last_route:
            agent = await self._get_agent(self._last_route)
            return await agent.call_agent_async(normalized)

        # Fallback only if nothing else applies
        return ROUTING_FALLBACK_MESSAGE

    async def reset_session(self, session_id: str) -> None:
        self.session_id = session_id
        for agent in self._agents.values():
            await agent.reset_session(session_id=session_id)

    async def _get_agent(self, name: str) -> BaseAgent:
        agent = self._agents.get(name)
        if agent is None:
            agent_cls = self._WORKER_MAP[name]
            agent = await agent_cls.create(user_id=self.user_id, session_id=self.session_id)
            self._agents[name] = agent
        return agent

    def _route(self, query: str) -> Optional[str]:
        return route_for_query(query)
