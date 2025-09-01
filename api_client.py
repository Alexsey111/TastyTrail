import requests
import json
import logging
from config import SPOONACULAR_API_KEY, THEMEALDB_API_URL
from translator import TranslatorService

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RecipeAPI:
    def __init__(self):
        self.spoonacular_api_key = SPOONACULAR_API_KEY
        self.themealdb_url = THEMEALDB_API_URL
        self.translator = TranslatorService()
    
    def search_recipes_themedb(self, query):
        """Поиск рецептов через TheMealDB API"""
        logger.info(f"🔍 TheMealDB поиск: '{query}'")
        try:
            url = f"{self.themealdb_url}/search.php"
            params = {'s': query}
            
            logger.info(f"📡 Запрос к TheMealDB: {url} с параметрами {params}")
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            meals = data.get('meals') or []
            logger.info(f"📥 Получен ответ от TheMealDB: {len(meals)} рецептов")
            
            if not meals:
                logger.warning("⚠️ TheMealDB не вернул рецептов для данного запроса")
                return []
            
            recipes = []
            for meal in meals:
                recipe = {
                    'id': meal['idMeal'],
                    'name': meal['strMeal'],
                    'image': meal['strMealThumb'],
                    'instructions': meal['strInstructions'],
                    'ingredients': self._extract_ingredients(meal),
                    'video': meal.get('strYoutube', ''),
                    'source': 'TheMealDB'
                }
                recipes.append(recipe)
            
            logger.info(f"✅ TheMealDB найдено {len(recipes)} рецептов")
            return recipes
            
        except Exception as e:
            logger.error(f"❌ Ошибка при поиске рецептов (TheMealDB): {e}")
            return []
    
    def search_recipes_spoonacular(self, query):
        """Поиск рецептов через Spoonacular API"""
        if not self.spoonacular_api_key:
            return []
        
        try:
            url = "https://api.spoonacular.com/recipes/complexSearch"
            params = {
                'apiKey': self.spoonacular_api_key,
                'query': query,
                'number': 10,
                'addRecipeInformation': True,
                'fillIngredients': True
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if 'results' not in data:
                return []
            
            recipes = []
            for recipe in data['results']:
                ingredients = []
                if 'extendedIngredients' in recipe:
                    for ingredient in recipe['extendedIngredients']:
                        ingredients.append({
                            'name': ingredient.get('name', ''),
                            'amount': ingredient.get('amount', ''),
                            'unit': ingredient.get('unit', '')
                        })
                
                recipe_data = {
                    'id': str(recipe['id']),
                    'name': recipe['title'],
                    'image': recipe.get('image', ''),
                    'instructions': recipe.get('instructions', ''),
                    'ingredients': ingredients,
                    'video': '',  # Spoonacular не предоставляет видео в базовом поиске
                    'source': 'Spoonacular'
                }
                recipes.append(recipe_data)
            
            return recipes
            
        except Exception as e:
            print(f"Ошибка при поиске рецептов (Spoonacular): {e}")
            return []
    
    def search_recipes(self, query):
        """Объединенный поиск рецептов с поддержкой перевода ru→en."""
        logger.info(f"🔍 Начинаем поиск рецептов для запроса: '{query}'")
        
        # Переводим запрос на английский, если он на русском
        query_en = self.translator.russian_to_english(query)
        logger.info(f"🔄 Переведенный запрос: '{query}' → '{query_en}'")

        recipes = []
        # Сначала пробуем TheMealDB (бесплатный)
        themedb_recipes = self.search_recipes_themedb(query_en)
        recipes.extend(themedb_recipes)

        # Если есть API ключ Spoonacular, добавляем и его результаты
        if self.spoonacular_api_key:
            logger.info("🔑 Используем Spoonacular API")
            spoonacular_recipes = self.search_recipes_spoonacular(query_en)
            recipes.extend(spoonacular_recipes)
        else:
            logger.info("⚠️ Spoonacular API ключ не настроен")

        # Ограничиваем количество результатов
        from config import MAX_RECIPES_PER_SEARCH
        if len(recipes) > MAX_RECIPES_PER_SEARCH:
            logger.info(f"✂️ Обрезаем результаты до {MAX_RECIPES_PER_SEARCH}")
            recipes = recipes[:MAX_RECIPES_PER_SEARCH]

        logger.info(f"📊 Всего найдено рецептов: {len(recipes)}")

        # Переводим данные рецептов обратно на русский для пользователя
        if recipes:
            logger.info("🔄 Начинаем перевод рецептов на русский язык")
            for i, recipe in enumerate(recipes):
                logger.info(f"   Перевод рецепта {i+1}: {recipe.get('name', 'Без названия')}")
                
                if recipe.get('name'):
                    original_name = recipe['name']
                    recipe['name'] = self.translator.english_to_russian(recipe['name'])
                    logger.info(f"     Название: '{original_name}' → '{recipe['name']}'")
                
                if recipe.get('instructions'):
                    recipe['instructions'] = self.translator.english_to_russian(recipe['instructions'])
                    logger.info(f"     Инструкции переведены")
                
                # Переводим ингредиенты
                if recipe.get('ingredients'):
                    translated_ingredients = []
                    for ing in recipe['ingredients']:
                        name = ing.get('name', '')
                        if name:
                            translated_name = self.translator.english_to_russian(name)
                            logger.info(f"     Ингредиент: '{name}' → '{translated_name}'")
                        else:
                            translated_name = name
                        translated_ingredients.append({
                            'name': translated_name,
                            'amount': ing.get('amount', ''),
                            'unit': ing.get('unit', '')
                        })
                    recipe['ingredients'] = translated_ingredients

        logger.info(f"✅ Поиск завершен. Возвращаем {len(recipes)} рецептов")
        return recipes
    
    def get_random_recipe(self):
        """Получение случайного рецепта"""
        try:
            url = f"{self.themealdb_url}/random.php"
            response = requests.get(url)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('meals') is None:
                return None
            
            meal = data['meals'][0]
            recipe = {
                'id': meal['idMeal'],
                'name': meal['strMeal'],
                'image': meal['strMealThumb'],
                'instructions': meal['strInstructions'],
                'ingredients': self._extract_ingredients(meal),
                'video': meal.get('strYoutube', ''),
                'source': 'TheMealDB'
            }
            
            return recipe
            
        except Exception as e:
            print(f"Ошибка при получении случайного рецепта: {e}")
            return None
    
    def _extract_ingredients(self, meal):
        """Извлечение ингредиентов из данных TheMealDB"""
        ingredients = []
        
        for i in range(1, 21):  # TheMealDB может иметь до 20 ингредиентов
            ingredient = meal.get(f'strIngredient{i}')
            measure = meal.get(f'strMeasure{i}')
            
            if ingredient and ingredient.strip():
                ingredients.append({
                    'name': ingredient.strip(),
                    'amount': measure.strip() if measure else '',
                    'unit': ''
                })
        
        return ingredients
    
    def get_recipe_by_id(self, recipe_id, source='TheMealDB'):
        """Получение рецепта по ID"""
        if source == 'TheMealDB':
            try:
                url = f"{self.themealdb_url}/lookup.php"
                params = {'i': recipe_id}
                
                response = requests.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                if data.get('meals') is None:
                    return None
                
                meal = data['meals'][0]
                recipe = {
                    'id': meal['idMeal'],
                    'name': meal['strMeal'],
                    'image': meal['strMealThumb'],
                    'instructions': meal['strInstructions'],
                    'ingredients': self._extract_ingredients(meal),
                    'video': meal.get('strYoutube', ''),
                    'source': 'TheMealDB'
                }
                
                return recipe
                
            except Exception as e:
                print(f"Ошибка при получении рецепта по ID: {e}")
                return None
        
        elif source == 'Spoonacular' and self.spoonacular_api_key:
            try:
                url = f"https://api.spoonacular.com/recipes/{recipe_id}/information"
                params = {'apiKey': self.spoonacular_api_key}
                
                response = requests.get(url, params=params)
                response.raise_for_status()
                
                recipe_data = response.json()
                
                ingredients = []
                if 'extendedIngredients' in recipe_data:
                    for ingredient in recipe_data['extendedIngredients']:
                        ingredients.append({
                            'name': ingredient.get('name', ''),
                            'amount': ingredient.get('amount', ''),
                            'unit': ingredient.get('unit', '')
                        })
                
                recipe = {
                    'id': str(recipe_data['id']),
                    'name': recipe_data['title'],
                    'image': recipe_data.get('image', ''),
                    'instructions': recipe_data.get('instructions', ''),
                    'ingredients': ingredients,
                    'video': '',
                    'source': 'Spoonacular'
                }
                
                return recipe
                
            except Exception as e:
                print(f"Ошибка при получении рецепта по ID (Spoonacular): {e}")
                return None
        
        return None
