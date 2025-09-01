from typing import Optional

try:
    from deep_translator import GoogleTranslator
except Exception:  # Library not installed or other import-time failure
    GoogleTranslator = None  # type: ignore


class TranslatorService:
    """Lightweight wrapper around deep-translator with safe fallbacks.

    Provides ru→en and en→ru translations with graceful degradation
    when the translation engine is unavailable or errors occur.
    """

    def __init__(self) -> None:
        self._translator_en = None
        self._translator_ru = None
        if GoogleTranslator is not None:
            try:
                self._translator_en = GoogleTranslator(source='ru', target='en')
                self._translator_ru = GoogleTranslator(source='en', target='ru')
            except Exception:
                self._translator_en = None
                self._translator_ru = None

    def _translate(self, text: str, translator) -> Optional[str]:
        if not text or translator is None:
            return text
        try:
            return translator.translate(text)
        except Exception:
            return None

    def russian_to_english(self, text: str) -> str:
        translated = self._translate(text, self._translator_en)
        return translated if translated is not None else text

    def english_to_russian(self, text: str) -> str:
        translated = self._translate(text, self._translator_ru)
        return translated if translated is not None else text


