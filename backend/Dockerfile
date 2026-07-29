FROM python:3.13-slim

WORKDIR /app

# Системні залежності
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python залежності
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Код додатку
COPY . .

# Порт (Render передає свій порт через $PORT; локально - 8000)
EXPOSE 8000

# Запуск: shell-форма, щоб розкрити $PORT (з дефолтом 8000 для локального docker run)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
