from __future__ import annotations

from google.adk.tools import FunctionTool

from chatbot_agent.agents.base_agent import BaseAgent
from chatbot_agent.prompts.multi_agent_prompts import (
    HISTORY_LIFESTYLE_AGENT_PROMPT,
    LABS_AGENT_PROMPT,
    MEDICATION_AGENT_PROMPT,
    PROFILE_AGENT_PROMPT,
    VITALS_AGENT_PROMPT,
)
from chatbot_agent.tools.medical_tools_runtime import (
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


class ProfileAgent(BaseAgent):
    """Agent responsible for profile level answers."""

    def __init__(self, user_id: str):
        tools = [FunctionTool(get_user_profile_summary)]
        super().__init__(
            user_id=user_id,
            agent_name="ProfileAgent",
            instruction=PROFILE_AGENT_PROMPT,
            tools=tools,
        )

    @classmethod
    async def create(cls, user_id: str, session_id: str) -> "ProfileAgent":
        instance = cls(user_id=user_id)
        return await instance._async_init(session_id=session_id)


class HistoryLifestyleAgent(BaseAgent):
    """Agent for medical history and lifestyle details."""

    def __init__(self, user_id: str):
        tools = [
            FunctionTool(get_medical_history_summary),
            FunctionTool(get_lifestyle_summary),
        ]
        super().__init__(
            user_id=user_id,
            agent_name="HistoryLifestyleAgent",
            instruction=HISTORY_LIFESTYLE_AGENT_PROMPT,
            tools=tools,
        )

    @classmethod
    async def create(cls, user_id: str, session_id: str) -> "HistoryLifestyleAgent":
        instance = cls(user_id=user_id)
        return await instance._async_init(session_id=session_id)


class VitalsAgent(BaseAgent):
    """Agent covering vitals measurements and updates."""

    def __init__(self, user_id: str):
        tools = [
            FunctionTool(get_measurements),
            FunctionTool(get_weight_trend),
            FunctionTool(add_blood_pressure_measurement),
            FunctionTool(add_blood_sugar_measurement),
            FunctionTool(add_weight_measurement),
        ]
        super().__init__(
            user_id=user_id,
            agent_name="VitalsAgent",
            instruction=VITALS_AGENT_PROMPT,
            tools=tools,
        )

    @classmethod
    async def create(cls, user_id: str, session_id: str) -> "VitalsAgent":
        instance = cls(user_id=user_id)
        return await instance._async_init(session_id=session_id)


class LabsAgent(BaseAgent):
    """Agent that reports on laboratory data."""

    def __init__(self, user_id: str):
        tools = [FunctionTool(get_labs)]
        super().__init__(
            user_id=user_id,
            agent_name="LabsAgent",
            instruction=LABS_AGENT_PROMPT,
            tools=tools,
        )

    @classmethod
    async def create(cls, user_id: str, session_id: str) -> "LabsAgent":
        instance = cls(user_id=user_id)
        return await instance._async_init(session_id=session_id)


class MedicationAgent(BaseAgent):
    """Agent for medication schedules."""

    def __init__(self, user_id: str):
        tools = [FunctionTool(get_medication_schedule)]
        super().__init__(
            user_id=user_id,
            agent_name="MedicationAgent",
            instruction=MEDICATION_AGENT_PROMPT,
            tools=tools,
        )

    @classmethod
    async def create(cls, user_id: str, session_id: str) -> "MedicationAgent":
        instance = cls(user_id=user_id)
        return await instance._async_init(session_id=session_id)
