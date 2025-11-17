from __future__ import annotations

import json
from datetime import date, datetime, timezone
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
WORKOUT_RATE_DESCRIPTIONS = {
    0: "ورزش متوسط کمتر از ۳ ساعت در هفته",
    1: "ورزش شدید کمتر از یک ساعت در هفته",
    2: "ورزش متوسط بین ۱ تا ۳ ساعت در هفته",
    3: "ورزش شدید بین ۱ تا ۳ ساعت در هفته",
    4: "فعالیت ورزشی نامنظم در طول روز",
    5: "بدون فعالیت ورزشی منظم",
    6: "فعالیت در سطح ورزشکار حرفه‌ای",
}

FRUIT_USAGE_DESCRIPTIONS = {
    0: "مصرف میوه کمتر از یک‌بار در هفته",
    1: "مصرف میوه ۱ تا ۴ بار در هفته",
    2: "مصرف میوه بیش از ۵ بار در هفته",
    3: "مصرف میوه ۱ تا ۳ بار در روز",
    4: "مصرف میوه بیش از ۳ بار در روز",
}

FOOD_USAGE_DESCRIPTIONS = {
    0: "کمتر از یک‌بار در ماه",
    1: "۱ تا ۳ بار در ماه",
    2: "۱ تا ۳ بار در هفته",
    3: "۴ تا ۶ بار در هفته",
    4: "۱ تا ۲ بار در روز",
    5: "بیش از ۳ بار در روز",
}

TOBACCO_ALCOHOL_STATUS = {
    "N": "مصرف نمی‌کند",
    "Y": "مصرف می‌کند",
    "L": "مصرف می‌کند",
    "S": "در گذشته مصرف می‌کرد",
    "W": "شش ماه گذشته مصرف نداشته است",
}

BLOOD_SUGAR_MEASURE_TIMES = [
    ("FBS", "ناشتا"),
    ("PBS", "دو ساعته بعد از صبحانه"),
    ("PLS", "دو ساعته بعد از ناهار"),
    ("PDS", "دو ساعته بعد از شام"),
    ("RBS", "رندم"),
]
_BLOOD_SUGAR_STATE_LABELS = {code: label for code, label in BLOOD_SUGAR_MEASURE_TIMES}


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


def _describe_lifestyle_value(value: Optional[int], descriptions: Dict[int, str]) -> str:
    if value is None:
        return "نامشخص"
    try:
        numeric_value = int(value)
    except (TypeError, ValueError):
        return "نامشخص"
    return descriptions.get(numeric_value, "نامشخص")


def _describe_tobacco_alcohol(code: Optional[str]) -> str:
    if not code:
        return "نامشخص"
    normalized = str(code).strip().upper()
    return TOBACCO_ALCOHOL_STATUS.get(normalized, "نامشخص")


def _is_positive_number(value: Optional[float]) -> bool:
    try:
        return float(value) > 0
    except (TypeError, ValueError):
        return False


def _format_number(value: Optional[float]) -> str:
    try:
        num = float(value)
    except (TypeError, ValueError):
        return "نامشخص"
    if num.is_integer():
        return str(int(num))
    return str(round(num, 1))


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


def _persist_data(data: Dict) -> None:
    """
    Persist the updated medical dataset and reset the cache so subsequent reads
    observe the latest data.
    """
    path = _data_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fp:
        json.dump(data, fp, ensure_ascii=False, indent=2)
    _load_data.cache_clear()


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


def get_lifestyle_summary(
    include_diet: Optional[bool] = None,
    include_activity: Optional[bool] = None,
    include_consumption: Optional[bool] = None,
) -> str:
    """
    خلاصه‌ای از عادات سبک زندگی کاربر (ورزش، تغذیه، مصرف دخانیات و الکل) را ارائه می‌دهد.
    """
    data = _load_data()
    lifestyle = data.get("life_style") or {}

    if not lifestyle:
        return "هیچ داده‌ای درباره سبک زندگی ثبت نشده است."

    include_activity = True if include_activity is None else bool(include_activity)
    include_diet = True if include_diet is None else bool(include_diet)
    include_consumption = True if include_consumption is None else bool(include_consumption)

    sections: List[str] = []

    if include_activity:
        workout_rate = lifestyle.get("workout_rate")
        workout_desc = _describe_lifestyle_value(workout_rate, WORKOUT_RATE_DESCRIPTIONS)
        activity_lines = ["فعالیت بدنی:"]
        if workout_desc == "نامشخص":
            activity_lines.append("- اطلاعاتی درباره سطح فعالیت بدنی ثبت نشده است.")
        else:
            activity_lines.append(f"- سطح تمرین: {workout_desc}")
        sections.append("\n".join(activity_lines))

    if include_diet:
        fruit_usage = lifestyle.get("fruit_usage")
        rice_usage = lifestyle.get("rice_usage")
        processed_food_usage = lifestyle.get("processed_food_usage")

        diet_lines = ["عادات تغذیه‌ای:"]
        diet_entries = []

        fruit_desc = _describe_lifestyle_value(fruit_usage, FRUIT_USAGE_DESCRIPTIONS)
        if fruit_desc != "نامشخص":
            diet_entries.append(f"- مصرف میوه: {fruit_desc}")

        rice_desc = _describe_lifestyle_value(rice_usage, FOOD_USAGE_DESCRIPTIONS)
        if rice_desc != "نامشخص":
            diet_entries.append(f"- مصرف برنج: {rice_desc}")

        processed_desc = _describe_lifestyle_value(processed_food_usage, FOOD_USAGE_DESCRIPTIONS)
        if processed_desc != "نامشخص":
            diet_entries.append(f"- مصرف غذای آماده/فست‌فود: {processed_desc}")

        if diet_entries:
            diet_lines.extend(diet_entries)
        else:
            diet_lines.append("- اطلاعات تغذیه‌ای ثبت نشده است.")
        sections.append("\n".join(diet_lines))

    if include_consumption:
        hookah_status = _describe_tobacco_alcohol(lifestyle.get("hookah_smoking"))
        smoking_status = _describe_tobacco_alcohol(lifestyle.get("smoking"))
        alcohol_status = _describe_tobacco_alcohol(lifestyle.get("alcohol_drink"))

        consumption_lines = ["مصرف دخانیات و الکل:"]
        entries: List[str] = []

        if hookah_status != "نامشخص":
            hookah_years = lifestyle.get("hookah_smoking_years")
            hookah_daily = lifestyle.get("hookah_smoking_count_a_day")
            details: List[str] = []
            if _is_positive_number(hookah_years):
                details.append(f"{_format_number(hookah_years)} سال سابقه")
            if _is_positive_number(hookah_daily):
                details.append(f"{_format_number(hookah_daily)} مرتبه در روز")
            if details:
                entries.append(f"- وضعیت قلیان: {hookah_status} ({'، '.join(details)})")
            else:
                entries.append(f"- وضعیت قلیان: {hookah_status}")

        if smoking_status != "نامشخص":
            smoking_years = lifestyle.get("smoking_years")
            smoking_daily = lifestyle.get("smoking_count_a_day")
            details = []
            if _is_positive_number(smoking_years):
                details.append(f"{_format_number(smoking_years)} سال سابقه")
            if _is_positive_number(smoking_daily):
                details.append(f"{_format_number(smoking_daily)} عدد در روز")
            if details:
                entries.append(f"- وضعیت سیگار: {smoking_status} ({'، '.join(details)})")
            else:
                entries.append(f"- وضعیت سیگار: {smoking_status}")

        if alcohol_status != "نامشخص":
            entries.append(f"- وضعیت مصرف الکل: {alcohol_status}")

        if entries:
            consumption_lines.extend(entries)
        else:
            consumption_lines.append("- اطلاعاتی درباره مصرف دخانیات یا الکل ثبت نشده است.")
        sections.append("\n".join(consumption_lines))

    sections = [section for section in sections if section]
    if not sections:
        return "هیچ داده‌ای درباره سبک زندگی ثبت نشده است."

    return "\n\n".join(sections)


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
            state = _describe_blood_sugar_state(entry.get("state"))
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


def add_blood_sugar_measurement(
    value: float,
    state: Optional[str] = None,
    measurement_date: Optional[str] = None,
) -> str:
    """
    رکورد جدید قند خون را به فایل داده کاربر اضافه می‌کند.
    - value: مقدار قند خون بر حسب mg/dL.
    - state: وضعیت اندازه‌گیری (یکی از FBS، PBS، PLS، PDS، RBS). اگر خالی باشد "نامشخص" ذخیره می‌شود.
    - measurement_date: تاریخ اندازه‌گیری به فرمت ISO. در صورت عدم ارسال، تاریخ امروز ذخیره می‌شود.
    """
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return "مقدار قند خون وارد شده نامعتبر است."
    if numeric_value <= 0:
        return "مقدار قند خون باید بزرگ‌تر از صفر باشد."

    stored_value = int(numeric_value) if numeric_value.is_integer() else round(numeric_value, 1)

    date_str = (measurement_date or "").strip()
    if date_str:
        parsed_date = _parse_ts_to_datetime(date_str)
        if parsed_date == datetime.min.replace(tzinfo=timezone.utc):
            return "تاریخ وارد شده نامعتبر است. لطفاً تاریخ را به‌صورت YYYY-MM-DD ارسال کنید."
        measurement_date_iso = parsed_date.date().isoformat()
    else:
        measurement_date_iso = date.today().isoformat()

    state_value = (state or "").strip()
    if not state_value:
        state_code = "نامشخص"
    else:
        normalized = state_value.upper()
        if normalized in _BLOOD_SUGAR_STATE_LABELS:
            state_code = normalized
        else:
            matching_code = next(
                (code for code, label in BLOOD_SUGAR_MEASURE_TIMES if label == state_value),
                None,
            )
            if matching_code:
                state_code = matching_code
            else:
                allowed = ", ".join(code for code, _ in BLOOD_SUGAR_MEASURE_TIMES)
                return f"وضعیت اندازه‌گیری نامعتبر است. مقادیر مجاز: {allowed}"

    data = _load_data()
    body = data.setdefault("body", {})
    records = body.get("blood suger")
    if not isinstance(records, list):
        records = []
        body["blood suger"] = records

    records.insert(
        0,
        {
            "date": measurement_date_iso,
            "value": stored_value,
            "state": state_code,
        },
    )

    _persist_data(data)
    state_text = _describe_blood_sugar_state(state_code)
    return (
        f"رکورد قند خون {stored_value} با وضعیت {state_text} "
        f"در تاریخ {measurement_date_iso} ذخیره شد."
    )


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


def _describe_blood_sugar_state(state: Optional[str]) -> str:
    if not state:
        return "نامشخص"
    normalized = str(state).strip().upper()
    label = _BLOOD_SUGAR_STATE_LABELS.get(normalized)
    if label:
        return f"{normalized} ({label})"
    return normalized or "نامشخص"


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
