#!/usr/bin/env python3
"""
Тестирование API рецептов
"""

from api_client import RecipeAPI

def test_themedb_api():
    """Тестирование TheMealDB API"""
    print("🔍 Тестирование TheMealDB API...")
    
    api = RecipeAPI()
    
    # Тест поиска рецептов
    test_queries = ["pasta", "chicken", "beef", "fish", "salad", "cake", "bread", "soup"]
    
    for query in test_queries:
        print(f"\n1. Поиск рецептов '{query}':")
        recipes = api.search_recipes_themedb(query)
        if recipes:
            print(f"✅ Найдено {len(recipes)} рецептов")
            for i, recipe in enumerate(recipes[:3], 1):
                print(f"   {i}. {recipe['name']}")
        else:
            print("❌ Рецепты не найдены")
    
    # Тест случайного рецепта
    print("\n2. Случайный рецепт:")
    random_recipe = api.get_random_recipe()
    if random_recipe:
        print(f"✅ Случайный рецепт: {random_recipe['name']}")
        print(f"   Ингредиентов: {len(random_recipe['ingredients'])}")
        if random_recipe.get('video'):
            print(f"   Видеорецепт: {random_recipe['video']}")
    else:
        print("❌ Не удалось получить случайный рецепт")
    
    # Тест получения рецепта по ID
    print(f"\n3. Получение рецепта по ID {random_recipe['id']}:")
    recipe_by_id = api.get_recipe_by_id(random_recipe['id'])
    if recipe_by_id:
        print(f"✅ Рецепт найден: {recipe_by_id['name']}")
    else:
        print("❌ Рецепт не найден")

def test_spoonacular_api():
    """Тестирование Spoonacular API"""
    print("\n🔍 Тестирование Spoonacular API...")
    
    api = RecipeAPI()
    
    if not api.spoonacular_api_key:
        print("⚠️  Spoonacular API ключ не установлен")
        return
    
    # Тест поиска рецептов
    print("\n1. Поиск рецептов 'chicken':")
    recipes = api.search_recipes_spoonacular("chicken")
    if recipes:
        print(f"✅ Найдено {len(recipes)} рецептов")
        for i, recipe in enumerate(recipes[:3], 1):
            print(f"   {i}. {recipe['name']}")
    else:
        print("❌ Рецепты не найдены")

def test_combined_search():
    """Тестирование объединенного поиска"""
    print("\n🔍 Тестирование объединенного поиска...")
    
    api = RecipeAPI()
    
    print("\n1. Поиск 'pizza':")
    recipes = api.search_recipes("pizza")
    if recipes:
        print(f"✅ Найдено {len(recipes)} рецептов")
        sources = {}
        for recipe in recipes:
            source = recipe.get('source', 'Unknown')
            sources[source] = sources.get(source, 0) + 1
        
        for source, count in sources.items():
            print(f"   {source}: {count} рецептов")
    else:
        print("❌ Рецепты не найдены")

if __name__ == "__main__":
    print("🧪 Тестирование API рецептов\n")
    
    try:
        test_themedb_api()
        test_spoonacular_api()
        test_combined_search()
        
        print("\n✅ Тестирование завершено!")
        
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании: {e}")
