from __future__ import annotations

import json
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

from django.conf import settings

_DISEASE_LABELS = {
    "DIABETES_TYPE_2": "دیابت نوع ۲",
    "DYSLIPIDEMIA_DISEASE": "دیس‌لیپیدمی",
}

_RELATION_LABELS = {
    "mother": "مادر",
    "father": "پدر",
    "brother": "برادر",
    "sister": "خواهر",
    "grandmother": "مادربزرگ",
    "grandfather": "پدربزرگ",
    "son": "پسر",
    "daughter": "دختر",
    "wife": "همسر",
    "husband": "همسر",
}


def _translate_disease(code: Optional[str]) -> str:
    if not code:
        return "نامشخص"
    normalized = code.strip()
    return _DISEASE_LABELS.get(normalized, normalized.replace("_", " ").title())


def _translate_relation(code: Optional[str]) -> str:
    if not code:
        return "نسبت نامشخص"
    key = code.strip().lower()
    return _RELATION_LABELS.get(key, code)


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
    خلاصه‌ای از اطلاعات هویتی و قد کاربر را برمی‌گرداند.
    """
    data = _load_data()
    user = data.get("user", {})
    body = data.get("body", {})

    height_cm = body.get("height_cm")

    return (
        f"نام: {user.get('first_name', 'نامشخص')} {user.get('last_name', '')}\n"
        f"تاریخ تولد: {user.get('dob', 'نامشخص')}\n"
        f"جنسیت: {user.get('sex', 'نامشخص')}\n"
        f"وضعیت تأهل: {user.get('marital_status', 'نامشخص')}\n"
        f"قد: {height_cm or 'نامشخص'} سانتی‌متر"
    )


def get_medical_history_summary(include_family: Optional[bool] = None) -> str:
    """
    خلاصه‌ای از سابقه پزشکی کاربر و خانواده را ارائه می‌دهد.
    """
    data = _load_data()
    personal_history = data.get("brief_medical_history") or []
    family_history = data.get("family_brief_medical_history") or []

    include_family = True if include_family is None else bool(include_family)

    sections: List[str] = []

    if personal_history:
        lines = ["سابقه پزشکی خود کاربر:"]
        for item in personal_history:
            disease = _translate_disease(item.get("diseaseType"))
            age = item.get("age")
            if isinstance(age, (int, float)):
                age_text = f"شروع علائم در سن {int(age)} سال"
            else:
                age_text = "سن شروع مشخص نشده است"
            lines.append(f"- {disease} ({age_text})")
        sections.append("\n".join(lines))
    else:
        sections.append("سابقه پزشکی برای خود کاربر ثبت نشده است.")

    if include_family:
        if family_history:
            lines = ["سابقه پزشکی خانواده:"]
            for item in family_history:
                disease = _translate_disease(item.get("diseaseType"))
                relation = _translate_relation(item.get("relation"))
                lines.append(f"- {relation}: {disease}")
            sections.append("\n".join(lines))
        else:
            sections.append("سابقه پزشکی خانوادگی ثبت نشده است.")

    filtered_sections = [section for section in sections if section]
    if not filtered_sections:
        return "هیچ سابقه پزشکی ثبت نشده است."

    return "\n\n".join(filtered_sections)


def get_weight_trend(limit: Optional[int] = None) -> str:
    """
    آخرین وضعیت وزن کاربر را همراه با روند تغییرات اخیر گزارش می‌کند.
    """
    data = _load_data()
    body = data.get("body", {})
    weight_entries = body.get("weight_kg")

    if not isinstance(weight_entries, list) or not weight_entries:
        return "هیچ داده‌ای برای وزن ثبت نشده است."

    valid_entries = []
    for entry in weight_entries:
        dt = _parse_ts_to_datetime(entry.get("date"))
        value = entry.get("value")
        if dt == datetime.min.replace(tzinfo=timezone.utc):
            continue
        valid_entries.append(
            {
                "date": entry.get("date", "نامشخص"),
                "value": value,
                "dt": dt,
            }
        )

    if not valid_entries:
        return "هیچ داده معتبر برای وزن پیدا نشد."

    sorted_entries = sorted(valid_entries, key=lambda item: item["dt"], reverse=True)

    limit = limit if limit is not None else 5
    limit = max(1, min(limit, 20))
    recent_entries = sorted_entries[:limit]

    latest = recent_entries[0]
    latest_value = latest.get("value")
    latest_date = latest.get("date")
    latest_dt = latest.get("dt")

    latest_value_text = f"{latest_value} کیلوگرم" if isinstance(latest_value, (int, float)) else "نامشخص"
    days_since = (datetime.now(timezone.utc).date() - latest_dt.date()).days
    recency_note = ""
    if days_since > 5:
        recency_note = (
            "آخرین داده مربوط به بیش از ۵ روز پیش است. لطفاً دادهٔ جدیدی ثبت کنید تا تحلیل دقیق‌تر امکان‌پذیر باشد.\n\n"
        )

    lines: List[str] = [
        f"آخرین وزن ثبت‌شده در تاریخ {latest_date}: {latest_value_text}.",
        f"این داده {days_since} روز پیش ثبت شده است." if days_since >= 0 else "",
    ]
    lines = [line for line in lines if line]

    if len(recent_entries) > 1:
        prev = recent_entries[1]
        prev_value = prev.get("value")
        prev_date = prev.get("date")
        if isinstance(latest_value, (int, float)) and isinstance(prev_value, (int, float)):
            diff = latest_value - prev_value
            diff_abs = round(abs(diff), 1)
            if diff > 0:
                change_text = f"{diff_abs} کیلوگرم افزایش نسبت به {prev_date}"
            elif diff < 0:
                change_text = f"{diff_abs} کیلوگرم کاهش نسبت به {prev_date}"
            else:
                change_text = f"تغییری نسبت به {prev_date} نداشته‌اید"
            lines.append(f"روند اخیر: {change_text}.")

    if len(recent_entries) > 1:
        oldest = recent_entries[-1]
        oldest_value = oldest.get("value")
        oldest_date = oldest.get("date")
        if isinstance(latest_value, (int, float)) and isinstance(oldest_value, (int, float)):
            overall_diff = latest_value - oldest_value
            overall_diff_abs = round(abs(overall_diff), 1)
            if overall_diff > 0:
                trend_text = f"{overall_diff_abs} کیلوگرم افزایش نسبت به {oldest_date}"
            elif overall_diff < 0:
                trend_text = f"{overall_diff_abs} کیلوگرم کاهش نسبت به {oldest_date}"
            else:
                trend_text = f"تغییری نسبت به {oldest_date} نداشته‌اید"
            lines.append(f"تصویر کلی ({len(recent_entries)} اندازه‌گیری اخیر): {trend_text}.")

    history_lines = []
    for item in recent_entries:
        value = item.get("value")
        value_text = f"{value} کیلوگرم" if isinstance(value, (int, float)) else "نامشخص"
        history_lines.append(f"- {item.get('date')}: {value_text}")

    lines.append("تاریخچهٔ اخیر:")
    lines.extend(history_lines)

    return recency_note + "\n".join(lines)


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
