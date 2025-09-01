#!/usr/bin/env python3
"""
Тестирование переводчика
"""

from translator import TranslatorService

def test_translator():
    """Тестирование переводчика"""
    print("🔍 Тестирование переводчика...")
    
    translator = TranslatorService()
    
    # Тест перевода с русского на английский
    test_queries = [
        "курица",
        "пицца", 
        "суп",
        "салат",
        "торт",
        "хлеб"
    ]
    
    print("\n🇷🇺 → 🇺🇸 Перевод запросов:")
    for query in test_queries:
        translated = translator.russian_to_english(query)
        print(f"   '{query}' → '{translated}'")
    
    # Тест перевода с английского на русский
    test_english = [
        "Chicken Handi",
        "Pizza Express Margherita",
        "Leblebi Soup",
        "Salmon Avocado Salad",
        "Carrot Cake",
        "Bread omelette"
    ]
    
    print("\n🇺🇸 → 🇷🇺 Перевод названий блюд:")
    for name in test_english:
        translated = translator.english_to_russian(name)
        print(f"   '{name}' → '{translated}'")
    
    # Тест с пустым текстом
    print(f"\n🔍 Тест с пустым текстом:")
    empty_result = translator.russian_to_english("")
    print(f"   Пустой текст: '{empty_result}'")

if __name__ == "__main__":
    try:
        test_translator()
        print("\n✅ Тестирование переводчика завершено!")
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()
