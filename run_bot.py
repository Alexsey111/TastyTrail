#!/usr/bin/env python3
"""
Скрипт для запуска Telegram-бота с настройкой переменных окружения
"""

import os
import sys

# Загружаем переменные окружения из .env файла
from dotenv import load_dotenv
load_dotenv()

# Получаем переменные окружения
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
SPOONACULAR_API_KEY = os.getenv('SPOONACULAR_API_KEY', '')

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Импортируем и запускаем бота
from bot import RecipeBot

if __name__ == "__main__":
    print("🍽️ Запуск TastyTrail Bot...")
    print("📱 Бот будет доступен в Telegram")
    print("🔍 API рецептов: TheMealDB (бесплатный)")
    print("=" * 50)
    
    # Проверяем наличие токена
    if not TELEGRAM_TOKEN:
        print("❌ ОШИБКА: Не найден TELEGRAM_TOKEN!")
        print("Создайте файл .env на основе env_example.txt и добавьте ваш токен")
        print("Пример:")
        print("TELEGRAM_TOKEN=ваш_токен_здесь")
        exit(1)
    
    try:
        bot = RecipeBot()
        bot.run()
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Ошибка при запуске бота: {e}")
        print("Проверьте:")
        print("1. Правильность токена бота")
        print("2. Подключение к интернету")
        print("3. Установку всех зависимостей")
