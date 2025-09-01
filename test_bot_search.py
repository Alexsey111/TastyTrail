#!/usr/bin/env python3
"""
Тестирование поиска рецептов в боте
"""

from api_client import RecipeAPI
import json

def test_bot_search():
    """Тестирование поиска рецептов как в боте"""
    print("🔍 Тестирование поиска рецептов в боте...")
    
    api = RecipeAPI()
    
    # Тестовые запросы
    test_queries = [
        "курица",
        "chicken", 
        "pasta",
        "пицца",
        "pizza",
        "суп",
        "soup",
        "салат",
        "salad"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Поиск: '{query}'")
        
        # Поиск через TheMealDB
        themedb_recipes = api.search_recipes_themedb(query)
        print(f"   TheMealDB: {len(themedb_recipes)} рецептов")
        
        # Поиск через объединенный метод
        all_recipes = api.search_recipes(query)
        print(f"   Всего: {len(all_recipes)} рецептов")
        
        if all_recipes:
            print("   Первые 3 рецепта:")
            for i, recipe in enumerate(all_recipes[:3], 1):
                print(f"     {i}. {recipe['name']} (ID: {recipe['id']}, Источник: {recipe['source']})")
        else:
            print("   ❌ Рецепты не найдены")
    
    # Тест с пустым запросом
    print(f"\n🔍 Тест с пустым запросом:")
    empty_result = api.search_recipes("")
    print(f"   Результат: {len(empty_result)} рецептов")
    
    # Тест с очень длинным запросом
    print(f"\n🔍 Тест с длинным запросом:")
    long_query = "очень длинный запрос для поиска рецептов с множеством слов"
    long_result = api.search_recipes(long_query)
    print(f"   Результат: {len(long_result)} рецептов")

if __name__ == "__main__":
    try:
        test_bot_search()
        print("\n✅ Тестирование завершено!")
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()
