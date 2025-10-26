from __future__ import annotations

import os
from typing import List, Optional
from urllib.parse import quote_plus

from django.conf import settings
from dotenv import load_dotenv

from google.adk.agents import LlmAgent
from google.adk.memory import InMemoryMemoryService
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService, Session
from google.adk.tools import FunctionTool
from google.genai import types

load_dotenv(settings.BASE_DIR / ".env")


def _build_db_url() -> str:
    """Translate Django's DATABASE settings into a SQLAlchemy-style URL."""
    db = settings.DATABASES["default"]
    engine = db.get("ENGINE", "")

    if engine == "django.db.backends.sqlite3":
        return f"sqlite:///{db['NAME']}"

    scheme_map = {
        "django.db.backends.postgresql": "postgresql+psycopg2",
        "django.db.backends.postgresql_psycopg2": "postgresql+psycopg2",
        "django.db.backends.mysql": "mysql+pymysql",
        "django.db.backends.oracle": "oracle+cx_oracle",
    }

    scheme = scheme_map.get(engine)
    if not scheme:
        raise ValueError(f"Unsupported database engine '{engine}' for BaseAgent.")

    user = db.get("USER", "")
    password = db.get("PASSWORD", "")
    host = db.get("HOST", "localhost")
    port = db.get("PORT", "")
    name = db.get("NAME", "")

    user_encoded = quote_plus(user) if user else ""
    password_encoded = quote_plus(password) if password else ""

    auth = ""
    if user_encoded or password_encoded:
        auth = user_encoded
        if password_encoded:
            auth = f"{auth}:{password_encoded}" if auth else f":{password_encoded}"
        auth = f"{auth}@"

    netloc = host or ""
    if port:
        netloc = f"{netloc}:{port}" if netloc else f":{port}"

    return f"{scheme}://{auth}{netloc}/{name}"


class BaseAgent:
    def __init__(
            self,
            user_id: str,
            agent_name: str,
            instruction: str,
            tools: List[FunctionTool],
            error_message: str = "مشکلی وجود دارد، لطفا بعدا تلاش کنید",
    ):
        """
        Synchronous constructor. Initializes basic components.
        The full initialization requires the _async_init method.
        """
        self.user_id = user_id

        model_name = os.getenv("OPENAI_MODEL_NAME")
        api_base = os.getenv("OPENAI_API_BASE")
        api_key = os.getenv("OPENAI_API_KEY")

        self.error_message = error_message

        self._agent = LlmAgent(
            name=agent_name,
            model=LiteLlm(model=model_name, api_key=api_key, api_base=api_base),
            description=agent_name,
            instruction=instruction,
            tools=tools,
        )

        self.session_service = DatabaseSessionService(db_url=_build_db_url())
        self.memory_service = InMemoryMemoryService()

        self.session: Optional[Session] = None
        self.runner: Optional[Runner] = None

    async def _async_init(self, session_id: str) -> "BaseAgent":
        """
        Asynchronous initializer. Fetches or creates the session and
        initializes the runner.
        """
        session = await self.get_session(session_id=session_id)
        if not session:
            session = await self.create_new_session(session_id=session_id)
        self.set_session(session)

        self.runner = Runner(
            agent=self.agent,
            app_name=self.app_name,
            session_service=self.session_service,
            memory_service=self.memory_service,
        )
        return self

    @property
    def agent(self):
        return self._agent

    @property
    def app_name(self):
        return self._agent.name

    async def reset_session(self, session_id: str) -> Session:
        """Deletes the old session and creates/returns a new one."""
        await self.session_service.delete_session(
            app_name=self.app_name, user_id=self.user_id, session_id=session_id
        )
        new_session = await self.create_new_session(session_id=session_id)
        self.session = new_session
        return new_session

    async def create_new_session(self, session_id: str) -> Session:
        """Asynchronously creates a new session."""
        session = await self.session_service.create_session(
            app_name=self.app_name,
            user_id=self.user_id,
            session_id=session_id,
        )
        return session

    async def get_session(self, session_id: Optional[str] = None) -> Session:
        """Asynchronously gets an existing session."""
        session = await self.session_service.get_session(
            app_name=self.app_name, user_id=self.user_id, session_id=session_id
        )
        return session

    def set_session(self, session: Session) -> None:
        self.session = session

    async def call_agent_async(self, query: str) -> str:
        """Asynchronously calls the agent with a user query."""
        if not self.runner or not self.session:
            raise RuntimeError(
                "Agent is not fully initialized. "
                "Use the '.create()' factory method to instantiate the agent."
            )

        sanitized_query = query.encode("utf-8", "replace").decode("utf-8")
        content = types.Content(role="user", parts=[types.Part(text=sanitized_query)])

        final_response_text = self.error_message

        async for event in self.runner.run_async(
                user_id=self.user_id, session_id=self.session.id, new_message=content
        ):
            if event.is_final_response():
                if event.content and event.content.parts:
                    raw_text = event.content.parts[0].text
                    sanitized_text = raw_text.encode("utf-8", "replace").decode("utf-8")
                    final_response_text = sanitized_text
                elif event.actions and event.actions.escalate:
                    final_response_text = self.error_message
                    await self.reset_session(session_id=self.session.id)
                break

        return final_response_text
