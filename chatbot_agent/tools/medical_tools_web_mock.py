from datetime import date
from typing import Optional


def get_user_profile_summary() -> str:
    return (
        "نام: کاربر نمونه\n"
        "تاریخ تولد: 1988-05-12\n"
        "جنسیت: مرد\n"
        "وضعیت تأهل: متأهل\n"
        "قد: 175 سانتی‌متر"
    )


def get_medical_history_summary(include_family: Optional[bool] = None) -> str:
    lines = [
        "سابقه پزشکی خود کاربر:",
        "- دیابت نوع ۲ (شروع علائم در سن ۴۰ سال)",
    ]
    if include_family or include_family is None:
        lines += [
            "",
            "سابقه پزشکی خانواده:",
            "- پدر: فشار خون بالا",
            "- مادر: دیابت نوع ۲",
        ]
    return "\n".join(lines)


def get_lifestyle_summary(
    include_diet: Optional[bool] = None,
    include_activity: Optional[bool] = None,
    include_consumption: Optional[bool] = None,
) -> str:
    return (
        "فعالیت بدنی:\n"
        "- ورزش متوسط بین ۱ تا ۳ ساعت در هفته\n\n"
        "عادات تغذیه‌ای:\n"
        "- مصرف میوه: ۱ تا ۳ بار در روز\n"
        "- مصرف غذای آماده: ۱ تا ۳ بار در هفته\n\n"
        "مصرف دخانیات و الکل:\n"
        "- وضعیت سیگار: مصرف نمی‌کند"
    )


def get_weight_trend(limit: Optional[int] = None) -> str:
    return (
        "آخرین وزن ثبت‌شده در تاریخ 2025-01-10: 82 کیلوگرم.\n"
        "این داده 2 روز پیش ثبت شده است.\n"
        "روند اخیر: 1 کیلوگرم کاهش نسبت به 2025-01-01.\n"
        "تصویر کلی (5 اندازه‌گیری اخیر): 3 کیلوگرم کاهش.\n"
        "تاریخچهٔ اخیر:\n"
        "- 2025-01-10: 82 کیلوگرم\n"
        "- 2025-01-01: 83 کیلوگرم\n"
        "- 2024-12-20: 85 کیلوگرم"
    )


def get_measurements(measure_type: str, limit: Optional[int] = None) -> str:
    if measure_type == "blood_sugar":
        return (
            "آخرین مقادیر قند خون:\n"
            "- تاریخ 2025-01-10 | مقدار 132 mg/dL | وضعیت: FBS (ناشتا)\n"
            "- تاریخ 2025-01-05 | مقدار 145 mg/dL | وضعیت: RBS (رندم)"
        )
    if measure_type == "blood_pressure":
        return (
            "آخرین مقادیر فشار خون:\n"
            "- تاریخ 2025-01-10 | 125/80 mmHg\n"
            "- تاریخ 2025-01-05 | 130/85 mmHg"
        )
    return "نوع اندازه‌گیری نامعتبر است."


def get_labs(parameter_name: Optional[str] = None, limit: Optional[int] = None) -> str:
    if parameter_name:
        return (
            f"تحلیل نتایج پارامتر {parameter_name}:\n"
            "- HbA1c = 6.8 % (خارج از محدوده طبیعی)، تاریخ 2024-12-15"
        )
    return (
        "تحلیل آخرین آزمایش ثبت‌شده (2024-12-15):\n"
        "- HbA1c = 6.8 % (خارج از محدوده طبیعی)\n"
        "- LDL = 160 mg/dL (خارج از محدوده طبیعی)\n"
        "سایر پارامترها در محدوده طبیعی هستند."
    )


def get_medication_schedule(active_only: Optional[bool] = None) -> str:
    return (
        "داروهای فعال کاربر:\n"
        "- متفورمین | شروع: 2023-01-01 | ادامه‌دار | دوز: 500mg دوبار در روز\n"
        "- آتورواستاتین | شروع: 2024-06-01 | ادامه‌دار | دوز: 20mg شب‌ها"
    )


def add_weight_measurement(value: float, measurement_date: Optional[str] = None) -> str:
    d = measurement_date or date.today().isoformat()
    return f"(Mock) وزن {value} کیلوگرم در تاریخ {d} ثبت شد."


def add_blood_pressure_measurement(
    systolic: float,
    diastolic: float,
    measurement_date: Optional[str] = None,
) -> str:
    d = measurement_date or date.today().isoformat()
    return f"(Mock) فشار خون {systolic}/{diastolic} در تاریخ {d} ثبت شد."


def add_blood_sugar_measurement(
    value: float,
    state: Optional[str] = None,
    measurement_date: Optional[str] = None,
) -> str:
    d = measurement_date or date.today().isoformat()
    s = state or "نامشخص"
    return f"(Mock) قند خون {value} با وضعیت {s} در تاریخ {d} ثبت شد."
