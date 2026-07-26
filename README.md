<div align="center">

<img src="emblem.png" alt="AI Prozorro Intelligence" width="120" />

# AI Prozorro Intelligence

**Відкрита AI-платформа моніторингу державних закупівель України**

Автоматичний збір тендерів з Prozorro • Оцінка корупційних ризиків • AI-пояснення кожного підозрілого тендера

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-16-000000?logo=next.js&logoColor=white)](https://nextjs.org/)
[![Groq](https://img.shields.io/badge/AI-Llama_3.3_70B_(Groq)-F55036)](https://groq.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Українська 🇺🇦 | English 🇬🇧 — інтерфейс двомовний

</div>

---

## 📸 Скриншоти

### Дашборд
KPI-метрики, динаміка закупівель, топ підозрілих тендерів (завершені та активні окремо) з AI-аналізом при наведенні.

![Дашборд](docs/screenshots/dashboard.png)

### Аналітика
Різнокольорові графіки за регіонами, категоріями CPV, компаніями-переможцями та замовниками.

![Аналітика](docs/screenshots/analytics.png)

### Тендери
Пошук, фільтри за ризиком/регіоном, сортування за сумою, ризиком і датою.

![Тендери](docs/screenshots/tenders.png)

### Щоденні звіти
Автоматичний звіт: нові тендери, обсяг, підозрілі закупівлі дня, найактивніший регіон.

![Звіти](docs/screenshots/reports.png)

---

## 🎯 Що вміє платформа

- **🔄 Автоматична синхронізація** — кожні 30 хвилин підтягує нові тендери з відкритого API Prozorro (без дублікатів: унікальний індекс + перевірка перед імпортом)
- **⚠️ Risk Engine** — власний рушій оцінки ризику (0–100) за факторами: один учасник, завищена ціна відносно категорії, короткі строки подання, "улюблені" постачальники замовника тощо
- **🧠 AI-аналіз (Llama 3.3 70B через Groq)** — для кожного підозрілого тендера генерується структурований висновок за 8 критеріями: умови участі, строки, ціна (з порівнянням із середньою по CPV-категорії та прикладами цін), кількість учасників, історія переможця, зміни умов, оскарження, профіль замовника. Кожен висновок завершується обов'язковим дисклеймером — це **не юридичний висновок**
- **📊 Аналітика** — розподіл закупівель за регіонами, CPV-категоріями, топ компаній-переможців і замовників
- **📅 Щоденні звіти** — зведення дня: кількість нових тендерів, обсяг, список підозрілих
- **🌐 Двомовність** — повністю українська та англійська локалізації (next-intl)
- **📱 Адаптивність** — працює на комп'ютері та телефоні (мобільне меню, доступ по локальній мережі)
- **🌙 Темна/світла тема**

---

## 🏗️ Архітектура

```
┌─────────────────┐     кожні 30 хв      ┌──────────────────────────┐
│  Prozorro API   │ ───────────────────► │  FastAPI Backend          │
│  (відкриті дані)│                      │  • Sync Service           │
└─────────────────┘                      │  • Risk Engine            │
                                         │  • AI Analyzer (Groq)     │
┌─────────────────┐                      │  • APScheduler            │
│  Groq API       │ ◄─────────────────── │  • SQLite / PostgreSQL    │
│  Llama 3.3 70B  │   rate limited       └────────────┬─────────────┘
└─────────────────┘   28 req/хв, 950/день             │ REST API
                                         ┌────────────▼─────────────┐
                                         │  Next.js 16 Frontend      │
                                         │  • Дашборд • Аналітика    │
                                         │  • Тендери • Звіти        │
                                         │  • UK/EN • Dark mode      │
                                         └──────────────────────────┘
```

### Технології

| Шар | Стек |
|---|---|
| Backend | Python 3.13, FastAPI, SQLAlchemy 2.0 (async), APScheduler |
| База даних | SQLite (локально) / PostgreSQL — Neon (продакшн) |
| AI | Groq API — `llama-3.3-70b-versatile` (безкоштовний тариф) |
| Frontend | Next.js 16, TypeScript, Tailwind CSS, shadcn/ui, Recharts, next-intl |
| Автоматизація | n8n (Telegram-сповіщення), Docker Compose |

---

## 🚀 Швидкий старт

### Вимоги

- Python 3.13+
- Node.js 20+
- Безкоштовний API-ключ [Groq](https://console.groq.com/)

### 1. Клонування та налаштування

```bash
git clone https://github.com/dev-arthur-petrunko/AI_Prozorro_Intelligence.git
cd AI_Prozorro_Intelligence

# Створіть .env з прикладу та вкажіть свій GROQ_API_KEY
cp .env.example .env
```

### 2. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/macOS
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

При першому запуску база створиться автоматично і почнеться імпорт останніх тендерів з Prozorro.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Відкрийте **http://localhost:3000** — платформа готова.

### 4. Доступ з телефона (опційно)

Запустіть `firewall-setup.ps1` від імені адміністратора (відкриває порти 3000/8000) і відкрийте `http://<IP-компʼютера>:3000` з телефона в тій самій Wi-Fi мережі.

---

## ☁️ Деплой у хмару (безкоштовно)

Платформа розгортається на безкоштовних тарифах: **Neon** (PostgreSQL) + **Render** (бекенд) + **Vercel** (фронтенд).

📖 Повна покрокова інструкція: **[DEPLOYMENT.md](DEPLOYMENT.md)**

---

## ⚙️ Конфігурація (.env)

| Змінна | Опис | За замовчуванням |
|---|---|---|
| `GROQ_API_KEY` | Ключ Groq API для AI-аналізу | — (обовʼязково) |
| `GROQ_MODEL` | Модель LLM | `llama-3.3-70b-versatile` |
| `GROQ_MAX_REQUESTS_PER_MINUTE` | Ліміт запитів до Groq за хвилину | `28` |
| `GROQ_MAX_REQUESTS_PER_DAY` | Ліміт запитів до Groq за день | `950` |
| `SYNC_INTERVAL_MINUTES` | Частота синхронізації з Prozorro | `30` |
| `BACKEND_CORS_ORIGINS` | Дозволені origin для API | `http://localhost:3000` |
| `TELEGRAM_BOT_TOKEN` | Токен бота для сповіщень (n8n) | опційно |
| `TELEGRAM_CHANNEL_ID` | ID каналу для сповіщень | опційно |

---

## 📡 Основні API ендпоінти

| Метод | Шлях | Опис |
|---|---|---|
| `GET` | `/dashboard` | KPI, графік, топ підозрілих (завершені/активні), останні тендери |
| `GET` | `/tenders` | Список тендерів: пошук, фільтри (`risk_min`, `region`), сортування |
| `GET` | `/tenders/{id}` | Деталі тендера з повним AI-аналізом і ризик-факторами |
| `GET` | `/analytics` | Аналітика за регіонами, категоріями, компаніями, замовниками |
| `GET` | `/reports/daily` | Щоденний звіт |
| `GET` | `/health` | Стан сервісу |
| `POST` | `/admin/run-ai-analysis` | Ручний запуск AI-аналізу (`?force=true&limit=N`) |
| `POST` | `/admin/run-analytics` | Ручний перерахунок аналітики |

Інтерактивна документація: **http://localhost:8000/docs** (Swagger UI)

---

## 🤖 Як працює оцінка ризиків

1. **Risk Engine** нараховує бали за зваженими факторами (один учасник, відхилення ціни від середньої по категорії, стислі строки, концентрація перемог у одного постачальника тощо) → **Risk Score 0–100**
2. Тендери з score > 30 потрапляють у чергу **AI-аналізу**
3. LLM отримує повні дані тендера + цінові порівняння по CPV-категорії та формує висновок за 8 критеріями зі шкалою підозрілості 1–10 і "червоними прапорцями"
4. Формулювання обережні ("може свідчити про...") — платформа **не звинувачує**, а привертає увагу громадськості

> ⚠️ **Дисклеймер:** аналіз є автоматичним припущенням на основі відкритих даних і не є юридичним висновком чи доказом порушення. Для офіційних висновків звертайтесь до АМКУ, ДАСУ або НАЗК.

---

## 🗂️ Структура проєкту

```
├── backend/
│   └── app/
│       ├── api/routes/      # dashboard, tenders, analytics, reports, health
│       ├── ai/              # Risk Engine, Groq клієнт, AI analyzer
│       ├── analytics/       # агрегації, retention (ковзне вікно 90 днів)
│       ├── collectors/      # Prozorro API клієнт, нормалізація, синхронізація
│       ├── models/          # Tender, Company, Buyer, AnalyticsSnapshot
│       └── scheduler/       # APScheduler задачі
├── frontend/
│   └── src/
│       ├── app/[locale]/    # дашборд, тендери, аналітика, звіти (UK/EN)
│       ├── components/      # UI, графіки, бейджі ризику/статусу
│       └── services/api.ts  # REST клієнт
├── n8n/                     # Workflow для Telegram-сповіщень
├── docs/screenshots/        # Скриншоти для README
└── docker-compose.yml       # PostgreSQL + n8n
```

---

## 📄 Ліцензія

Проєкт з відкритим кодом. Дані — з відкритого API [Prozorro](https://prozorro.gov.ua/).

Створено для підвищення прозорості державних закупівель України 🇺🇦
