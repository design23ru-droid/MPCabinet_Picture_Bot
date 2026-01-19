"""Точка входа Telegram бота для парсинга медиа с Wildberries."""

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config.settings import Settings
from utils.logger import setup_logger
from bot.handlers import start, article, callbacks
from bot.middlewares.error_handler import ErrorHandlerMiddleware


async def main():
    """Точка входа приложения."""
    # Настройка логирования
    setup_logger()
    logger = logging.getLogger(__name__)

    # Загрузка конфигурации
    try:
        settings = Settings()
    except Exception as e:
        logger.critical(f"Failed to load settings: {e}")
        logger.critical("Make sure you have .env file with BOT_TOKEN")
        return

    # Инициализация бота
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    # Инициализация диспетчера
    dp = Dispatcher()

    # Регистрация middleware
    dp.message.middleware(ErrorHandlerMiddleware())
    dp.callback_query.middleware(ErrorHandlerMiddleware())

    # Регистрация роутеров (порядок важен!)
    dp.include_router(start.router)      # /start, /help
    dp.include_router(callbacks.router)  # callback queries
    dp.include_router(article.router)    # fallback для текста (в конце!)

    logger.info("Bot starting...")
    logger.info(f"Log level: {settings.LOG_LEVEL}")
    logger.info(f"WB API timeout: {settings.WB_API_TIMEOUT}s")
    logger.info(f"WB rate limit delay: {settings.WB_RATE_LIMIT_DELAY}s")

    try:
        # Удаляем webhook (для long polling)
        await bot.delete_webhook(drop_pending_updates=True)

        # Запуск long polling
        logger.info("Starting long polling...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.critical(f"Fatal error: {e}")
    finally:
        await bot.session.close()
        logger.info("Bot stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user")
