"""Кастомные исключения для бота."""


class WBBotException(Exception):
    """Базовое исключение для бота."""
    pass


class InvalidArticleError(WBBotException):
    """Неверный формат артикула."""
    pass


class ProductNotFoundError(WBBotException):
    """Товар не найден на Wildberries."""
    pass


class NoMediaError(WBBotException):
    """У товара нет медиафайлов."""
    pass


class WBAPIError(WBBotException):
    """Ошибка при работе с API Wildberries."""
    pass
