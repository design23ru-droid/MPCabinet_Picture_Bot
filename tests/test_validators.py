"""Тесты для utils/validators.py"""

import pytest
from utils.validators import ArticleValidator
from utils.exceptions import InvalidArticleError


class TestArticleValidator:
    """Тесты для ArticleValidator."""

    def test_extract_article_valid_6_digits(self):
        """Тест: валидный артикул 6 цифр."""
        result = ArticleValidator.extract_article("123456")
        assert result == "123456"

    def test_extract_article_valid_10_digits(self):
        """Тест: валидный артикул 10 цифр."""
        result = ArticleValidator.extract_article("1234567890")
        assert result == "1234567890"

    def test_extract_article_valid_8_digits(self):
        """Тест: валидный артикул 8 цифр (типичный)."""
        result = ArticleValidator.extract_article("12345678")
        assert result == "12345678"

    def test_extract_article_from_url_wildberries(self):
        """Тест: извлечение из ссылки wildberries.ru."""
        url = "https://www.wildberries.ru/catalog/12345678/detail.aspx"
        result = ArticleValidator.extract_article(url)
        assert result == "12345678"

    def test_extract_article_from_url_wb(self):
        """Тест: извлечение из ссылки wb.ru."""
        url = "https://wb.ru/catalog/87654321/detail.aspx"
        result = ArticleValidator.extract_article(url)
        assert result == "87654321"

    def test_extract_article_from_url_complex(self):
        """Тест: извлечение из сложной ссылки wildberries."""
        url = "https://wildberries.ru/product/test/365180/feedback"
        result = ArticleValidator.extract_article(url)
        assert result == "365180"

    def test_extract_article_whitespace_trimmed(self):
        """Тест: пробелы обрезаются."""
        result = ArticleValidator.extract_article("  12345678  ")
        assert result == "12345678"

    def test_extract_article_invalid_too_short(self):
        """Тест: артикул слишком короткий (5 цифр)."""
        with pytest.raises(InvalidArticleError):
            ArticleValidator.extract_article("12345")

    def test_extract_article_invalid_too_long(self):
        """Тест: артикул слишком длинный (11 цифр)."""
        with pytest.raises(InvalidArticleError):
            ArticleValidator.extract_article("12345678901")

    def test_extract_article_invalid_letters(self):
        """Тест: артикул содержит буквы."""
        with pytest.raises(InvalidArticleError):
            ArticleValidator.extract_article("abc12345")

    def test_extract_article_invalid_empty(self):
        """Тест: пустая строка."""
        with pytest.raises(InvalidArticleError):
            ArticleValidator.extract_article("")

    def test_extract_article_invalid_no_digits(self):
        """Тест: строка без цифр."""
        with pytest.raises(InvalidArticleError):
            ArticleValidator.extract_article("https://example.com/test")

    def test_is_valid_article_true_6_digits(self):
        """Тест: is_valid_article для валидного 6-значного артикула."""
        assert ArticleValidator.is_valid_article("123456") is True

    def test_is_valid_article_true_10_digits(self):
        """Тест: is_valid_article для валидного 10-значного артикула."""
        assert ArticleValidator.is_valid_article("1234567890") is True

    def test_is_valid_article_false_short(self):
        """Тест: is_valid_article для короткого артикула."""
        assert ArticleValidator.is_valid_article("12345") is False

    def test_is_valid_article_false_long(self):
        """Тест: is_valid_article для длинного артикула."""
        assert ArticleValidator.is_valid_article("12345678901") is False

    def test_is_valid_article_false_letters(self):
        """Тест: is_valid_article для артикула с буквами."""
        assert ArticleValidator.is_valid_article("abc12345") is False

    def test_is_valid_article_false_empty(self):
        """Тест: is_valid_article для пустой строки."""
        assert ArticleValidator.is_valid_article("") is False
