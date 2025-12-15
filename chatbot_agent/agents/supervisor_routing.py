from __future__ import annotations

import re
from typing import Optional

ROUTING_FALLBACK_MESSAGE = (
    "متوجه سوال شما نشدم.\n"
    "می‌توانید درباره آزمایش‌ها، علائم حیاتی، داروها، "
    "سابقه پزشکی یا پروفایل خود سوال بپرسید."
)

_LABS_KEYWORDS = [
    "آزمایش",
    "lab",
    "hba1c",
    "ldl",
    "hdl",
    "tsh",
    "cbc",
    "تری",
    "کلسترول",
    "na",
    "k",
    "creat",
]
_MEDICATION_KEYWORDS = [
    "دارو",
    "داروی",
    "قرص",
    "کپسول",
    "دوز",
    "مصرف",
    "انسولین",
    "متفورمین",
    "داروی جدید",
]
_VITALS_KEYWORDS = [
    "فشار",
    "قند",
    "قند خون",
    "sugar",
    "bp",
    "blood pressure",
    "وزن",
    "کیلو",
    "bmi",
    "اندازه گیری",
    "ثبت",
]
_HISTORY_KEYWORDS = [
    "سابقه",
    "تاریخچه",
    "خانواده",
    "ژنتیک",
    "family",
    "سبک",
    "زندگی",
    "ورزش",
    "تغذیه",
    "سیگار",
    "الکل",
    "دخانیات",
]
_PROFILE_KEYWORDS = [
    "پروفایل",
    "اطلاعات",
    "مشخصات",
    "سن",
    "سالگی",
    "قد",
    "جنسیت",
    "نام",
]

_NUMERIC_PATTERN = re.compile(r"\d+")


def route_for_query(query: str) -> Optional[str]:
    """
    Deterministically map the incoming question to a worker domain.
    """
    normalized = (query or "").strip().lower()
    if not normalized:
        return None

    if _contains(normalized, _LABS_KEYWORDS):
        return "labs"

    if _contains(normalized, _MEDICATION_KEYWORDS):
        return "medication"

    if _is_vitals_request(normalized):
        return "vitals"

    if _contains(normalized, _HISTORY_KEYWORDS):
        return "history"

    if _contains(normalized, _PROFILE_KEYWORDS):
        return "profile"

    return None


def _contains(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def _is_vitals_request(text: str) -> bool:
    if _contains(text, _VITALS_KEYWORDS):
        return True
    has_numbers = bool(_NUMERIC_PATTERN.search(text))
    return has_numbers and any(token in text for token in ["bp", "mmhg", "mg/dl", "kg"])
