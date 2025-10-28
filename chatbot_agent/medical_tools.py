from __future__ import annotations

import json
from datetime import datetime, timezone
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


def _parse_ts_to_datetime(value: Optional[str]) -> datetime:
    """تبدیل امن رشتهٔ تاریخ به datetime با پشتیبانی از ISO و timezone"""
    if not value:
        return datetime.min.replace(tzinfo=timezone.utc)
    normalized = value.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(normalized)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        try:
            d = datetime.strptime(normalized.split("T")[0], "%Y-%m-%d")
            return d.replace(tzinfo=timezone.utc)
        except ValueError:
            return datetime.min.replace(tzinfo=timezone.utc)


def get_labs(parameter_name: Optional[str], limit: Optional[int]) -> str:
    """
    تحلیل آخرین آزمایش کاربر.
    - اگر پارامتر خاصی مشخص نشده باشد، فقط آخرین آزمایش تحلیل می‌شود.
    - فقط پارامترهای غیرطبیعی (tag=2) یا نیازمند تفسیر (tag=0) نمایش داده می‌شوند.
    - اگر آزمایش مربوط به بیش از ۳۰ روز قبل باشد، فقط اطلاع‌رسانی انجام می‌شود.
    """
    data = _load_data()
    labs = data.get("labs", [])
    if not labs:
        return "هیچ آزمایش ثبت نشده است."

    # مرتب‌سازی آزمایش‌ها بر اساس تاریخ
    sorted_labs = sorted(labs, key=lambda lab: _parse_ts_to_datetime(lab.get("occurred_at")), reverse=True)
    latest_lab = sorted_labs[0]
    latest_lab_dt = _parse_ts_to_datetime(latest_lab.get("occurred_at"))

    # فاصله زمانی از امروز
    days_diff = (datetime.now(timezone.utc).date() - latest_lab_dt.date()).days
    info_note = ""
    if days_diff > 30:
        info_note = "توجه: این نتایج مربوط به آزمایش قبلی هستند و ممکن است وضعیت فعلی شما را به‌طور کامل نشان ندهند.\n\n"

    status_map = {
        2: "خارج از محدوده طبیعی گزارش شده است",
        1: "در محدوده طبیعی است",
        0: "وضعیت آزمایش نامشخص است",
    }

    search_key = (parameter_name or "").strip().lower() or None

    # حالت ۱: تحلیل کامل آخرین آزمایش
    if not search_key:
        occurred_at = latest_lab.get("occurred_at", "نامشخص")
        source = latest_lab.get("source", "نامشخص")
        params = latest_lab.get("parameters", [])

        if not params:
            return "هیچ پارامتری در آخرین آزمایش یافت نشد."

        abnormal = [p for p in params if p.get("tag") in (0, 2)]
        normal = [p for p in params if p.get("tag") == 1]

        lines: List[str] = [info_note + f"تحلیل آخرین آزمایش ثبت‌شده ({occurred_at}، منبع: {source}):"]

        if abnormal:
            lines.append("پارامترهای غیرطبیعی یا نیازمند تفسیر:")
            for p in abnormal:
                name = p.get("name", "پارامتر")
                val = p.get("value")
                unit = p.get("unit") or ""
                tag = p.get("tag")
                val_text = "نامشخص" if val is None else str(val)
                lines.append(f"- {name} = {val_text}{(' ' + unit) if unit else ''} ({status_map[tag]})")

        if abnormal and normal:
            lines.append("سایر پارامترهای این آزمایش در محدوده طبیعی بوده و جای نگرانی نیست.")
        elif not abnormal and normal:
            lines.append("تمام پارامترهای این آزمایش در محدوده طبیعی هستند.")
        elif not abnormal and not normal:
            lines.append("هیچ پارامتر قابل تفسیر در این آزمایش وجود ندارد.")

        return "\n".join(lines)

    # حالت ۲: اگر کاربر پارامتر خاصی خواسته باشد (مثلاً HbA1c)
    limit = limit if limit is not None else 3
    limit = max(1, min(limit, 5))

    results = []
    count_abnormal = 0

    for lab in sorted_labs:
        params = lab.get("parameters", [])
        filtered = [p for p in params if search_key in (p.get("name") or "").lower()]
        if not filtered:
            continue

        occurred_at = lab.get("occurred_at", "نامشخص")
        source = lab.get("source", "نامشخص")

        for p in filtered:
            name = p.get("name", "پارامتر")
            val = p.get("value")
            unit = p.get("unit") or ""
            tag = p.get("tag")
            val_text = "نامشخص" if val is None else str(val)
            results.append(
                f"- {name} = {val_text}{(' ' + unit) if unit else ''} ({status_map[tag]})، تاریخ {occurred_at}")
            if tag in (0, 2):
                count_abnormal += 1

        if len(results) >= limit:
            break

    if not results:
        return f"آزمایشی برای پارامتر {parameter_name} پیدا نشد."

    summary = f"تحلیل نتایج پارامتر {parameter_name}:\n\n" + "\n".join(results)
    if count_abnormal:
        summary += f"\n\nدر مجموع {count_abnormal} مورد غیرطبیعی یا نیازمند تفسیر مشاهده شد."
    return info_note + summary


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
