from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

class Keyboards:
    @staticmethod
    def get_main_menu():
        """Главное меню с основными действиями"""
        keyboard = [
            [KeyboardButton("🔍 Поиск рецептов")],
            [KeyboardButton("⭐ Мои избранные рецепты")],
            [KeyboardButton("🎲 Случайный рецепт")]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    
    @staticmethod
    def get_recipe_actions(recipe_id, is_favorite=False):
        """Кнопки действий для рецепта"""
        keyboard = []
        
        if is_favorite:
            keyboard.append([InlineKeyboardButton("❌ Удалить из избранного", callback_data=f"remove_favorite:{recipe_id}")])
        else:
            keyboard.append([InlineKeyboardButton("⭐ Добавить в избранное", callback_data=f"add_favorite:{recipe_id}")])
        
        keyboard.append([InlineKeyboardButton("📺 Видеорецепт", callback_data=f"video:{recipe_id}")])
        keyboard.append([InlineKeyboardButton("🔙 Назад к поиску", callback_data="back_to_search")])
        keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_rating_keyboard(recipe_id):
        """Клавиатура для оценки рецепта"""
        keyboard = []
        rating_row = []
        
        for i in range(1, 6):
            rating_row.append(InlineKeyboardButton(f"{'⭐' * i}", callback_data=f"rate:{recipe_id}:{i}"))
        
        keyboard.append(rating_row)
        keyboard.append([InlineKeyboardButton("❌ Пропустить", callback_data=f"skip_rating:{recipe_id}")])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_favorite_recipe_actions(recipe_id, rating=0):
        """Кнопки действий для избранного рецепта"""
        keyboard = []
        
        # Показываем текущий рейтинг
        if rating > 0:
            keyboard.append([InlineKeyboardButton(f"Рейтинг: {'⭐' * rating}", callback_data="show_rating")])
        
        keyboard.append([InlineKeyboardButton("⭐ Изменить рейтинг", callback_data=f"change_rating:{recipe_id}")])
        keyboard.append([InlineKeyboardButton("❌ Удалить из избранного", callback_data=f"remove_favorite:{recipe_id}")])
        keyboard.append([InlineKeyboardButton("📺 Видеорецепт", callback_data=f"video:{recipe_id}")])
        keyboard.append([InlineKeyboardButton("🔙 Назад к избранному", callback_data="back_to_favorites")])
        keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_search_results_navigation(current_page, total_pages, recipe_id):
        keyboard = []
        nav_row = []
        
        if current_page > 0:
            nav_row.append(InlineKeyboardButton("⬅️", callback_data=f"prev_page:{current_page}"))
        
        nav_row.append(InlineKeyboardButton(f"{current_page + 1}/{total_pages}", callback_data="page_info"))
        
        if current_page < total_pages - 1:
            nav_row.append(InlineKeyboardButton("➡️", callback_data=f"next_page:{current_page + 1}"))
        
        keyboard.append(nav_row)
        
        keyboard.append([InlineKeyboardButton("⭐ Добавить в избранное", callback_data=f"add_favorite:{recipe_id}")])
        keyboard.append([InlineKeyboardButton("📺 Видеорецепт", callback_data=f"video:{recipe_id}")])
        keyboard.append([InlineKeyboardButton("🔙 Новый поиск", callback_data="new_search")])
        keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_favorites_navigation(current_page, total_pages, recipe_id):
        keyboard = []
        nav_row = []
        
        if current_page > 0:
            nav_row.append(InlineKeyboardButton("⬅️", callback_data=f"prev_fav_page:{current_page}"))
        
        nav_row.append(InlineKeyboardButton(f"{current_page + 1}/{total_pages}", callback_data="fav_page_info"))
        
        if current_page < total_pages - 1:
            nav_row.append(InlineKeyboardButton("➡️", callback_data=f"next_fav_page:{current_page + 1}"))
        
        keyboard.append(nav_row)
        
        keyboard.append([InlineKeyboardButton("🔍 Подробнее", callback_data=f"view_fav:{recipe_id}")])
        keyboard.append([InlineKeyboardButton("⭐ Изменить рейтинг", callback_data=f"change_rating:{recipe_id}")])
        keyboard.append([InlineKeyboardButton("❌ Удалить из избранного", callback_data=f"remove_favorite:{recipe_id}")])
        keyboard.append([InlineKeyboardButton("📺 Видеорецепт", callback_data=f"video:{recipe_id}")])
        keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_cancel_keyboard():
        """Кнопка отмены"""
        keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="cancel")]]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_help_keyboard():
        """Клавиатура для справки"""
        keyboard = [
            [InlineKeyboardButton("🔍 Как искать рецепты", callback_data="help_search")],
            [InlineKeyboardButton("⭐ Как добавить в избранное", callback_data="help_favorites")],
            [InlineKeyboardButton("⭐ Как оценить рецепт", callback_data="help_rating")],
            [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
