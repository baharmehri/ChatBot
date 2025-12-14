from __future__ import annotations

from google.adk.tools import FunctionTool

from chatbot_agent.agents.base_agent import BaseAgent
from chatbot_agent.prompts.medical_prompts import MEDICAL_AGENT_PROMPT
from chatbot_agent.tools.medical_tools_runtime import *


class PersianMedicalAgent(BaseAgent):
    """
    Medical chatbot specialized for answering Persian queries using structured user data.
    """

    def __init__(self, user_id: str):
        tools = [
            FunctionTool(add_blood_pressure_measurement),
            FunctionTool(add_blood_sugar_measurement),
            FunctionTool(add_weight_measurement),
            FunctionTool(get_user_profile_summary),
            FunctionTool(get_medical_history_summary),
            FunctionTool(get_lifestyle_summary),
            FunctionTool(get_weight_trend),
            FunctionTool(get_measurements),
            FunctionTool(get_labs),
            FunctionTool(get_medication_schedule),
        ]

        super().__init__(
            user_id=user_id,
            agent_name="PersianMedicalAgent",
            instruction=MEDICAL_AGENT_PROMPT,
            tools=tools,
        )

    @classmethod
    async def create(cls, user_id: str, session_id: str) -> "PersianMedicalAgent":
        instance = cls(user_id=user_id)
        return await instance._async_init(session_id=session_id)
