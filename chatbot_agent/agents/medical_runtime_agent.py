from __future__ import annotations

from chatbot_agent.agents.supervisor_agent import SupervisorAgent


class PersianMedicalAgent:
    """
    Backwards compatible façade that exposes the old agent interface while delegating to
    the new supervisor-based multi-agent system.
    """

    def __init__(self, supervisor: SupervisorAgent):
        self._supervisor = supervisor

    @classmethod
    async def create(cls, user_id: str, session_id: str) -> "PersianMedicalAgent":
        supervisor = await SupervisorAgent.create(user_id=user_id, session_id=session_id)
        return cls(supervisor=supervisor)

    async def call_agent_async(self, query: str) -> str:
        return await self._supervisor.call_agent_async(query)

    async def reset_session(self, session_id: str) -> None:
        await self._supervisor.reset_session(session_id=session_id)
