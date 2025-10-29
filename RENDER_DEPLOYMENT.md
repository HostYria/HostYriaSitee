# دليل نشر المشروع على Render

## المتطلبات الأساسية

1. حساب على [Render.com](https://render.com)
2. ربط الحساب مع GitHub/GitLab
3. رفع المشروع إلى repository على GitHub

## خطوات النشر

### 1. تجهيز المشروع

المشروع جاهز للنشر ويحتوي على:
- ✅ ملف `render.yaml` للإعدادات التلقائية
- ✅ أوامر Build و Start محددة في `package.json`
- ✅ المنفذ (PORT) مُعد ديناميكياً عبر `process.env.PORT`

### 2. إنشاء خدمة جديدة على Render

1. افتح [Render Dashboard](https://dashboard.render.com)
2. اضغط على **New** ← **Web Service**
3. اختر repository المشروع من GitHub
4. Render سيكتشف تلقائياً ملف `render.yaml`

### 3. إعداد المتغيرات البيئية (Environment Variables)

يجب إضافة المتغيرات التالية في Render Dashboard:

| المتغير | الوصف | مطلوب |
|---------|--------|-------|
| `HOSTYRIA_BOT_TOKEN` | رمز Telegram Bot من @BotFather | ✅ نعم |
| `DATABASE_URL` | رابط قاعدة البيانات PostgreSQL | ✅ نعم |
| `SESSION_SECRET` | مفتاح سري للجلسات (يُنشأ تلقائياً) | ✅ نعم |
| `NODE_ENV` | البيئة (production) | ✅ نعم |

#### كيفية إضافة المتغيرات:

1. في صفحة الخدمة، اذهب إلى **Environment**
2. اضغط **Add Environment Variable**
3. أضف كل متغير مع قيمته

### 4. إعداد قاعدة البيانات

#### الخيار 1: استخدام PostgreSQL من Render (موصى به)

1. في Render Dashboard، اضغط **New** ← **PostgreSQL**
2. اختر الخطة المناسبة (Free tier متاح)
3. بعد الإنشاء، انسخ **Internal Database URL**
4. أضفه كمتغير `DATABASE_URL` في الخدمة

#### الخيار 2: استخدام قاعدة بيانات خارجية

يمكنك استخدام:
- [Neon](https://neon.tech) - PostgreSQL مجاني
- [Supabase](https://supabase.com) - PostgreSQL مع Realtime
- [Railway](https://railway.app) - PostgreSQL مع دعم جيد

### 5. النشر

1. اضغط **Create Web Service**
2. Render سيقوم تلقائياً بـ:
   - تثبيت الحزم (`npm install`)
   - بناء المشروع (`npm run build`)
   - تشغيل الخادم (`npm run start`)

المشروع سيكون متاحاً على: `https://hostyria.onrender.com`

### 6. النشر التلقائي

كل `git push` للفرع الرئيسي سيؤدي إلى نشر تلقائي جديد.

## معلومات إضافية

### الأوامر المستخدمة

```json
{
  "build": "vite build && esbuild server/index.ts --platform=node --packages=external --bundle --format=esm --outdir=dist",
  "start": "NODE_ENV=production node dist/index.js"
}
```

### الخطة المجانية

- ✅ 750 ساعة شهرياً
- ✅ 512 MB RAM
- ⚠️ يتوقف بعد 15 دقيقة من عدم النشاط
- ⚠️ أول طلب بعد التوقف قد يأخذ ~30 ثانية

### الترقية للخطة المدفوعة

للحصول على خدمة 24/7 بدون توقف:
- **Starter Plan**: $7/شهر
- 512 MB RAM
- دائماً نشط

## استكشاف الأخطاء

### خطأ في البناء (Build Error)

1. تحقق من سجلات البناء في Render
2. تأكد من تثبيت جميع الحزم في `package.json`
3. جرب البناء محلياً: `npm run build`

### خطأ في التشغيل (Runtime Error)

1. تحقق من السجلات (Logs) في Render Dashboard
2. تأكد من إضافة جميع المتغيرات البيئية
3. تحقق من اتصال قاعدة البيانات

### مشكلة في Telegram Bot

1. تأكد من صحة `HOSTYRIA_BOT_TOKEN`
2. تحقق من أن البوت نشط في @BotFather
3. راجع السجلات للتأكد من الاتصال

## الدعم

- [Render Docs](https://render.com/docs)
- [Render Discord](https://discord.gg/render)
- [Render Status](https://status.render.com)

---

## English Version

# Render Deployment Guide

## Prerequisites

1. Account on [Render.com](https://render.com)
2. Connect account with GitHub/GitLab
3. Push project to GitHub repository

## Deployment Steps

### 1. Project Preparation

Project is ready with:
- ✅ `render.yaml` configuration file
- ✅ Build & Start commands in `package.json`
- ✅ Dynamic PORT via `process.env.PORT`

### 2. Create New Service on Render

1. Open [Render Dashboard](https://dashboard.render.com)
2. Click **New** ← **Web Service**
3. Select project repository from GitHub
4. Render will auto-detect `render.yaml`

### 3. Environment Variables Setup

Required variables:

| Variable | Description | Required |
|----------|-------------|----------|
| `HOSTYRIA_BOT_TOKEN` | Telegram Bot token from @BotFather | ✅ Yes |
| `DATABASE_URL` | PostgreSQL connection string | ✅ Yes |
| `SESSION_SECRET` | Secret key for sessions (auto-generated) | ✅ Yes |
| `NODE_ENV` | Environment (production) | ✅ Yes |

### 4. Database Setup

**Option 1: Render PostgreSQL** (Recommended)
1. Create new PostgreSQL database
2. Copy **Internal Database URL**
3. Add as `DATABASE_URL` environment variable

**Option 2: External Database**
- [Neon](https://neon.tech)
- [Supabase](https://supabase.com)
- [Railway](https://railway.app)

### 5. Deploy

Click **Create Web Service** and Render will automatically build and deploy.

Your app will be live at: `https://hostyria.onrender.com`

## Free Tier Limits

- 750 hours/month
- 512 MB RAM
- Spins down after 15 min inactivity
- First request after sleep ~30 seconds

## Troubleshooting

Check logs in Render Dashboard for any errors.
