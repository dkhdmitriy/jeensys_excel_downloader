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
    && apt-get install -y --no-install-recommends chromium chromium-driver || true \
    && rm -rf /var/lib/apt/lists/*

# Указать явный путь к бинарнику Chrome/Chromium для приложений
ENV CHROME_BIN=/usr/bin/chromium

# Рабочая директория
WORKDIR /app

# Копируем зависимости и ставим их
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Покажем версии Chromium и ChromeDriver для отладки (лог сборки)
RUN if command -v chromium >/dev/null 2>&1; then chromium --version || true; fi
RUN if command -v chromedriver >/dev/null 2>&1; then chromedriver --version || true; fi

# Автоматически скачиваем ChromeDriver, соответствующий установленной версии Chromium.
# Используем хранилище chromedriver.storage.googleapis.com: запрашиваем LATEST_RELEASE_<MAJOR>
RUN set -eux; \
        if command -v chromium >/dev/null 2>&1; then \
            CHROME_VER_FULL=$(chromium --version | awk '{print $2}' || true); \
            echo "Detected Chromium version: $CHROME_VER_FULL"; \
            CHROME_MAJOR=$(echo "$CHROME_VER_FULL" | cut -d. -f1); \
            echo "Chromium major: $CHROME_MAJOR"; \
            LATEST_DRIVER_VERSION=$(wget -qO- "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_MAJOR}" || true); \
            if [ -z "$LATEST_DRIVER_VERSION" ]; then \
                echo "Не удалось получить LATEST_RELEASE for $CHROME_MAJOR, пытаемся без суффикса"; \
                LATEST_DRIVER_VERSION=$(wget -qO- "https://chromedriver.storage.googleapis.com/LATEST_RELEASE" || true); \
            fi; \
            echo "Chromedriver version to download: $LATEST_DRIVER_VERSION"; \
            if [ -n "$LATEST_DRIVER_VERSION" ]; then \
                wget -q -O /tmp/chromedriver_linux64.zip "https://chromedriver.storage.googleapis.com/${LATEST_DRIVER_VERSION}/chromedriver_linux64.zip"; \
                unzip -q /tmp/chromedriver_linux64.zip -d /tmp || true; \
                mv -f /tmp/chromedriver /usr/local/bin/chromedriver; \
                chmod +x /usr/local/bin/chromedriver; \
                rm -f /tmp/chromedriver_linux64.zip; \
            else \
                echo "Не найден chromedriver для версии Chromium $CHROME_VER_FULL"; \
            fi; \
        else \
            echo "Chromium не установлен; пропускаем загрузку chromedriver"; \
        fi

# Копируем проект в образ
COPY . /app

# Порт, если нужен
EXPOSE 80

# Команда по умолчанию — запуск Telegram-бота (можно переопределить в CI)
CMD ["python", "bot.py"]
