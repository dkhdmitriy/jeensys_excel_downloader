"""
Telegram-бот для анализа Excel файлов и отправки отчётов.
"""

import os
import sys
import logging
import subprocess
from typing import Dict, List

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import (
    find_latest_excel,
    parse_excel_devices,
    calculate_stats,
    format_number,
)

# Получаем токен Telegram бота из переменной окружения
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_TOKEN:
    raise RuntimeError(
        "Telegram bot token not found. Set environment variable TELEGRAM_BOT_TOKEN"
    )

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start."""
    chat_id = update.effective_chat.id
    await update.message.reply_text(
        "Привет! 👋\n\n"
        "Я помогу тебе анализировать Excel-файлы с устройствами.\n\n"
        "Доступные команды:\n"
        "/report - Получить отчёт по устройствам\n"
        "/help - Справка\n\n"
        f"Твой Chat ID: `{chat_id}`",
        parse_mode="Markdown"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help."""
    await update.message.reply_text(
        "📖 Справка:\n\n"
        "/report - Анализирует последний загруженный Excel-файл и отправляет отчёт\n"
        "/start - Показать приветствие\n"
        "/help - Показать эту справку"
    )


def format_report(devices_by_client: Dict[str, List[Dict]]) -> str:
    """Форматирует отчёт для отправки в Telegram."""
    
    lines = []
    lines.append("=" * 50)
    lines.append("📊 ОТЧЁТ ПО УСТРОЙСТВАМ")
    lines.append("=" * 50)
    lines.append("")
    
    # LTC сегмент
    ltc_clients = {
        "L7": devices_by_client.get("L7", []),
        "L9": devices_by_client.get("L9", [])
    }
    
    ltc_total_hashrate = 0
    
    for client_name, devices in ltc_clients.items():
        if not devices:
            continue
        
        stats = calculate_stats(devices)
        avg_hr = format_number(stats["avg_hashrate"], 2)
        count = int(round(stats["count"]))
        total_hr = int(round(stats["total_hashrate"]))
        
        lines.append(f"{client_name}-{avg_hr} ({count}шт-{total_hr}хэш)")
        ltc_total_hashrate += stats["total_hashrate"]
    
    ltc_total_str = int(round(ltc_total_hashrate))
    lines.append(f"ИТОГ LTC {ltc_total_str}")
    lines.append("")
    
    # BTC сегмент
    btc_clients_order = [
        ("WM", "WM"),
        ("T21", "T21"),
        ("S19", "S19"),
        ("S19_dop", "S19 доп"),
        ("S19_emcd", "S19 emcd"),
    ]
    
    s19_all_devices = []
    btc_total_hashrate = 0
    
    for client_key, display_name in btc_clients_order:
        devices = devices_by_client.get(client_key, [])
        
        if not devices:
            continue
        
        stats = calculate_stats(devices)
        avg_hr = format_number(stats["avg_hashrate"], 2)
        count = int(round(stats["count"]))
        total_hr = int(round(stats["total_hashrate"]))
        
        if client_key.startswith("S19"):
            s19_all_devices.extend(devices)
        
        lines.append(f"{display_name}-{avg_hr} ({count}шт-{total_hr}хэш)")
        btc_total_hashrate += stats["total_hashrate"]
    
    # Среднее по всем S19
    if s19_all_devices:
        s19_stats = calculate_stats(s19_all_devices)
        avg_s19 = format_number(s19_stats["avg_hashrate"], 2)
        s19_count = int(round(s19_stats["count"]))
        s19_total = int(round(s19_stats["total_hashrate"]))
        lines.append(f"Среднее S19 - {avg_s19} ({s19_count}шт-{s19_total}хэш)")
    
    btc_total_str = int(round(btc_total_hashrate))
    lines.append(f"ИТОГ BTC {btc_total_str}")
    lines.append("")
    
    return "\n".join(lines)


async def report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /report."""
    
    chat_id = update.effective_chat.id
    user_name = update.effective_user.first_name
    logger = logging.getLogger(__name__)
    logger.info(f"Получена команда /report от {user_name} (chat_id: {chat_id})")
    
    # Отправляем сообщение о начале процесса
    await update.message.reply_text("⏳ Начинаю скачивание файла с устройствами...")
    
    try:
        # Шаг 1: Запускаем main.py для скачивания Excel файла
        logger.info(f"Запускаю main.py для скачивания Excel файла...")
        
        # Получаем путь к main.py
        script_dir = os.path.dirname(os.path.abspath(__file__))
        main_py_path = os.path.join(script_dir, "main.py")
        
        # Запускаем main.py в headless режиме (без браузера в окне)
        # Используем subprocess для запуска в отдельном процессе
        result = subprocess.run(
            [sys.executable, main_py_path, "--headless"],
            capture_output=True,
            text=True,
            timeout=300  # Таймаут 5 минут
        )
        
        if result.returncode != 0:
            logger.error(f"Ошибка при запуске main.py: {result.stderr}")
            await update.message.reply_text(
                f"❌ Ошибка при скачивании файла:\n```\n{result.stderr}\n```",
                parse_mode="Markdown"
            )
            return
        
        logger.info("Файл успешно скачан, начинаю анализ...")
        await update.message.reply_text("📊 Анализирую загруженный файл...")
        
        # Шаг 2: Парсим устройства из скачанного файла
        excel_path = find_latest_excel()
        logger.info(f"Найден файл: {excel_path}")
        
        # Парсим устройства
        devices_by_client = parse_excel_devices(excel_path)
        
        if not devices_by_client:
            await update.message.reply_text("❌ Устройства не найдены в файле.")
            return
        
        # Форматируем отчёт
        report_text = format_report(devices_by_client)
        
        # Отправляем отчёт (разбиваем на части если нужно, так как лимит на сообщение)
        # Telegram лимит на сообщение - 4096 символов
        if len(report_text) <= 4096:
            await update.message.reply_text(
                f"```\n{report_text}\n```",
                parse_mode="Markdown"
            )
        else:
            # Если текст большой, разбиваем на части
            parts = [report_text[i:i+4000] for i in range(0, len(report_text), 4000)]
            for part in parts:
                await update.message.reply_text(
                    f"```\n{part}\n```",
                    parse_mode="Markdown"
                )
        
        logger.info(f"Отчёт успешно отправлен пользователю {user_name}")
        await update.message.reply_text("✅ Отчёт готов!")
    
    except subprocess.TimeoutExpired:
        logger.error("Таймаут при скачивании файла (более 5 минут)")
        await update.message.reply_text("❌ Ошибка: превышено время ожидания при скачивании файла (более 5 минут)")
    except FileNotFoundError as e:
        logger.error(f"Файл не найден: {e}")
        await update.message.reply_text(f"❌ Ошибка: {e}")
    except Exception as e:
        logger.error(f"Ошибка при анализе файла: {e}")
        await update.message.reply_text(f"❌ Ошибка при анализе файла: {e}")


def main() -> None:
    """Запуск Telegram-бота."""
    
    logger = logging.getLogger(__name__)
    logger.info("Инициализация Telegram-бота...")
    
    # Создаём приложение
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("report", report))
    
    # Запускаем бота
    logger.info("🤖 Telegram-бот запущен. Нажмите Ctrl+C для остановки.")
    print("🤖 Telegram-бот запущен. Нажмите Ctrl+C для остановки.")
    application.run_polling()


if __name__ == "__main__":
    main()
