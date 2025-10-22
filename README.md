# سیستم مدیریت بیمارستان (Django) — رابط مدرن RTL + پزشک‌یار هوش مصنوعی

سامانه تحت وب برای مدیریت بیمارستان با نقش‌های پزشک و پرستار، مدیریت بیماران، ثبت علائم حیاتی، نمودارهای تعاملی، خروجی/ورودی اکسل و «پزشک‌یار هوش مصنوعی» با بارگذاری سریع، لودینگ حرفه‌ای، و لاگ مرحله‌ای در کنسول مرورگر.

[hospital_project/settings.py](hospital_project/settings.py) · [main_app/urls.py](main_app/urls.py) · [main_app/views.py](main_app/views.py) · [main_app/services/ai_summary.py](main_app/services/ai_summary.py) · [main_app/templates/base.html](main_app/templates/base.html)

---

## امکانات کلیدی

- احراز هویت و نقش‌بنیاد:
  - ورود و ثبت‌نام کاربران با نقش‌های «پرستار» و «پزشک»
  - هدایت خودکار به داشبورد نقش مربوطه
- مدیریت بیمار:
  - افزودن، ویرایش، حذف و مشاهده جزئیات بیمار
  - ثبت علائم حیاتی توسط پرستار و نمایش تاریخچه
- نمودارهای علائم حیاتی:
  - نمایش روند علائم حیاتی با Chart.js
  - تزریق ایمن داده‌ها با json_script برای جلوگیری از خطاهای JS
- پزشک‌یار هوش مصنوعی (AI Assistant):
  - تولید خلاصه بالینی هوشمند به زبان فارسی با استفاده از gpt4free (g4f)
  - بارگذاری غیرهمگام (Async) برای خلاصه AI؛ UI بلاک نمی‌شود و صفحه سریع‌تر لود می‌شود
  - لودینگ حرفه‌ای شامل اسپینر و Skeleton Loader
  - لاگ مرحله‌ای کامل در کنسول مرورگر (INIT، REQUEST_SENT، RESPONSE_RECEIVED، JSON_PARSED، RETRY_SCHEDULED، RENDERED، FAILED)
  - در صورت عدم دسترسی به سرویس، خلاصه محلی مبتنی بر قواعد ارائه می‌شود (Rule‑based Fallback)
- خروجی و ورودی اکسل:
  - خروجی اکسل از داده‌های بیمار
  - آپلود اکسل برای ثبت/به‌روزرسانی علائم حیاتی
- رابط کاربری مدرن و RTL:
  - طراحی مبتنی بر Tailwind (CDN) با راست‌چین کامل
  - الگوهای قابل‌دسترسی (aria، ESC، کلیک بیرون) و پیام‌های سیستمی زیبا
- بهینه‌سازی عملکرد:
  - محدودسازی هوشمند رکوردها برای رندر سریع جدول و نمودار
  - دریافت خلاصه AI از اندپوینت سبک JSON پس از بارگذاری صفحه

---

## تصاویر رابط کاربری

- داشبورد پرستار:
  - ![Nurse Dashboard](screenshots/Screenshot%202025-10-22%20132658.png)
- صفحه جزئیات بیمار (پرستار) با خلاصه AI و نمودار:
  - ![Patient Detail](screenshots/Screenshot%202025-10-22%20135209.png)

فایل‌های مرتبط:
- [main_app/templates/main_app/nurse/nurse_dashboard.html](main_app/templates/main_app/nurse/nurse_dashboard.html)
- [main_app/templates/main_app/nurse/patient_detail.html](main_app/templates/main_app/nurse/patient_detail.html)

---

## راه‌اندازی سریع

پیش‌نیازها: Python 3.10+ و pip

1) ساخت و فعال‌سازی محیط مجازی

Windows:
```
python -m venv .venv
.venv\Scripts\activate
```

macOS/Linux:
```
python3 -m venv .venv
source .venv/bin/activate
```

2) نصب وابستگی‌ها (در صورت نبود requirements.txt)
```
pip install django django-jalali pandas xlsxwriter
# وابستگی اختیاری برای پزشک‌یار هوش مصنوعی:
pip install g4f
```

3) پایگاه‌داده (SQLite پیش‌فرض)
- پیکربندی انجام شده در: [hospital_project/settings.py](hospital_project/settings.py)

4) مهاجرت‌ها و ساخت سوپرکاربر
```
python manage.py migrate
python manage.py createsuperuser
```

5) اجرای سرور توسعه
```
python manage.py runserver
```
سپس به آدرس http://127.0.0.1:8000 مراجعه کنید.

---

## ساختار پوشه‌ها

```
e:/hospital_project
├─ manage.py
├─ hospital_project/
│  ├─ settings.py
│  ├─ urls.py
│  └─ wsgi.py
├─ main_app/
│  ├─ models.py
│  ├─ views.py
│  ├─ urls.py
│  ├─ forms.py
│  ├─ services/
│  │  └─ ai_summary.py
│  ├─ templates/
│  │  ├─ base.html
│  │  ├─ base_Dr.html
│  │  ├─ base_Nurse.html
│  │  ├─ main_app/login.html
│  │  ├─ main_app/register.html
│  │  ├─ main_app/dr/doctor_dashboard.html
│  │  ├─ main_app/dr/patient_detail.html
│  │  ├─ main_app/dr/edit_patient.html
│  │  ├─ main_app/dr/nurse_list.html
│  │  ├─ main_app/dr/nurse_detail.html
│  │  ├─ main_app/nurse/nurse_dashboard.html
│  │  ├─ main_app/nurse/add_patient.html
│  │  ├─ main_app/nurse/edit_patient.html
│  │  └─ main_app/nurse/edit_vital_signs.html
│  └─ templatetags/form_tags.py
├─ screenshots/
│  ├─ Screenshot 2025-10-22 132658.png
│  └─ Screenshot 2025-10-22 135209.png
└─ static/
```

---

## مسیرها و صفحات کلیدی

- خانه و هدایت نقش‌ها: [main_app/views.py](main_app/views.py)
- ورود/ثبت‌نام: [main_app/templates/main_app/login.html](main_app/templates/main_app/login.html) · [main_app/templates/main_app/register.html](main_app/templates/main_app/register.html)
- داشبورد پزشک/پرستار:
  - [main_app/templates/main_app/dr/doctor_dashboard.html](main_app/templates/main_app/dr/doctor_dashboard.html)
  - [main_app/templates/main_app/nurse/nurse_dashboard.html](main_app/templates/main_app/nurse/nurse_dashboard.html)
- جزئیات بیمار:
  - پزشک: [main_app/templates/main_app/dr/patient_detail.html](main_app/templates/main_app/dr/patient_detail.html)
  - پرستار: [main_app/templates/main_app/nurse/patient_detail.html](main_app/templates/main_app/nurse/patient_detail.html)
- اندپوینت خلاصه AI (غیرهمگام):
  - [main_app/urls.py](main_app/urls.py) · نام مسیر: patient_ai_summary_nr
  - الگوی URL: `/patient_nr/<pk>/ai_summary/`

---

## پزشک‌یار هوش مصنوعی (AI Assistant)

- موتور: gpt4free (g4f) با چند مدل و تلاش مجدد (Multi‑Model Retry)
- اتصال سرویس:
  - کد سرویس: [main_app/services/ai_summary.py](main_app/services/ai_summary.py)
  - فراخوانی در ویو‌ها: [main_app/views.py](main_app/views.py)
- رفتار:
  - خلاصه AI پس از بارگذاری صفحه به صورت غیرهمگام دریافت و نمایش می‌شود
  - در صورت عدم دسترسی سرویس، خلاصه محلی مبتنی بر قواعد (Rule‑based) نمایش داده می‌شود
- لودینگ و لاگ مرحله‌ای کنسول:
  - در کنسول مرورگر گروهی با عنوان "AI Assistant Summary" ثبت می‌شود
  - مراحل قابل مشاهده: INIT، REQUEST_SENT، RESPONSE_RECEIVED، JSON_PARSED، RETRY_SCHEDULED (در صورت تلاش مجدد)، RENDERED، FAILED
  - زمان کل عملیات با `console.time('AI_total')` اندازه‌گیری و با `console.timeEnd` گزارش می‌شود
- نصب وابستگی اختیاری:
  - `pip install g4f`
  - پس از نصب، سرویس به صورت خودکار فعال می‌شود؛ در صورت عدم نصب، خلاصه محلی نمایش داده می‌شود

نکته: فایل‌های HAR و کوکی‌ها برای برخی مسیرهای g4f در پوشه زیر قرار دارند (اختیاری):
- [main_app/services/har_and_cookies/](main_app/services/har_and_cookies/)

---

## بهینه‌سازی عملکرد

- محدودسازی رکوردها جهت رندر سریع جدول و نمودار (مثلاً 200 رکورد اخیر)
- محدودسازی ورودی پرامپت AI به ~50 رکورد برای تولید سریع خلاصه
- تزریق ایمن داده‌ها به Chart.js با json_script برای حذف خطاهای JS

---

## تجربه کاربری (UI/UX) و دسترس‌پذیری

- چیدمان راست‌چین کامل و فونت دوستانه برای فارسی
- فرم‌ها با استایل یکپارچه، پیام خطای میدان به صورت نزدیک هر فیلد
- منوهای دسترس‌پذیر با aria، پشتیبانی ESC و کلیک بیرون
- پیام‌های سیستم (موفقیت/خطا) به‌صورت Toast در [main_app/templates/base.html](main_app/templates/base.html)

---

## نصب و پیکربندی سریع g4f (اختیاری)

1) نصب:
```
pip install g4f
```
2) اجرای برنامه:
- هیچ پیکربندی اضافی لازم نیست؛ سرویس به صورت خودکار تلاش می‌کند پاسخ از مدل‌های موجود دریافت کند
- در کنسول مرورگر لاگ‌های مرحله‌ای را مشاهده کنید تا وضعیت درخواست مشخص باشد

---

## توسعه و مشارکت

- مخزن را Fork کنید و شاخه جدید بسازید
- تغییرات را اعمال کرده و Pull Request ارسال کنید
- برای استایل فرم‌ها از [main_app/templatetags/form_tags.py](main_app/templatetags/form_tags.py) و کلاس‌های تعریف‌شده در [main_app/templates/base.html](main_app/templates/base.html) استفاده کنید

---

## نکات سئو برای مخزن

- عنوان و توضیحات دقیق با کلمات کلیدی: مدیریت بیمارستان، سامانه بیمارستان، Django، علائم حیاتی، Chart.js، RTL، فارسی، خروجی اکسل، هوش مصنوعی، gpt4free
- افزودن اسکرین‌شات‌های واضح با عنوان مناسب و جایگذاری در بخش تصاویر
- استفاده از Topics مانند: hospital-management، django، rtl، chartjs، persian، ai-assistant، gpt4free
- نگهداری README به‌روز و اشاره به تغییرات مهم در Issue یا Releases

---

## مجوز

این پروژه تحت مجوز MIT منتشر می‌شود. در صورت نیاز فایل LICENSE اضافه کنید.

---

## پشتیبانی

اگر مشکلی مشاهده شد، Issue باز کنید و اطلاعات کامل (نسخه پایتون، پیام خطا، اسکرین‌شات‌ها) را درج کنید.