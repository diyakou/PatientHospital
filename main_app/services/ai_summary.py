# -*- coding: utf-8 -*-
"""
AI Summary Service for patient profiles using gpt4free (g4f).

- ریس موازی بین مدل‌ها + سقف زمان سفت (۸s هر تلاش / ۱۵s کل)
- لاگینگ مرحله‌ای شبیه اسکریپت خبری
- آماده‌سازی کوکی‌ها پیش از فراخوانی
- پرامپت بهینه (۳ رکورد آخر علائم حیاتی)
- فال‌بک محلی اگر AI در ددلاین پاسخ نداد

Usage (Django):
    from .services.ai_summary import generate_patient_summary
    summary_text, error_message = generate_patient_summary(patient, vital_signs_iterable)

Notes:
- خروجی صرفاً برای کمک به تیم درمان است و جایگزین تصمیم پزشک نیست.
"""

from __future__ import annotations

from typing import Iterable, Optional, Tuple, List
import logging
import time
import os
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED, TimeoutError as FutureTimeout

logger = logging.getLogger("ai_summary")

# --- g4f optional import ---
try:
    from g4f.client import Client
    from g4f.cookies import set_cookies_dir, read_cookie_files
    from g4f.Provider import OpenaiChat
    # در صورت نیاز می‌توانید Provider خاص هم ایمپورت کنید:
    # from g4f.Provider import OpenaiChat
except Exception:  # pragma: no cover
    Client = None  # type: ignore

# ----------------------------
# Helpers
# ----------------------------

def _safe(v) -> str:
    return "" if v is None else str(v)

def _format_vital_signs(vital_signs: Iterable) -> str:
    """
    آخرین 3 رکورد علائم حیاتی را به متن فشرده فارسی تبدیل می‌کند.
    انتظار می‌رود هر آیتم ویژگی‌های:
    date, blood_pressure_systolic, blood_pressure_diastolic, heart_rate, blood_sugar, body_temperature
    را داشته باشد.
    """
    rows: List[str] = []
    count = 0
    for vs in vital_signs:
        rows.append(
            f"- تاریخ: {_safe(getattr(vs, 'date', ''))} | فشار خون: "
            f"{_safe(getattr(vs, 'blood_pressure_systolic', ''))}/"
            f"{_safe(getattr(vs, 'blood_pressure_diastolic', ''))} | "
            f"ضربان قلب: {_safe(getattr(vs, 'heart_rate', ''))} | "
            f"قند خون: {_safe(getattr(vs, 'blood_sugar', ''))} | "
            f"دمای بدن: {_safe(getattr(vs, 'body_temperature', ''))}"
        )
        count += 1
        if count >= 3:  # برای کاهش توکن و سرعت بهتر
            break
    return "\n".join(rows) if rows else "داده‌ای برای علائم حیاتی ثبت نشده است."

def _build_user_prompt(patient, vital_signs: Iterable) -> str:
    """
    ساخت پرامپت فارسی برای تولید خلاصه بالینی ایمن و عملیاتی.
    """
    first_name = _safe(getattr(patient, "first_name", ""))
    last_name = _safe(getattr(patient, "last_name", ""))
    age = _safe(getattr(patient, "age", ""))
    reason = _safe(getattr(patient, "reason", ""))
    meds = _safe(getattr(patient, "medications", ""))
    emergency = getattr(patient, "emergency", False)

    vitals_text = _format_vital_signs(vital_signs)

    return f"""
اطلاعات پایه بیمار:
- نام: {first_name} {last_name}
- سن: {age}
- دلیل مراجعه/بیماری: {reason}
- اورژانسی: {"بله" if emergency else "خیر"}
- داروهای فعلی/تجویزی: {meds or "ذکر نشده"}

خلاصه علائم حیاتی اخیر:
{vitals_text}

دستورالعمل:
- لطفاً یک خلاصه بالینی کوتاه و ساختاریافته (تقریباً ۱۲۰ تا ۱۸۰ کلمه) به زبان فارسی ارائه کن.
- نقش شما «پزشک‌یار هوش مصنوعی» است؛ بر ایمنی، وضوح، و اقدامات بعدی تاکید کن.
- اگر داده کم است، محدودیت‌ها را شفاف بگو.
- ساختار خروجی شامل این بخش‌ها باشد:
  1) خلاصه وضعیت
  2) نکات مثبت/منفی بالینی
  3) پیشنهاد اقدامات بعدی (غیردستور پزشکی قطعی)
  4) هشدار و سلب مسئولیت (این متن جایگزین تصمیم پزشک نیست)
""".strip()

def _system_prompt() -> str:
    return (
        "شما یک «پزشک‌یار هوش مصنوعی» هستید. هدف: کمک به تیم درمان با خلاصه‌سازی دقیق، ایمن، و منسجم."
        " از ادبیات حرفه‌ای اما قابل‌فهم برای تیم درمان استفاده کنید. از ارائه تشخیص قطعی یا تجویز مستقیم خودداری کنید."
        " در صورت کمبود داده، آن را مطرح کرده و پیشنهاد جمع‌آوری داده بیشتر بدهید."
    )

# ----------------------------
# Local fallback summary (rule-based)
# ----------------------------

def _local_fallback_summary(patient, vital_signs: Iterable) -> str:
    """
    خلاصه محلی (Rule-based) در صورت عدم دسترسی/تاخیر AI.
    """
    try:
        vs_list = list(vital_signs)
    except Exception:
        vs_list = []
    latest = vs_list[0] if vs_list else None

    first_name = _safe(getattr(patient, "first_name", ""))
    last_name = _safe(getattr(patient, "last_name", ""))
    age = _safe(getattr(patient, "age", ""))
    reason = _safe(getattr(patient, "reason", ""))
    meds = _safe(getattr(patient, "medications", ""))
    emergency = getattr(patient, "emergency", False)

    date = _safe(getattr(latest, "date", "")) if latest else ""
    sys_bp = getattr(latest, "blood_pressure_systolic", None) if latest else None
    dia_bp = getattr(latest, "blood_pressure_diastolic", None) if latest else None
    hr = getattr(latest, "heart_rate", None) if latest else None
    sugar = getattr(latest, "blood_sugar", None) if latest else None
    temp = getattr(latest, "body_temperature", None) if latest else None

    flags = []
    try:
        if sys_bp is not None and dia_bp is not None:
            if sys_bp >= 130 or dia_bp >= 85:
                flags.append("احتمال فشار خون بالا")
            elif sys_bp >= 120 or dia_bp >= 80:
                flags.append("فشار خون در محدوده مرزی")
        if temp is not None:
            if temp >= 38:
                flags.append("احتمال تب")
            elif temp < 35:
                flags.append("احتمال افت دما")
        if hr is not None:
            if hr > 100:
                flags.append("احتمال تاکی‌کاردی")
            elif hr < 60:
                flags.append("احتمال برادی‌کاردی")
        if sugar is not None:
            try:
                age_int = int(age) if str(age).isdigit() else None
            except Exception:
                age_int = None
            if age_int is not None:
                if age_int <= 30 and sugar > 100:
                    flags.append("قند خون بالاتر از محدوده توصیه‌شده برای سن")
                elif 30 < age_int <= 40 and sugar > 108:
                    flags.append("قند خون بالاتر از محدوده توصیه‌شده برای سن")
                elif age_int > 40 and sugar > 160:
                    flags.append("قند خون بالاتر از محدوده توصیه‌شده برای سن")
    except Exception:
        pass

    flags_text = "، ".join(flags) if flags else "در داده‌های موجود نکته هشداردهنده واضح مشاهده نشد."

    vitals_text = (
        f"تاریخ: {date} | فشار خون: {sys_bp or '—'}/{dia_bp or '—'} | "
        f"ضربان قلب: {hr or '—'} | قند خون: {sugar or '—'} | دمای بدن: {temp or '—'}"
        if latest else "داده‌ای برای علائم حیاتی ثبت نشده است."
    )

    summary = (
        f"خلاصه وضعیت بیمار: {first_name} {last_name}، سن {age} سال، "
        f"دلیل مراجعه/بیماری: {reason or 'ذکر نشده'}. وضعیت اورژانسی: {'بله' if emergency else 'خیر'}. "
        f"داروهای فعلی: {meds or 'ذکر نشده'}.\n\n"
        f"آخرین علائم حیاتی:\n{vitals_text}\n\n"
        f"نکات بالینی: {flags_text}.\n"
        "پیشنهاد اقدامات بعدی: پایش مجدد علائم حیاتی، بررسی پرونده دارویی، تکمیل شرح حال و "
        "در صورت نیاز ارجاع به پزشک مربوطه. این متن صرفاً جهت کمک به تیم درمان است و جایگزین "
        "تصمیم پزشک نیست."
    )
    return summary

# ----------------------------
# Main entry
# ----------------------------

def generate_patient_summary(patient, vital_signs: Iterable) -> Tuple[Optional[str], Optional[str]]:
    """
    تولید خلاصه با g4f تحت ددلاین:
    - ریس موازی بین مدل‌ها (اولین پاسخ معتبر انتخاب می‌شود)
    - اگر در ددلاین پاسخی نیاید، فال‌بک محلی
    """
    # ددلاین‌ها مشابه اسکریپت خبری
    PER_ATTEMPT_TIMEOUT = 50       # هر تلاش g4f حداکثر 8s
    OVERALL_DEADLINE   = 30     # سقف کل عملیات 15s
    MODEL_CANDIDATES   = ["gpt-5"]  # اگر 4o در g4f شما نباشد، نادیده گرفته می‌شود

    logger.info("🔍 شروع تولید خلاصه | بیمار: %s %s",
                getattr(patient, "first_name", ""), getattr(patient, "last_name", ""))
    t_all = time.monotonic()

    if Client is None:
        logger.warning("⚠️ g4f Client در دسترس نیست → فال‌بک محلی")
        return (_local_fallback_summary(patient, vital_signs), None)

    try:
        # آماده‌سازی کوکی‌ها (الگوی اسکریپت خبری)
        cookies_dir = os.path.join(os.getcwd(), "har_and_cookies")
        try:
            set_cookies_dir(cookies_dir)
            read_cookie_files()
            logger.debug("🍪 cookies آماده شد: %s", cookies_dir)
        except Exception as e:
            logger.warning("🍪 آماده‌سازی کوکی‌ها ناموفق: %s", e)

        # ساخت پیام‌ها
        messages = [
            {"role": "system", "content": _system_prompt()},
            {"role": "user",  "content": _build_user_prompt(patient, vital_signs)},
        ]
        logger.debug("📨 prompt آماده شد: %s", messages[-1]["content"][:200])

        def _call_g4f_once(model: str):
            # Client تازه برای هر فراخوانی (برخی providerها thread-safe نیستند)
            c = Client()
            return c.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.2,
                max_tokens=600,
                provider=OpenaiChat,
                # اگر نسخه g4f شما پشتیبانی می‌کند، باز کنید:
                # timeout=PER_ATTEMPT_TIMEOUT,
                # request_timeout=PER_ATTEMPT_TIMEOUT,
            )

        content: Optional[str] = None

        # 1) ریس موازی بین مدل‌ها (اولین پاسخ برنده)
        logger.info("🏁 ریس موازی بین مدل‌ها: %s", ", ".join(MODEL_CANDIDATES))
        with ThreadPoolExecutor(max_workers=len(MODEL_CANDIDATES)) as pool:
            futures = [pool.submit(_call_g4f_once, m) for m in MODEL_CANDIDATES]
            done, pending = wait(
                futures,
                timeout=min(PER_ATTEMPT_TIMEOUT, OVERALL_DEADLINE),
                return_when=FIRST_COMPLETED
            )
            if not done:
                logger.warning("⏲️ timeout در ریسِ موازی (>%ss)", min(PER_ATTEMPT_TIMEOUT, OVERALL_DEADLINE))
            else:
                for f in done:
                    try:
                        resp = f.result(timeout=0.2)
                        if getattr(resp, "choices", None):
                            ch = resp.choices[0]
                            msg = getattr(ch, "message", None)
                            if msg and getattr(msg, "content", None):
                                content = (msg.content or "").strip()
                                logger.info("✅ پاسخ از ریس موازی دریافت شد")
                                for p in pending:
                                    p.cancel()
                                break
                    except Exception as e:
                        logger.exception("❌ خطا در future: %s", e)

        # 2) اگر هنوز پاسخی نداریم و زمان باقی است: یک تلاش ترتیبی کوتاه
        elapsed = time.monotonic() - t_all
        if not content and elapsed < OVERALL_DEADLINE:
            for m in MODEL_CANDIDATES:
                remaining = OVERALL_DEADLINE - (time.monotonic() - t_all)
                if remaining <= 0:
                    break
                logger.info("🧠 تلاش ترتیبی با %s (باقیمانده: %.1fs)", m, remaining)
                with ThreadPoolExecutor(max_workers=1) as pool:
                    fut = pool.submit(_call_g4f_once, m)
                    try:
                        resp = fut.result(timeout=min(PER_ATTEMPT_TIMEOUT, max(1.0, remaining)))
                        if getattr(resp, "choices", None):
                            ch = resp.choices[0]
                            msg = getattr(ch, "message", None)
                            if msg and getattr(msg, "content", None):
                                content = (msg.content or "").strip()
                                logger.info("✅ پاسخ از %s دریافت شد", m)
                                break
                    except FutureTimeout:
                        logger.error("⏱️ timeout در مدل %s", m)
                    except Exception as e:
                        logger.exception("❌ خطا در مدل %s: %s", m, e)

        if content:
            logger.debug("🧾 خلاصه نهایی (نمونه 300کاراکتر): %s", content[:300])
            logger.info("⏱️ تمام شد در %.2fs", time.monotonic() - t_all)
            return (content, None)

        logger.warning("⚠️ پاسخی از AI نیامد در %.2fs → فال‌بک محلی", time.monotonic() - t_all)
        return (_local_fallback_summary(patient, vital_signs), None)

    except Exception as e:
        logger.exception("💥 خطای کلی AI summary: %s", e)
        return (_local_fallback_summary(patient, vital_signs), None)
