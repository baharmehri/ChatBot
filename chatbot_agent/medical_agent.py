from __future__ import annotations

from google.adk.tools import FunctionTool

from chatbot_agent.base_agent import BaseAgent
from chatbot_agent.medical_tools import (
    get_lab_results,
    get_measurements,
    get_medication_schedule,
    get_user_profile_summary,
)

MEDICAL_AGENT_PROMPT = """
تو یک همراه پزشکی فارسی زبان هستی که باید صرفاً بر اساس داده‌های ثبت شده پاسخ بدهی.
- برای دریافت خلاصه اطلاعات هویتی از ابزار get_user_profile_summary استفاده کن.
- برای قند یا فشار خون از get_measurements استفاده کن؛ مقدار measure_type را روی یکی از blood_sugar یا blood_pressure بگذار و اگر مطمئن نیستی limit را 5 در نظر بگیر.
- برای یافتن نتایج آزمایش از get_lab_results با نام پارامتر (مثلاً HbA1c) استفاده کن و limit را مشخص کن (در صورت شک 5).
- برای فهرست داروها از get_medication_schedule استفاده کن و مقدار active_only را True یا False تعیین کن.
- همه پاسخ‌ها را به فارسی بنویس و از لحن محترمانه استفاده کن.
- قبل از نتیجه‌گیری حتماً دادهٔ مربوطه را با استفاده از ابزار مناسب بازیابی کن.
- اگر داده‌ای وجود ندارد یا نامشخص است، واضح بگو و حدس نزن.
- در صورت اشاره به مقادیر، واحد و تاریخ اندازه‌گیری را ذکر کن.
- یادآوری کن که این گفتگو جایگزین ویزیت پزشک نیست و کاربر باید در موارد اضطراری به پزشک مراجعه کند.
"""


class PersianMedicalAgent(BaseAgent):
    """
    Medical chatbot specialized for answering Persian queries using structured user data.
    """

    def __init__(self, user_id: str):
        tools = [
            FunctionTool(get_user_profile_summary),
            FunctionTool(get_measurements),
            FunctionTool(get_lab_results),
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


# Example usage:
# agent = await PersianMedicalAgent.create(user_id="123", session_id="conv-1")
# answer = await agent.call_agent_async("آخرین نتایج قند خونم را بگو")
