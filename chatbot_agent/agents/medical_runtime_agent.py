from __future__ import annotations

from asgiref.sync import sync_to_async
from google.adk.tools import FunctionTool
from google.genai import types

from chatbot_agent.agents.base_agent import BaseAgent
from chatbot_agent.conversation_state import (
    default_conversation_state,
    extract_response_and_state,
    serialize_state,
    validate_conversation_state,
)
from chatbot_agent.prompts.medical_prompts import build_dynamic_prompt
from chatbot_agent.tools.medical_tools_runtime import *
from telegram_bot.models import ConversationState


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
            instruction="Follow the prompt provided in the user message.",
            tools=tools,
        )

    @classmethod
    async def create(cls, user_id: str, session_id: str) -> "PersianMedicalAgent":
        instance = cls(user_id=user_id)
        return await instance._async_init(session_id=session_id)

    async def call_agent_async(self, query: str) -> str:
        if not self.runner or not self.session:
            raise RuntimeError(
                "Agent is not fully initialized. "
                "Use the '.create()' factory method to instantiate the agent."
            )

        sanitized_query = query.encode("utf-8", "replace").decode("utf-8")
        conversation_state = await self._load_conversation_state()
        prompt = build_dynamic_prompt(serialize_state(conversation_state), sanitized_query)
        content = types.Content(role="user", parts=[types.Part(text=prompt)])

        final_response_text = self.error_message
        updated_state = conversation_state

        async for event in self.runner.run_async(
            user_id=self.user_id, session_id=self.session.id, new_message=content
        ):
            if event.is_final_response():
                if event.content and event.content.parts:
                    raw_text = event.content.parts[0].text
                    sanitized_text = raw_text.encode("utf-8", "replace").decode("utf-8")
                    final_response_text, updated_state = extract_response_and_state(
                        sanitized_text, conversation_state
                    )
                    if validate_conversation_state(updated_state):
                        await self._save_conversation_state(updated_state)
                elif event.actions and event.actions.escalate:
                    final_response_text = self.error_message
                    await self.reset_session(session_id=self.session.id)
                break

        await self.reset_session(session_id=self.session.id)
        return final_response_text

    async def _load_conversation_state(self):
        state = await sync_to_async(_load_conversation_state_sync)(
            external_user_id=self.user_id,
            session_id=self.session.id,
        )
        if not validate_conversation_state(state):
            return default_conversation_state()
        return state

    async def _save_conversation_state(self, state):
        await sync_to_async(_save_conversation_state_sync)(
            external_user_id=self.user_id,
            session_id=self.session.id,
            state=state,
        )


def _load_conversation_state_sync(*, external_user_id: str, session_id: str):
    record = ConversationState.objects.filter(
        external_user_id=external_user_id, session_id=session_id
    ).first()
    if record and isinstance(record.state, dict):
        return record.state
    return default_conversation_state()


def _save_conversation_state_sync(
    *, external_user_id: str, session_id: str, state
):
    ConversationState.objects.update_or_create(
        external_user_id=external_user_id,
        session_id=session_id,
        defaults={"state": state},
    )
