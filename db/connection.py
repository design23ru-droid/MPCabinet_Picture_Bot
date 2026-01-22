"""Управление пулом соединений PostgreSQL через asyncpg."""

import asyncpg
import logging
from typing import Optional

from config.settings import Settings

logger = logging.getLogger(__name__)

# Глобальный пул соединений (singleton)
_pool: Optional[asyncpg.Pool] = None


async def get_pool() -> Optional[asyncpg.Pool]:
    """
    Получить пул соединений PostgreSQL (singleton).

    Если пул уже создан - возвращает его.
    Если DATABASE_URL не настроен - возвращает None (graceful degradation).
    При ошибке подключения - логирует ошибку и возвращает None.

    Returns:
        asyncpg.Pool или None если БД недоступна
    """
    global _pool

    # Если пул уже создан - возвращаем его
    if _pool is not None:
        return _pool

    # Загружаем настройки
    settings = Settings()

    # Проверяем наличие DATABASE_URL
    if not settings.DATABASE_URL:
        logger.warning(
            "⚠️  DATABASE_URL не настроен - аналитика отключена. "
            "Бот продолжит работу без сохранения статистики."
        )
        return None

    # Пытаемся создать пул соединений
    try:
        _pool = await asyncpg.create_pool(
            settings.DATABASE_URL,
            min_size=2,  # Минимум 2 соединения в пуле
            max_size=10,  # Максимум 10 соединений
            command_timeout=60,  # Таймаут команды 60 секунд
        )
        logger.info("✅ Пул соединений PostgreSQL создан (min=2, max=10)")
        return _pool

    except asyncpg.InvalidCatalogNameError as e:
        logger.error(
            f"❌ База данных не существует: {e}\n"
            f"Создайте базу данных или выполните миграцию."
        )
        return None

    except asyncpg.InvalidPasswordError as e:
        logger.error(f"❌ Неверный пароль PostgreSQL: {e}")
        return None

    except (asyncpg.PostgresConnectionError, OSError) as e:
        logger.error(
            f"❌ Не удалось подключиться к PostgreSQL: {type(e).__name__}: {e}\n"
            f"Проверьте что PostgreSQL запущен и доступен."
        )
        return None

    except Exception as e:
        logger.error(
            f"❌ Непредвиденная ошибка при создании пула PostgreSQL: "
            f"{type(e).__name__}: {e}"
        )
        return None


async def close_pool() -> None:
    """
    Закрыть пул соединений PostgreSQL (graceful shutdown).

    Вызывается при остановке бота для корректного завершения всех соединений.
    """
    global _pool

    if _pool is not None:
        await _pool.close()
        _pool = None
        logger.info("✅ Пул соединений PostgreSQL закрыт")
    else:
        logger.debug("Пул соединений PostgreSQL уже закрыт или не был создан")
