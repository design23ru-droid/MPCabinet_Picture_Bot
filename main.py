"""Точка входа Telegram бота для парсинга медиа с Wildberries."""

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.enums import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

from config.settings import Settings
from utils.logger import setup_logger
from bot.handlers import start, article, callbacks
from bot.middlewares.error_handler import ErrorHandlerMiddleware
from bot.middlewares.rate_limiter import RateLimiterMiddleware
from services.digest import send_daily_digest_job
from db.connection import get_pool, close_pool


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

    # Инициализация бота (с поддержкой Local Bot API)
    session = None
    if settings.TELEGRAM_API_BASE_URL:
        api_server = TelegramAPIServer.from_base(
            base=settings.TELEGRAM_API_BASE_URL,
            is_local=settings.TELEGRAM_API_LOCAL
        )
        session = AiohttpSession(api=api_server)
        logger.info(f"Using Local Bot API: {settings.TELEGRAM_API_BASE_URL}")

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        session=session
    )

    # Инициализация диспетчера
    dp = Dispatcher()

    # Регистрация middleware (порядок важен: rate limiter → error handler)
    dp.message.middleware(RateLimiterMiddleware())
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
    logger.info(f"User rate limit: {settings.RATE_LIMIT_SECONDS}s")

    # Инициализация пула PostgreSQL
    pool = await get_pool()
    if pool:
        logger.info("✅ PostgreSQL pool initialized")
    else:
        logger.warning("⚠️  PostgreSQL unavailable - analytics disabled")

    # Настройка APScheduler для ежедневного дайджеста
    scheduler = None
    if settings.ENABLE_ANALYTICS and pool:
        msk_tz = pytz.timezone('Europe/Moscow')
        scheduler = AsyncIOScheduler(timezone=msk_tz)

        # Добавление задачи: ежедневно в 00:00 MSK
        scheduler.add_job(
            send_daily_digest_job,
            trigger=CronTrigger(hour=0, minute=0, timezone=msk_tz),
            args=[bot],
            id='daily_digest',
            name='Daily Analytics Digest',
            replace_existing=True
        )

        scheduler.start()
        logger.info("✅ APScheduler started: daily digest at 00:00 MSK")
    else:
        logger.info("ℹ️  APScheduler not started (analytics disabled or DB unavailable)")

    try:
        # Удаляем webhook (для long polling)
        await bot.delete_webhook(drop_pending_updates=True)

        # Запуск long polling
        logger.info("Starting long polling...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.critical(f"Fatal error: {e}")
    finally:
        # Остановка scheduler
        if scheduler and scheduler.running:
            scheduler.shutdown(wait=False)
            logger.info("APScheduler stopped")

        # Закрытие пула БД
        await close_pool()
        logger.info("PostgreSQL pool closed")

        await bot.session.close()
        logger.info("Bot stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user")
