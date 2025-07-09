# 📛 Scholar Profile API

این پروژه یک API بر باستی یِ FastAPI است که اطلاعات عمومی پروفایل Google Scholar کاربران را جمع‌آوری می‌کند و با استفاده از SQLAlchemy در پایگاه داده ذخیره می‌نماید. داده‌ها شامل اطلاعات پروفایل، شاخص‌های استنادی و مقالات علمی است.

---

## 🚀 ویژگی‌ها

- دریافت اطلاعات پروفایل Google Scholar از روی URL یا ID
- ذخیره‌سازی داده‌ها در PostgreSQL
- کش 24 ساعته برای جلوگیری از درخواست‌های تکراری
- استخراج مقالات تا 100 عدد
- ساختار مدرن با استفاده از:
  - FastAPI
  - SQLAlchemy (async)
  - PostgreSQL
  - Docker و Docker Compose

---

## 🫐 پیش‌نیازها

- Python 3.11+
- Docker & Docker Compose
- Git

---

## ⚙️ نصب و اجرا

### 1. کلون کردن مخزن

```bash
git clone https://github.com/alirezarazani2003/scholar-service.git
cd scholar-service
```

### 2. تنظیم متغیرهای محیطی

یک فایل `.env` در ریشه بسازید:

```env
POSTGRES_USER=youruser
POSTGRES_PASSWORD=yourpassword
POSTGRES_DB=scholar_db
DATABASE_URL=postgresql+asyncpg://youruser:yourpassword@db:5432/scholar_db
```

### 3. اجرای پروژه با Docker

```bash
docker-compose up --build -d
```

API به صورت پیش‌فرض روی `http://localhost:8000` در دسترس خواهد بود.

---

## 📦 ساختار پروژه

```
scholar-service/
│
├── app/
│   ├── main.py            # کد اصلی API
│   ├── models.py          # تعریف ORM برای پروفایل و مقاله
│   ├── database.py        # اتصال به دیتابیس
│
├── requirements.txt       # وابستگی‌های پایتون
├── docker-compose.yml     # تعریف سرویس‌ها
├── Dockerfile             # ساخت ایمیج اپلیکیشن
├── .env                   # متغیرهای محیطی
└── README.md              # فایل راهنما
```

---

## 📱 مستندات API

پس از اجرای پروژه، مستندات خودکار در دسترس هستند:

- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🧪 نمونه درخواست

### `POST /scholar/profile/`

#### Request Body:

```json
{
  "user_url": "https://scholar.google.com/citations?user=abcd1234"
}
```

یا فقط ID:

```json
{
  "user_url": "abcd1234"
}
```

#### Response:

```json
{
  "name": "John Doe",
  "affiliation": "University of Example",
  "email": "Verified email at example.edu",
  "h_index_all": 35,
  "h_index_recent": 12,
  "i10_index_all": 50,
  "i10_index_recent": 20,
  "citations_all": 3000,
  "citations_recent": 600,
  "articles": [
    {
      "title": "Sample Paper Title",
      "link": "https://scholar.google.com/...",
      "year": "2020",
      "citations": 120
    }
  ]
}
```

---

## 💪 توسعه

برای اجرای پروژه بدون Docker:

```bash
# فعال‌سازی محیط مجازی
python -m venv venv
source venv/bin/activate

# نصب وابستگی‌ها
pip install -r requirements.txt

# اجرای پروژه
uvicorn app.main:app --reload
```

---
