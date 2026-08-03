FROM python:3.13-slim
WORKDIR /app

# Системні залежності
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# cloudflared — клієнт для TCP-тунелю до локальної БД на неттопі
RUN curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /usr/local/bin/cloudflared \
    && chmod +x /usr/local/bin/cloudflared

# Python залежності
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Код додатку
COPY . .

# Порт (Render передає свій порт через $PORT; локально - 8000)
EXPOSE 8000

# Запуск: піднімаємо cloudflared-тунель до Postgres у фоні, чекаємо, потім старт uvicorn
CMD ["sh", "-c", "cloudflared access tcp --hostname db.by-petrunko.com --url localhost:5432 & sleep 3 && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
