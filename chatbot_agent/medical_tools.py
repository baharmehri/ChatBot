from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

from django.conf import settings


def _data_path() -> Path:
    override_path = getattr(settings, "USER_MEDICAL_DATA_PATH", None)
    if override_path:
        return Path(override_path)
    return Path(settings.BASE_DIR) / "user_test_data.json"


@lru_cache(maxsize=1)
def _load_data() -> Dict:
    path = _data_path()
    if not path.exists():
        raise FileNotFoundError(
            f"Medical data file '{path}' not found. "
            f"Set USER_MEDICAL_DATA_PATH in settings if the file is stored elsewhere."
        )
    with path.open(encoding="utf-8") as fp:
        return json.load(fp)


def get_user_profile_summary() -> str:
    """
    خلاصه‌ای از اطلاعات هویتی و وضعیت جسمی (قد، وزن، شاخص BMI تقریبی) کاربر را برمی‌گرداند.
    """
    data = _load_data()
    user = data.get("user", {})
    body = data.get("body", {})

    height_cm = body.get("height_cm")
    weight_kg = body.get("weight_kg")
    bmi = None
    if height_cm and weight_kg:
        bmi = round(weight_kg / ((height_cm / 100) ** 2), 1)

    return (
        f"نام: {user.get('first_name', 'نامشخص')} {user.get('last_name', '')}\n"
        f"تاریخ تولد: {user.get('dob', 'نامشخص')}\n"
        f"جنسیت: {user.get('sex', 'نامشخص')}\n"
        f"وضعیت تأهل: {user.get('marital_status', 'نامشخص')}\n"
        f"قد: {height_cm or 'نامشخص'} سانتی‌متر\n"
        f"وزن: {weight_kg or 'نامشخص'} کیلوگرم\n"
        f"BMI تقریبی: {bmi if bmi else 'نامشخص'}"
    )


def get_measurements(measure_type: str, limit: Optional[int]) -> str:
    """
    سوابق اندازه‌گیری فشارخون یا قند خون را با جزئیات تاریخ و وضعیت اندازه‌گیری می‌دهد.
    measure_type یکی از 'blood_sugar' یا 'blood_pressure' باشد.
    """
    data = _load_data()
    body = data.get("body", {})
    measure_type = (measure_type or "").lower()
    limit = limit if limit is not None else 5
    limit = max(1, min(limit, 20))

    if measure_type in ("blood_sugar", "sugar", "blood sugar"):
        records = body.get("blood suger", [])
        if not records:
            return "رکوردی برای قند خون موجود نیست."
        lines = ["آخرین مقادیر قند خون:"]
        for entry in records[:limit]:
            state = entry.get("state", "نامشخص")
            lines.append(
                f"- تاریخ {entry.get('date', 'نامشخص')} | مقدار {entry.get('value', 'نامشخص')} mg/dL | وضعیت: {state}"
            )
        return "\n".join(lines)

    if measure_type in ("blood_pressure", "pressure", "bp"):
        records = body.get("blood pressure", [])
        if not records:
            return "رکوردی برای فشار خون موجود نیست."
        lines = ["آخرین مقادیر فشار خون:"]
        for entry in records[:limit]:
            lines.append(
                f"- تاریخ {entry.get('date', 'نامشخص')} | "
                f"{entry.get('systolic', '؟')}/{entry.get('diastolic', '؟')} mmHg"
            )
        return "\n".join(lines)

    return "نوع اندازه‌گیری نامعتبر است. از 'blood_sugar' یا 'blood_pressure' استفاده کنید."


def get_lab_results(parameter_name: str, limit: Optional[int]) -> str:
    """
    نتایج آزمایش بر اساس نام پارامتر (مثلاً HbA1c، Na، LDL) را جستجو و به صورت فهرست برمی‌گرداند.
    """
    if not parameter_name:
        return "لطفاً نام پارامتر آزمایش را وارد کنید."

    data = _load_data()
    labs = data.get("labs", [])
    limit = limit if limit is not None else 5
    limit = max(1, min(limit, 10))
    key = parameter_name.lower()

    matches: List[str] = []
    for lab in labs:
        for param in lab.get("parameters", []):
            name = (param.get("name") or "").lower()
            if key in name:
                matches.append(
                    f"- تاریخ {lab.get('occurred_at', 'نامشخص')} | "
                    f"{param.get('name', 'پارامتر')} = {param.get('value', '؟')} {param.get('unit', '')}"
                )
                if len(matches) >= limit:
                    break
        if len(matches) >= limit:
            break

    if not matches:
        return "آزمایشی با این نام پارامتر پیدا نشد."

    return "نتایج آزمایش موردنظر:\n" + "\n".join(matches)


def get_medication_schedule(active_only: Optional[bool]) -> str:
    """
    فهرست داروهای مصرفی کاربر را (در صورت نیاز فقط داروهای فعال) با جزئیات دوره مصرف و دوز ارائه می‌کند.
    """
    data = _load_data()
    meds = data.get("medications", [])
    if active_only is None:
        active_only = True

    if not meds:
        return "اطلاعاتی درباره داروها ثبت نشده است."

    lines: List[str] = []
    for med in meds:
        end_date = med.get("usage_end_date")
        is_active = not end_date
        if active_only and not is_active:
            continue

        lines.append(
            f"- {med.get('generic_fa_name', med.get('generic_en_name', 'نامشخص'))} | "
            f"شروع: {med.get('usage_start', 'نامشخص')} "
            f"| پایان: {end_date or 'ادامه‌دار'} "
            f"| تکرار: هر {med.get('repetition_count', '?')} {med.get('repetition_period', '')} "
            f"| دوز: {med.get('quantity', '?')}"
        )

    if not lines:
        return "داروی فعالی ثبت نشده است."

    header = "داروهای فعال کاربر:" if active_only else "همه داروهای ثبت‌شده:"
    return "\n".join([header, *lines])
