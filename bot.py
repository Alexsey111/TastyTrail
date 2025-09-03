import logging
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes, ConversationHandler
from config import TELEGRAM_TOKEN
from database import Database
from api_client import RecipeAPI
from keyboards import Keyboards
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
WAITING_FOR_SEARCH_QUERY = 1

class RecipeBot:
    def __init__(self):
        self.db = Database()
        self.api = RecipeAPI()
        self.keyboards = Keyboards()
        
        # Хранилище состояния пользователей
        self.user_states = {}  # {user_id: {'search_results': [], 'current_page': 0, 'favorites': [], 'fav_page': 0}}
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        welcome_text = f"""
🍽️ Привет, {user.first_name}! 

Я бот для поиска рецептов блюд. Вот что я умею:

🔍 **Поиск рецептов** - найду рецепты по вашему запросу
⭐ **Избранные рецепты** - сохраните понравившиеся рецепты
🎲 **Случайный рецепт** - предложу случайное блюдо
⭐ **Рейтинг** - оценивайте избранные рецепты от 1 до 5 звезд
📺 **Видеорецепты** - ссылки на видео приготовления

Выберите действие:
        """
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=self.keyboards.get_main_menu()
        )
    
    async def handle_search_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начало поиска рецептов"""
        await update.message.reply_text(
            "Введите название блюда или ингредиент для поиска:",
            reply_markup=self.keyboards.get_cancel_keyboard()
        )
        return WAITING_FOR_SEARCH_QUERY

    async def handle_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик главного меню"""
        text = update.message.text
        logger.info(f"Главное меню: получен текст '{text}' от пользователя {update.effective_user.id}")
        user_id = update.effective_user.id
        
        if text == "🔍 Поиск рецептов":
            await update.message.reply_text(
                "Введите название блюда или ингредиент для поиска:",
                reply_markup=self.keyboards.get_cancel_keyboard()
            )
            return WAITING_FOR_SEARCH_QUERY
        
        elif text == "⭐ Мои избранные рецепты":
            await self.show_favorites(update, context)
            return ConversationHandler.END
        
        elif text == "🎲 Случайный рецепт":
            await self.show_random_recipe(update, context)
            return ConversationHandler.END
        
        # Любой другой текст трактуем как запрос для поиска
        logger.info("Трактуем введенный текст как поисковый запрос")
        return await self.search_recipes(update, context)
    
    async def search_recipes(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Поиск рецептов"""
        query = update.message.text
        user_id = update.effective_user.id
        
        # Показываем пользователю, что идет обработка запроса
        try:
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
        except Exception:
            pass
        await update.message.reply_text("🔍 Ищу рецепты...")
        
        # Поиск рецептов через API
        try:
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
        except Exception:
            pass
        recipes = self.api.search_recipes(query)
        
        if not recipes:
            await update.message.reply_text(
                f"😔 По запросу '{query}' ничего не найдено.\nПопробуйте другой запрос:",
                reply_markup=self.keyboards.get_cancel_keyboard()
            )
            return WAITING_FOR_SEARCH_QUERY
        
        # Сохраняем результаты поиска
        self.user_states[user_id] = {
            'search_results': recipes,
            'current_page': 0,
            'favorites': [],
            'fav_page': 0
        }
        
        # Показываем первый рецепт
        await self.show_recipe(update, context, recipes[0], is_search=True)
        return ConversationHandler.END
    
    async def show_recipe(self, update: Update, context: ContextTypes.DEFAULT_TYPE, recipe, is_search=False, is_favorite=False):
        """Показать рецепт"""
        user_id = update.effective_user.id

        # Формируем текст рецепта
        recipe_text = f"""
    🍽️ **{recipe['name']}**

    📝 **Ингредиенты:**
    """

        for ingredient in recipe['ingredients']:
            if ingredient.get('amount') and ingredient.get('unit'):
                recipe_text += f"• {ingredient['amount']} {ingredient['unit']} {ingredient['name']}\n"
            elif ingredient.get('amount'):
                recipe_text += f"• {ingredient['amount']} {ingredient['name']}\n"
            else:
                recipe_text += f"• {ingredient['name']}\n"

        recipe_text += f"""
    📋 **Инструкция:**
    {recipe['instructions']}

    """

        if recipe.get('video'):
            recipe_text += f"📺 **Видеорецепт:** {recipe['video']}\n\n"

        # Проверяем, находится ли рецепт в избранном
        is_in_favorites = self.db.is_recipe_favorite(user_id, recipe['id'])

        # Выбираем клавиатуру
        if is_search:
            user_state = self.user_states.get(user_id, {})
            current_page = user_state.get('current_page', 0)
            total_pages = len(user_state.get('search_results', [])) or 1
            keyboard = self.keyboards.get_search_results_navigation(current_page, total_pages, recipe['id'])
        elif is_favorite:
            rating = 0
            favorites = self.user_states.get(user_id, {}).get('favorites', [])
            for fav in favorites:
                if fav['id'] == recipe['id']:
                    rating = fav.get('rating', 0)
                    break
            keyboard = self.keyboards.get_favorite_recipe_actions(recipe['id'], rating)
        else:
            keyboard = self.keyboards.get_recipe_actions(recipe['id'], is_in_favorites)

        # Ограничиваем длину подписи
        if len(recipe_text) > 1000:
            recipe_caption = recipe_text[:1000] + "...\n\n(Описание сокращено)"
        else:
            recipe_caption = recipe_text

        # Отправляем фото с подписью
        if recipe.get('image'):
            try:
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=recipe['image'],
                    caption=recipe_caption,
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
            except Exception as e:
                logger.error(f"Ошибка при отправке фото: {e}")
                # Резерв: отправляем текст отдельно
                await update.message.reply_text(
                    "🖼️ Фото недоступно, но вот рецепт:",
                    parse_mode='HTML'
                )
                await update.message.reply_text(
                    recipe_text,
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
        else:
            await update.message.reply_text(
                recipe_text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )

    def _format_recipe_caption(self, recipe):
        caption = f"🍽️ **{recipe['name']}**\n\n"
        
        caption += "**📝 Ингредиенты:**\n"
        for ingr in recipe['ingredients'][:8]:
            name = ingr.get('name', 'неизвестно')
            amount = ingr.get('amount', '')
            unit = ingr.get('unit', '')
            if amount and unit:
                caption += f"• {amount} {unit} {name}\n"
            elif amount:
                caption += f"• {amount} {name}\n"
            else:
                caption += f"• {name}\n"
        
        if len(recipe['ingredients']) > 8:
            caption += "• и ещё...\n"
        
        caption += f"\n**📋 Инструкция:**\n{recipe['instructions'][:300]}...\n"
        
        if recipe.get('video'):
            caption += "\n📺 Нажмите 'Видеорецепт' для просмотра"
        
        return caption[:1000] + "..." if len(caption) > 1000 else caption

    def get_favorites_navigation_keyboard(self, current_page: int, total_pages: int, recipe_id: str):
        """Клавиатура навигации по избранным"""
        buttons = []

        # Кнопки "Назад" / "Вперёд"
        if current_page > 0:
            buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"prev_fav_page:{current_page}"))
        if current_page < total_pages - 1:
            buttons.append(InlineKeyboardButton("Вперёд ➡️", callback_data=f"next_fav_page:{current_page}"))

        # Кнопка "Подробнее"
        buttons.append([InlineKeyboardButton("🔍 Подробнее", callback_data=f"view_fav:{recipe_id}")])

        # Кнопка "В меню"
        buttons.append([InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")])

        return InlineKeyboardMarkup(buttons)

    async def show_favorites(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать избранные рецепты — с навигацией"""
        user_id = update.effective_user.id
        favorites = self.db.get_favorite_recipes(user_id)

        if not favorites:
            await update.message.reply_text(
                "⭐ У вас пока нет избранных рецептов.\nНайдите рецепт и добавьте его!",
                reply_markup=self.keyboards.get_main_menu()
            )
            return

        # Сохраняем в состояние
        if user_id not in self.user_states:
            self.user_states[user_id] = {}
        self.user_states[user_id]['favorites'] = favorites
        self.user_states[user_id]['fav_page'] = 0  # ← начинаем с 0

        # Показываем первый рецепт с навигацией
        await self.show_favorite_with_navigation(update, context, 0)
    
    async def show_favorite_with_navigation(self, update: Update, context: ContextTypes.DEFAULT_TYPE, page: int):
        """Показать избранный рецепт с навигацией"""
        user_id = update.effective_user.id
        favorites = self.user_states.get(user_id, {}).get('favorites', [])

        if not favorites:
            await update.message.reply_text("Нет избранных рецептов.")
            return

        if page < 0 or page >= len(favorites):
            return

        # Обновляем текущую страницу
        self.user_states[user_id]['fav_page'] = page
        recipe = favorites[page]

        # Формируем подпись
        caption = f"[{page + 1}/{len(favorites)}] 🍽️ **{recipe['name']}**\n\n"
        caption += f"⭐ Рейтинг: {recipe.get('rating', 0)}\n\n"
        caption += f"📝 Ингредиентов: {len(recipe['ingredients'])}\n"
        caption += "Нажмите 'Подробнее' для просмотра."

        # Клавиатура: навигация + действия
        keyboard = self.keyboards.get_favorites_navigation(
            current_page=page,
            total_pages=len(favorites),
            recipe_id=recipe['id']
        )


        # Отправляем фото
        if recipe.get('image'):
            try:
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=recipe['image'],
                    caption=caption,
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
            except Exception as e:
                logger.error(f"Ошибка отправки фото: {e}")
                await update.message.reply_text(caption, reply_markup=keyboard, parse_mode='HTML')
        else:
            await update.message.reply_text(caption, reply_markup=keyboard, parse_mode='HTML')
    
    async def show_random_recipe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать случайный рецепт"""
        await update.message.reply_text("🎲 Ищу случайный рецепт...")
        
        recipe = self.api.get_random_recipe()
        
        if not recipe:
            await update.message.reply_text(
                "😔 Не удалось получить случайный рецепт. Попробуйте позже.",
                reply_markup=self.keyboards.get_main_menu()
            )
            return
        
        await self.show_recipe(update, context, recipe)
    
    async def show_favorite_detail(self, update: Update, context: ContextTypes.DEFAULT_TYPE, recipe_id: str):
        """Показать полную информацию о рецепте из избранного"""
        user_id = update.effective_user.id
        favorites = self.user_states.get(user_id, {}).get('favorites', [])
        
        recipe = next((r for r in favorites if r['id'] == recipe_id), None)
        if not recipe:
            await update.callback_query.answer("❌ Рецепт не найден.")
            return

        # Формируем подпись
        caption = f"""
    🍽️ **{recipe['name']}**

    📝 **Ингредиенты:**
    """
        for ingr in recipe['ingredients'][:8]:
            name = ingr.get('name', '')
            amount = ingr.get('amount', '')
            unit = ingr.get('unit', '')
            if amount and unit:
                caption += f"• {amount} {unit} {name}\n"
            elif amount:
                caption += f"• {amount} {name}\n"
            else:
                caption += f"• {name}\n"

        if len(recipe['ingredients']) > 8:
            caption += "• и ещё...\n"

        caption += f"""
    📋 **Инструкция:**
    {recipe['instructions'][:300]}...

    """
        if recipe.get('video'):
            caption += f"📺 **Видеорецепт:** {recipe['video']}\n"

        # Обрезаем подпись
        if len(caption) > 1024:
            caption = caption[:1000] + "...\n\n(Описание сокращено)"

        # Клавиатура
        keyboard = self.keyboards.get_favorite_recipe_actions(recipe_id, recipe.get('rating', 0))

        try:
            await update.callback_query.edit_message_caption(
                caption=caption,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Ошибка при отображении деталей: {e}")

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик callback запросов"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        data = query.data
        
        if data.startswith("add_favorite:"):
            await self.add_to_favorites(update, context, data.split(":")[1])
        
        elif data.startswith("remove_favorite:"):
            await self.remove_from_favorites(update, context, data.split(":")[1])
        
        elif data.startswith("rate:"):
            parts = data.split(":")
            recipe_id = parts[1]
            rating = int(parts[2])
            await self.rate_recipe(update, context, recipe_id, rating)
        
        elif data.startswith("change_rating:"):
            recipe_id = data.split(":")[1]
            await self.show_rating_keyboard(update, context, recipe_id)
        
        elif data.startswith("skip_rating:"):
            await self.skip_rating(update, context)
        
        elif data.startswith("video:"):
            recipe_id = data.split(":")[1]
            await self.show_video(update, context, recipe_id)
        
        elif data == "back_to_search":
            await self.back_to_search(update, context)
        
        elif data == "back_to_favorites":
            await self.back_to_favorites(update, context)
        
        elif data == "main_menu":
            await self.back_to_main_menu(update, context)
        
        elif data == "new_search":
            await self.new_search(update, context)
        
        elif data.startswith("prev_page:"):
            page = int(data.split(":")[1])
            await self.navigate_search_results(update, context, page - 1)
        
        elif data.startswith("next_page:"):
            page = int(data.split(":")[1])
            await self.navigate_search_results(update, context, page + 1)
        
        elif data.startswith("prev_fav_page:"):
            page = int(data.split(":")[1])
            await self.navigate_favorites(update, context, page - 1)
        
        elif data.startswith("next_fav_page:"):
            page = int(data.split(":")[1])
            await self.navigate_favorites(update, context, page + 1)
        
        elif data.startswith("view_fav:"):
            recipe_id = data.split(":")[1]
            await self.show_favorite_detail(update, context, recipe_id)
    
    async def add_to_favorites(self, update: Update, context: ContextTypes.DEFAULT_TYPE, recipe_id):
        user_id = update.effective_user.id
        recipe = self.api.get_recipe_by_id(recipe_id)
        if not recipe:
            await update.callback_query.answer("❌ Рецепт не найден.")
            return

        if self.db.is_recipe_favorite(user_id, recipe_id):
            await update.callback_query.answer("Уже в избранном!")
            return

        if self.db.add_favorite_recipe(user_id, recipe):
            await update.callback_query.edit_message_caption(
                caption="✅ Добавлено в избранное! Оцените блюдо:",
                reply_markup=self.keyboards.get_rating_keyboard(recipe_id),
                parse_mode='HTML'
            )
        else:
            await update.callback_query.answer("Ошибка сохранения.")
    
    async def remove_from_favorites(self, update: Update, context: ContextTypes.DEFAULT_TYPE, recipe_id):
        """Удалить рецепт из избранного"""
        user_id = update.effective_user.id
        success = self.db.remove_favorite_recipe(user_id, recipe_id)

        if success:
            try:
                await update.callback_query.edit_message_caption(
                    caption="✅ Рецепт удален из избранного.",
                    reply_markup=None
                )
            except Exception as e:
                logger.error(f"Ошибка: {e}")
        else:
            await update.callback_query.answer("❌ Ошибка при удалении.")
    
    async def rate_recipe(self, update: Update, context: ContextTypes.DEFAULT_TYPE, recipe_id, rating):
        user_id = update.effective_user.id
        success = self.db.update_recipe_rating(user_id, recipe_id, rating)
        
        if success:
            # Получаем обновлённый рецепт
            recipe = self.api.get_recipe_by_id(recipe_id)
            if not recipe:
                await update.callback_query.answer("❌ Рецепт не найден.")
                return

            # Обновляем рейтинг в объекте
            recipe['rating'] = rating

            # Формируем подпись
            caption = f"⭐ Вы оценили рецепт на {rating} звёзд!\n\n{self._format_recipe_caption(recipe)}"

            # Обновляем подпись и клавиатуру
            try:
                await update.callback_query.edit_message_caption(
                    caption=caption,
                    reply_markup=self.keyboards.get_favorite_recipe_actions(recipe_id, rating),
                    parse_mode='HTML'
                )
                await update.callback_query.answer("Оценка сохранена!")
            except Exception as e:
                logger.error(f"Ошибка при обновлении: {e}")
                await update.callback_query.answer("Оценка сохранена, но интерфейс не обновился.")
        else:
            await update.callback_query.answer("❌ Ошибка при оценке.")

    async def skip_rating(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            await update.callback_query.edit_message_caption(
                caption="Оценка пропущена.",
                reply_markup=None
            )
        except Exception as e:
            logger.error(f"Ошибка: {e}")

    async def show_video(self, update: Update, context: ContextTypes.DEFAULT_TYPE, recipe_id):
        recipe = self.api.get_recipe_by_id(recipe_id)
        if recipe and recipe.get('video'):
            video_link = recipe['video']
            try:
                await update.callback_query.edit_message_caption(
                    caption=f"📺 **Видеорецепт:**\n{video_link}",
                    parse_mode='HTML'
                )
            except Exception as e:
                logger.error(f"Ошибка: {e}")
        else:
            await update.callback_query.answer("📺 Видеорецепт недоступен.")
        
    async def navigate_search_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE, page):
        """Навигация по результатам поиска"""
        user_id = update.effective_user.id
        user_state = self.user_states.get(user_id, {})
        search_results = user_state.get('search_results', [])
        
        if 0 <= page < len(search_results):
            user_state['current_page'] = page
            recipe = search_results[page]
            
            await self.update_recipe_message(update, context, recipe, is_search=True)
    
    async def navigate_favorites(self, update: Update, context: ContextTypes.DEFAULT_TYPE, page):
        """Навигация по избранным рецептам"""
        user_id = update.effective_user.id
        user_state = self.user_states.get(user_id, {})
        favorites = user_state.get('favorites', [])
        
        if 0 <= page < len(favorites):
            user_state['fav_page'] = page
            recipe = favorites[page]
            
            await self.show_favorite_with_navigation(update, context, page)
    
    async def update_recipe_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE, recipe, is_search=False, is_favorite=False):
        """Обновить сообщение с рецептом (универсально)"""
        user_id = update.effective_user.id

        # Формируем текст
        recipe_text = f"""
    🍽️ **{recipe['name']}**

    📝 **Ингредиенты:**
    """
        for ingredient in recipe['ingredients']:
            if ingredient.get('amount') and ingredient.get('unit'):
                recipe_text += f"• {ingredient['amount']} {ingredient['unit']} {ingredient['name']}\n"
            elif ingredient.get('amount'):
                recipe_text += f"• {ingredient['amount']} {ingredient['name']}\n"
            else:
                recipe_text += f"• {ingredient['name']}\n"

        recipe_text += f"""
    📋 **Инструкция:**
    {recipe['instructions']}

    """
        if recipe.get('video'):
            recipe_text += f"📺 **Видеорецепт:** {recipe['video']}\n\n"

        # Обрезаем подпись
        caption = recipe_text[:1000] + "..." if len(recipe_text) > 1000 else recipe_text

        # Клавиатура
        if is_favorite:
            rating = recipe.get('rating', 0)
            keyboard = self.keyboards.get_favorite_recipe_actions(recipe['id'], rating)
        else:
            is_in_fav = self.db.is_recipe_favorite(user_id, recipe['id'])
            keyboard = self.keyboards.get_recipe_actions(recipe['id'], is_in_fav)

        # Попробуем сначала изменить подпись
        try:
            await update.callback_query.edit_message_caption(
                caption=caption,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
        except Exception as e:
            if "message is not modified" in str(e):
                pass
            else:
                logger.error(f"Ошибка при редактировании подписи: {e}")
                # Если не получилось — пробуем изменить текст
                try:
                    await update.callback_query.edit_message_text(
                        text=caption,
                        reply_markup=keyboard,
                        parse_mode='HTML'
                    )
                except Exception as e2:
                    logger.error(f"Не удалось отредактировать сообщение: {e2}")
    
    async def back_to_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Вернуться к поиску — удаляем и отправляем текст"""
        query = update.callback_query
        await query.answer()

        try:
            await query.delete_message()
        except Exception as e:
            logger.error(f"Ошибка удаления: {e}")

        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Введите название блюда или ингредиент для поиска:",
                reply_markup=self.keyboards.get_cancel_keyboard(),
                parse_mode='HTML'
            )
            return WAITING_FOR_SEARCH_QUERY
        except Exception as e:
            logger.error(f"Ошибка: {e}")
    
    async def back_to_favorites(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Вернуться к избранному"""
        await self.show_favorites(update, context)
    
    async def back_to_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Вернуться в главное меню — безопасно: удаляем и отправляем заново"""
        query = update.callback_query
        await query.answer()

        try:
            # Сначала удаляем текущее сообщение (фото с подписью)
            await query.delete_message()
        except Exception as e:
            logger.error(f"Не удалось удалить сообщение: {e}")
            # Если не получилось — хотя бы закрываем callback
            return

        # Теперь отправляем новое сообщение с главным меню
        user = update.effective_user
        welcome_text = f"""
    🍽️ Привет, {user.first_name}!  

    Выберите действие:
        """
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=welcome_text,
                reply_markup=self.keyboards.get_main_menu(),
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Ошибка при отправке главного меню: {e}")
    
    async def new_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Новый поиск"""
        await update.callback_query.edit_message_text(
            "Введите название блюда или ингредиент для поиска:",
            reply_markup=self.keyboards.get_cancel_keyboard()
        )
        return WAITING_FOR_SEARCH_QUERY
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отмена операции"""
        await update.message.reply_text(
            "Операция отменена. Выберите действие:",
            reply_markup=self.keyboards.get_main_menu()
        )
        return ConversationHandler.END
    
    def run(self):
        """Запуск бота"""
        if not TELEGRAM_TOKEN:
            logger.error("Не установлен TELEGRAM_TOKEN в переменных окружения!")
            return
        
        # Создаем приложение
        application = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # Создаем ConversationHandler только для поиска
        conv_handler = ConversationHandler(
            entry_points=[
                MessageHandler(filters.Regex("^🔍 Поиск рецептов$"), self.handle_search_start)
            ],
            states={
                WAITING_FOR_SEARCH_QUERY: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.search_recipes),
                    CallbackQueryHandler(self.handle_callback, pattern="^cancel$")
                ]
            },
            fallbacks=[
                CommandHandler("cancel", self.cancel),
                MessageHandler(filters.COMMAND, self.cancel)
            ],
            per_message=True  # ← Это важно для callback-кнопок
        )
        
        # Добавляем обработчики
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(conv_handler)
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_main_menu))
        application.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # Запускаем бота
        logger.info("Бот запущен...")
        try:
            application.run_polling(allowed_updates=Update.ALL_TYPES)
        except Exception as e:
            logger.error(f"Ошибка при запуске polling: {e}")
            # Альтернативный способ запуска
            application.run_polling()

if __name__ == "__main__":
    bot = RecipeBot()
    bot.run()
