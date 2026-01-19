"""Валидация артикулов и ссылок Wildberries."""

import re
import logging
from utils.exceptions import InvalidArticleError

logger = logging.getLogger(__name__)


class ArticleValidator:
    """Валидатор артикулов Wildberries."""

    # Паттерны для ссылок WB
    URL_PATTERNS = [
        r'wildberries\.ru/catalog/(\d+)/',
        r'wb\.ru/catalog/(\d+)/',
        r'wildberries\.ru.*?/(\d{6,10})/',
    ]

    @staticmethod
    def extract_article(text: str) -> str:
        """
        Извлекает артикул из текста (артикул или ссылка).

        Args:
            text: Артикул или ссылка на товар

        Returns:
            Артикул (nmId) в виде строки

        Raises:
            InvalidArticleError: Если формат неверный
        """
        text = text.strip()

        logger.debug(f"🔍 Попытка извлечения артикула из: '{text[:50]}'")

        # Проверка: просто артикул (6-10 цифр)
        if text.isdigit() and 6 <= len(text) <= 10:
            logger.debug(f"✅ Найден прямой артикул: {text}")
            return text

        # Проверка: ссылка
        for pattern in ArticleValidator.URL_PATTERNS:
            match = re.search(pattern, text)
            if match:
                article = match.group(1)
                if ArticleValidator.is_valid_article(article):
                    logger.debug(
                        f"✅ Артикул извлечен из URL по паттерну '{pattern}': {article}"
                    )
                    return article

        logger.warning(f"❌ Не удалось распознать артикул в тексте: '{text[:50]}'")
        raise InvalidArticleError(
            "❌ Неверный формат. Отправьте:\n"
            "• Артикул (например: 12345678)\n"
            "• Или ссылку на товар с Wildberries"
        )

    @staticmethod
    def is_valid_article(article: str) -> bool:
        """
        Проверка валидности артикула.

        Args:
            article: Артикул для проверки

        Returns:
            True если артикул валидный, False иначе
        """
        is_valid = article.isdigit() and 6 <= len(article) <= 10
        if not is_valid:
            logger.debug(f"❌ Невалидный артикул: {article} (не цифры или длина не 6-10)")
        return is_valid
