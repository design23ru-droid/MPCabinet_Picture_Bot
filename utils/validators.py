"""Валидация артикулов и ссылок Wildberries."""

import re
from utils.exceptions import InvalidArticleError


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

        # Проверка: просто артикул (6-10 цифр)
        if text.isdigit() and 6 <= len(text) <= 10:
            return text

        # Проверка: ссылка
        for pattern in ArticleValidator.URL_PATTERNS:
            match = re.search(pattern, text)
            if match:
                article = match.group(1)
                if ArticleValidator.is_valid_article(article):
                    return article

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
        return article.isdigit() and 6 <= len(article) <= 10
