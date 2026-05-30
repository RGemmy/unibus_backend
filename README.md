# 🐍 UniBus — Django Backend

نظام النقل الجامعي — الـ Backend مبني بـ **Django 5 + Django REST Framework**

---

## 🚀 تشغيل المشروع

```bash
# 1. إنشاء بيئة افتراضية
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# 2. تثبيت المكتبات
pip install -r requirements.txt

# 3. إنشاء قاعدة البيانات
python manage.py migrate

# 4. إضافة بيانات تجريبية
python manage.py seed_data

# 5. تشغيل السيرفر
python manage.py runserver
```

السيرفر يعمل على: `http://localhost:8000`

---

## 📁 هيكل المشروع

```
unibus-backend/
├── config/
│   ├── settings.py       # الإعدادات الرئيسية
│   ├── urls.py           # الـ URLs الرئيسية
│   └── wsgi.py
├── apps/
│   ├── users/            # المستخدمون + Auth + السائقون + المشرفون
│   ├── buses/            # الباصات
│   ├── routes/           # المسارات + الجداول + الأماكن
│   ├── trips/            # الرحلات
│   ├── students/         # الطلاب + الجامعات
│   ├── reservations/     # الحجوزات
│   ├── payments/         # المدفوعات + أنواع الدفع
│   └── subscriptions/    # الاشتراكات
├── requirements.txt
├── manage.py
└── .env
```

---

## 🔑 بيانات الدخول (بعد seed_data)

| الدور | البريد | كلمة المرور |
|-------|--------|-------------|
| مدير | admin@unibus.sa | admin123 |
| طالب | sara@student.sa | student123 |
| سائق | driver1@unibus.sa | driver123 |

---

## 📡 API Endpoints

### 🔐 المصادقة
```
POST   /api/auth/register/          تسجيل حساب جديد
POST   /api/auth/login/             تسجيل الدخول → يرجع token
POST   /api/auth/logout/            تسجيل الخروج
GET    /api/auth/me/                بيانات المستخدم الحالي
POST   /api/auth/token/refresh/     تجديد الـ token
```

### 🚌 الباصات
```
GET    /api/buses/                  قائمة الباصات
POST   /api/buses/                  إضافة باص
GET    /api/buses/{id}/             تفاصيل باص
PUT    /api/buses/{id}/             تعديل باص
DELETE /api/buses/{id}/             حذف باص
```

### 🗺️ المسارات والأماكن
```
GET    /api/routes/                 قائمة المسارات (مع الجداول)
POST   /api/routes/                 إضافة مسار
GET    /api/routes/{id}/            تفاصيل مسار
PUT    /api/routes/{id}/            تعديل مسار
DELETE /api/routes/{id}/            حذف مسار

GET    /api/routes/places/          قائمة الأماكن
POST   /api/routes/places/          إضافة مكان

GET    /api/routes/schedules/       قائمة الجداول
POST   /api/routes/schedules/       إضافة جدول
```

### 🚍 الرحلات
```
GET    /api/trips/                  قائمة الرحلات
POST   /api/trips/                  إضافة رحلة
GET    /api/trips/{id}/             تفاصيل رحلة (مفصّلة)
PUT    /api/trips/{id}/             تعديل رحلة
DELETE /api/trips/{id}/             حذف رحلة
GET    /api/trips/today/            رحلات اليوم
PATCH  /api/trips/{id}/cancel/      إلغاء رحلة
```

**فلترة الرحلات:**
```
GET /api/trips/?status=active
GET /api/trips/?trip_date=2026-04-15
GET /api/trips/?place=1
```

### 🎓 الطلاب والجامعات
```
GET    /api/students/               قائمة الطلاب
POST   /api/students/               إضافة طالب (ينشئ User + Student معاً)
GET    /api/students/{id}/          تفاصيل طالب
PUT    /api/students/{id}/          تعديل طالب
DELETE /api/students/{id}/          حذف طالب

GET    /api/students/universities/  قائمة الجامعات
POST   /api/students/universities/  إضافة جامعة
```

### 📋 الحجوزات
```
GET    /api/reservations/           قائمة الحجوزات
POST   /api/reservations/           إضافة حجز
GET    /api/reservations/my/        حجوزاتي (للطالب المسجل)
PATCH  /api/reservations/{id}/cancel/    إلغاء حجز
PATCH  /api/reservations/{id}/confirm/   تأكيد حجز
```

### 💳 المدفوعات
```
GET    /api/payments/               قائمة المدفوعات
POST   /api/payments/               إضافة دفعة
GET    /api/payments/{id}/          تفاصيل دفعة
PUT    /api/payments/{id}/          تعديل دفعة

GET    /api/payments/types/         أنواع الدفع
POST   /api/payments/types/         إضافة نوع دفع
```

### 🔔 الاشتراكات
```
GET    /api/subscriptions/          قائمة الاشتراكات
POST   /api/subscriptions/          إضافة اشتراك
GET    /api/subscriptions/{id}/     تفاصيل اشتراك
PUT    /api/subscriptions/{id}/     تعديل اشتراك
PATCH  /api/subscriptions/{id}/cancel/  إلغاء اشتراك
```

### 👥 المستخدمون والأدوار (admin فقط)
```
GET    /api/auth/users/             قائمة المستخدمين
POST   /api/auth/users/             إضافة مستخدم
PUT    /api/auth/users/{id}/        تعديل مستخدم
DELETE /api/auth/users/{id}/        حذف مستخدم

GET    /api/auth/roles/             قائمة الأدوار
GET    /api/auth/drivers/           قائمة السائقين
POST   /api/auth/drivers/           إضافة سائق
```

### 📊 الإحصائيات
```
GET    /api/auth/dashboard/stats/   إحصائيات لوحة التحكم
```

---

## 🔐 المصادقة

النظام يستخدم **JWT (JSON Web Token)**

```bash
# تسجيل الدخول
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@unibus.sa", "password": "admin123"}'

# استخدام الـ Token
curl http://localhost:8000/api/trips/ \
  -H "Authorization: Bearer <token>"
```

---

## 🔍 الفلترة والبحث والترتيب

كل endpoint يدعم:

```bash
# بحث
GET /api/students/?search=سارة

# فلترة
GET /api/trips/?status=active&trip_date=2026-04-15

# ترتيب
GET /api/buses/?ordering=capacity
GET /api/trips/?ordering=-trip_date      # تنازلي

# صفحات
GET /api/students/?page=2&page_size=10
```

---

## 🛠️ الـ Admin Panel

```
http://localhost:8000/admin/
البريد: admin@unibus.sa
الباسورد: admin123
```

---

## ⚙️ إعدادات قاعدة البيانات (PostgreSQL)

في ملف `config/settings.py` بدّل الـ DATABASES:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'unibus_db',
        'USER': 'postgres',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

وثبّت: `pip install psycopg2-binary`

---

## 📝 ملاحظات التطوير

- الـ `DEBUG=True` في `.env` — غيّره في الإنتاج
- الـ `SECRET_KEY` في `.env` — غيّره لقيمة قوية في الإنتاج
- الـ `CORS_ALLOWED_ORIGINS` في settings يسمح لـ React على port 5173
- الـ JWT token صالح لـ **يوم واحد** والـ refresh لـ **30 يوم**
