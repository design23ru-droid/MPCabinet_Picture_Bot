-- Миграция 02: Система аналитики и уведомлений
-- Версия: 0.5.0
-- Дата: 2026-01-22

-- Создание схемы shared если не существует
CREATE SCHEMA IF NOT EXISTS shared;

-- Таблица пользователей (единая для всех ботов экосистемы)
CREATE TABLE IF NOT EXISTS shared.users (
    telegram_id BIGINT PRIMARY KEY,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    first_seen TIMESTAMP DEFAULT NOW(),
    last_seen TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE shared.users IS 'Единая таблица пользователей для CRM экосистемы MPCabinet';
COMMENT ON COLUMN shared.users.telegram_id IS 'Telegram ID пользователя (первичный ключ)';
COMMENT ON COLUMN shared.users.username IS 'Username в Telegram (@username)';
COMMENT ON COLUMN shared.users.first_name IS 'Имя пользователя';
COMMENT ON COLUMN shared.users.last_name IS 'Фамилия пользователя';
COMMENT ON COLUMN shared.users.first_seen IS 'Время первого обращения к боту';
COMMENT ON COLUMN shared.users.last_seen IS 'Время последнего обращения к боту';

-- Таблица событий аналитики
CREATE TABLE IF NOT EXISTS shared.analytics_events (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL REFERENCES shared.users(telegram_id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE shared.analytics_events IS 'События аналитики для всех ботов экосистемы';
COMMENT ON COLUMN shared.analytics_events.id IS 'Уникальный идентификатор события';
COMMENT ON COLUMN shared.analytics_events.telegram_id IS 'ID пользователя (FK на shared.users)';
COMMENT ON COLUMN shared.analytics_events.event_type IS 'Тип события: user_start, article_request, photo_sent, video_sent, error';
COMMENT ON COLUMN shared.analytics_events.event_data IS 'Дополнительные данные в формате JSON';
COMMENT ON COLUMN shared.analytics_events.created_at IS 'Время создания события';

-- Индексы для производительности
CREATE INDEX IF NOT EXISTS idx_events_created_at ON shared.analytics_events(created_at);
CREATE INDEX IF NOT EXISTS idx_events_type ON shared.analytics_events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_telegram_id ON shared.analytics_events(telegram_id);

-- Составной индекс для запросов по дате + типу события
CREATE INDEX IF NOT EXISTS idx_events_date_type ON shared.analytics_events(created_at, event_type);

-- Вывод информации о созданных объектах
DO $$
BEGIN
    RAISE NOTICE 'Миграция 02-analytics.sql успешно выполнена';
    RAISE NOTICE 'Создано:';
    RAISE NOTICE '  - Схема: shared';
    RAISE NOTICE '  - Таблица: shared.users';
    RAISE NOTICE '  - Таблица: shared.analytics_events';
    RAISE NOTICE '  - Индексы: 4 шт (created_at, event_type, telegram_id, date_type)';
END $$;
