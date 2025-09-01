import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

# API Keys
SPOONACULAR_API_KEY = os.getenv('SPOONACULAR_API_KEY')
THEMEALDB_API_URL = "https://www.themealdb.com/api/json/v1/1"

# Database
DATABASE_NAME = "recipes.db"

# Bot settings
MAX_RECIPES_PER_SEARCH = 5
MAX_FAVORITES_PER_USER = 50
