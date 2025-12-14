import os

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import FunctionTool

from chatbot_agent.prompts.medical_prompts import MEDICAL_AGENT_PROMPT
from chatbot_agent.tools.medical_tools_web_mock import *

DEFAULT_MODEL = "gpt-4o-mini"


def _build_llm():
    model_name = os.getenv("OPENAI_MODEL_NAME", DEFAULT_MODEL)
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY must be set to run the PersianMedicalWebAgent."
        )
    api_base = os.getenv("OPENAI_API_BASE")

    return LiteLlm(model=model_name, api_key=api_key, api_base=api_base)


def create_web_agent():
    return Agent(
        name="PersianMedicalWebAgent",
        model=_build_llm(),
        instruction=MEDICAL_AGENT_PROMPT,
        tools=[
            FunctionTool(get_user_profile_summary),
            FunctionTool(get_medical_history_summary),
            FunctionTool(get_lifestyle_summary),
            FunctionTool(get_weight_trend),
            FunctionTool(get_measurements),
            FunctionTool(get_labs),
            FunctionTool(get_medication_schedule),
            FunctionTool(add_weight_measurement),
            FunctionTool(add_blood_pressure_measurement),
            FunctionTool(add_blood_sugar_measurement),
        ],
    )
