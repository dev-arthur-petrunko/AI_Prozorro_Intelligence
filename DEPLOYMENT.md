# 🚀 Деплой AI Prozorro Intelligence (безкоштовно)

Схема: **Neon** (PostgreSQL) + **Render** (бекенд FastAPI) + **Vercel** (фронтенд Next.js).

```
Vercel (frontend) ──► Render (backend) ──► Neon (PostgreSQL)
                                      └──► Groq API (AI)
```

---

## Крок 1. Neon — база даних PostgreSQL

1. Зареєструйтесь на [console.neon.tech](https://console.neon.tech) (безкоштовний план: 0.5 GB)
2. Створіть проєкт, наприклад `ai-prozorro`
3. На головній сторінці проєкту натисніть **Connect** і скопіюйте **Connection string**, виглядає так:
   ```
   postgresql://neondb_owner:npg_xxxx@ep-xxx-xxx.eu-central-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require
   ```
4. Збережіть цей рядок — він потрібен на кроці 2 як `DATABASE_URL`

> Нічого конвертувати не треба: бекенд сам перетворює URL під asyncpg і вмикає SSL.
> Таблиці створюються автоматично при першому старті бекенда.

---

## Крок 2. Render — бекенд

1. Зареєструйтесь на [render.com](https://render.com) через GitHub
2. **New → Web Service** → підключіть репозиторій `AI_Prozorro_Intelligence`. Render виявить `backend/Dockerfile` і обере runtime **Docker** (Root Directory: `backend`). Порт бекенд бере з `$PORT` автоматично.
3. У **Environment** заповніть секретні змінні:
   | Змінна | Значення |
   |---|---|
   | `DATABASE_URL` | connection string з Neon (крок 1) |
   | `GROQ_API_KEY` | ваш ключ з [console.groq.com](https://console.groq.com) |
   | `BACKEND_CORS_ORIGINS` | поки `http://localhost:3000`, після кроку 3 додати Vercel-домен |
4. Дочекайтесь деплою. Ваш бекенд: `https://ai-prozorro-intelligence.onrender.com`
5. Перевірка: відкрийте `https://<ваш-бекенд>.onrender.com/health` → має бути `{"status": "healthy"}`.
   Після першого старту почнеться імпорт тендерів з Prozorro (кілька хвилин).

### ⚠️ Особливості безкоштовного Render

- Сервіс **засинає після 15 хв без запитів** (перший запит потім триває ~50 сек).
- Коли сервіс спить — **планувальник не працює** (синхронізація кожні 30 хв не виконується).
- **Рішення:** безкоштовний пінгер [UptimeRobot](https://uptimerobot.com) або [cron-job.org](https://cron-job.org):
  моніторинг URL `https://<ваш-бекенд>.onrender.com/health` кожні 10–14 хвилин.

---

## Крок 3. Vercel — фронтенд

1. Зареєструйтесь на [vercel.com](https://vercel.com) через GitHub
2. **Add New → Project** → імпортуйте репозиторій `AI_Prozorro_Intelligence`
3. Налаштування проєкту:
   | Параметр | Значення |
   |---|---|
   | Framework Preset | Next.js (визначиться автоматично) |
   | **Root Directory** | `frontend` ← обов'язково! |
4. **Environment Variables**:
   | Змінна | Значення |
   |---|---|
   | `NEXT_PUBLIC_API_URL` | `https://ai-prozorro-intelligence.onrender.com` (URL з кроку 2, без слеша в кінці) |
5. **Deploy**. Ваш сайт: `https://<project>.vercel.app`

---

## Крок 4. Зв'язати CORS

1. Поверніться в Render → ваш сервіс → **Environment**
2. Оновіть `BACKEND_CORS_ORIGINS`:
   ```
   https://<project>.vercel.app,http://localhost:3000
   ```
3. Save → сервіс перезапуститься автоматично

---

## ✅ Перевірка

| Що | URL | Очікування |
|---|---|---|
| Бекенд живий | `https://<бекенд>.onrender.com/health` | `{"status": "healthy"}` |
| API документація | `https://<бекенд>.onrender.com/docs` | Swagger UI |
| Дані є | `https://<бекенд>.onrender.com/dashboard` | JSON з KPI |
| Сайт | `https://<project>.vercel.app/uk/dashboard` | Дашборд з даними |

---

## Ліміти безкоштовних тарифів

| Сервіс | Ліміт | Достатньо? |
|---|---|---|
| Neon | 0.5 GB, автосуспенд через 5 хв простою | ✅ база ~5-10 тис. тендерів займає < 100 MB |
| Render | 750 год/міс, сон після 15 хв | ✅ з пінгером працює постійно |
| Vercel | 100 GB трафіку/міс | ✅ більш ніж достатньо |
| Groq | 30 зап/хв, 1000 зап/день, 100k токенів/день | ✅ вбудований rate limiter |

## Оновлення

Просто пуште в `main` — Render і Vercel автоматично передеплоять:

```bash
git add .
git commit -m "опис змін"
git push
```
