import sqlite3
import json
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.db_name = "recipes.db"  # Убедись, что DATABASE_NAME = "recipes.db"
        self.init_database()

    def init_database(self):
        """Инициализация базы данных и создание таблиц"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()

                # Таблица для избранных рецептов
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS favorite_recipes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        recipe_id TEXT NOT NULL,
                        recipe_name TEXT NOT NULL,
                        recipe_image TEXT,
                        recipe_instructions TEXT,
                        recipe_ingredients TEXT,
                        recipe_video TEXT,
                        rating INTEGER DEFAULT 0,
                        added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(user_id, recipe_id)
                    )
                ''')

                conn.commit()
                logger.info("База данных инициализирована.")
        except Exception as e:
            logger.error(f"Ошибка при инициализации базы данных: {e}")

    def add_favorite_recipe(self, user_id, recipe_data):
        """Добавление рецепта в избранное"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()

                # Преобразуем ингредиенты в JSON с поддержкой кириллицы
                ingredients_json = json.dumps(recipe_data.get('ingredients', []), ensure_ascii=False)

                cursor.execute('''
                    INSERT OR REPLACE INTO favorite_recipes 
                    (user_id, recipe_id, recipe_name, recipe_image, recipe_instructions, 
                     recipe_ingredients, recipe_video, rating)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id,
                    recipe_data['id'],
                    recipe_data['name'],
                    recipe_data.get('image', ''),
                    recipe_data.get('instructions', ''),
                    ingredients_json,
                    recipe_data.get('video', ''),
                    0  # Новый рецепт — рейтинг 0
                ))

                conn.commit()
                logger.info(f"Рецепт {recipe_data['id']} добавлен в избранное для пользователя {user_id}")
                return True
        except Exception as e:
            logger.error(f"Ошибка при добавлении рецепта в избранное: {e}")
            return False

    def get_favorite_recipes(self, user_id):
        """Получение избранных рецептов пользователя, отсортированных по рейтингу"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT recipe_id, recipe_name, recipe_image, recipe_instructions, 
                           recipe_ingredients, recipe_video, rating, added_date
                    FROM favorite_recipes 
                    WHERE user_id = ?
                    ORDER BY rating DESC, added_date DESC
                ''', (user_id,))

                recipes = []
                for row in cursor.fetchall():
                    try:
                        # Парсим ингредиенты с защитой от ошибок
                        try:
                            ingredients = json.loads(row[4]) if row[4] else []
                        except (json.JSONDecodeError, TypeError):
                            logger.warning(f"Некорректный JSON в ingredients для рецепта {row[0]}")
                            ingredients = []

                        recipe = {
                            'id': row[0],
                            'name': row[1],
                            'image': row[2],
                            'instructions': row[3],
                            'ingredients': ingredients,
                            'video': row[5],
                            'rating': row[6],
                            'added_date': row[7]
                        }
                        recipes.append(recipe)
                    except Exception as e:
                        logger.error(f"Ошибка при обработке строки рецепта {row[0]}: {e}")
                        continue  # Пропускаем битые записи

                logger.info(f"Загружено {len(recipes)} избранных рецептов для пользователя {user_id}")
                return recipes
        except Exception as e:
            logger.error(f"Ошибка при получении избранных рецептов: {e}")
            return []

    def update_recipe_rating(self, user_id, recipe_id, rating):
        """Обновление рейтинга рецепта"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    UPDATE favorite_recipes 
                    SET rating = ?
                    WHERE user_id = ? AND recipe_id = ?
                ''', (rating, user_id, recipe_id))

                conn.commit()
                if cursor.rowcount > 0:
                    logger.info(f"Рецепт {recipe_id} оценён на {rating} звёзд пользователем {user_id}")
                    return True
                else:
                    logger.warning(f"Рецепт {recipe_id} не найден для обновления рейтинга")
                    return False
        except Exception as e:
            logger.error(f"Ошибка при обновлении рейтинга: {e}")
            return False

    def remove_favorite_recipe(self, user_id, recipe_id):
        """Удаление рецепта из избранного"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    DELETE FROM favorite_recipes 
                    WHERE user_id = ? AND recipe_id = ?
                ''', (user_id, recipe_id))

                conn.commit()
                if cursor.rowcount > 0:
                    logger.info(f"Рецепт {recipe_id} удалён из избранного для пользователя {user_id}")
                    return True
                else:
                    logger.warning(f"Рецепт {recipe_id} не найден в избранном пользователя {user_id}")
                    return False
        except Exception as e:
            logger.error(f"Ошибка при удалении рецепта: {e}")
            return False

    def is_recipe_favorite(self, user_id, recipe_id):
        """Проверка, находится ли рецепт в избранном"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT 1 FROM favorite_recipes 
                    WHERE user_id = ? AND recipe_id = ?
                    LIMIT 1
                ''', (user_id, recipe_id))

                return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Ошибка при проверке избранного: {e}")
            return False