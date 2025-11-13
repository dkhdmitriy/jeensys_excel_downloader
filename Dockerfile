FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

# Установим системные зависимости для Chromium и работы Selenium
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       wget gnupg ca-certificates unzip \
       fonts-liberation libnss3 libxss1 libasound2 lsb-release \
       libatk1.0-0 libatk-bridge2.0-0 libcups2 libx11-xcb1 libxcb1 \
       libxcomposite1 libxdamage1 libxrandr2 libgbm1 libpangocairo-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Установим Chromium из репозиториев (подходит для большинства Debian/Ubuntu образов)
RUN apt-get update \
    && apt-get install -y --no-install-recommends chromium \
    && rm -rf /var/lib/apt/lists/*

# Указать явный путь к бинарнику Chrome/Chromium для приложений
ENV CHROME_BIN=/usr/bin/chromium

# Рабочая директория
WORKDIR /app

# Копируем зависимости и ставим их
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Копируем проект в образ
COPY . /app

# Порт, если нужен
EXPOSE 80

# Команда по умолчанию — запуск Telegram-бота (можно переопределить в CI)
CMD ["python", "bot.py"]
