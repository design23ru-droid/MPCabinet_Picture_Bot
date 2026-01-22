# Документация по Timeweb VPS для MPCabinet Picture Bot

**Дата развертывания:** 22.01.2026
**Провайдер:** [Timeweb Cloud](https://timeweb.cloud/)
**Локация:** MSK (Москва)

---

## 1. Характеристики VPS

### Тариф: Cloud MSK 2 GB

| Параметр | Значение |
|----------|----------|
| **vCPU** | 1 ядро |
| **RAM** | 2 GB |
| **NVMe SSD** | 10 GB |
| **Стоимость** | 550 ₽/мес |
| **ОС** | Ubuntu 24.04 LTS |
| **IPv4** | 89.23.101.91 |
| **IPv6** | Отсутствует (ISP не поддерживает) |

### Доступ

```bash
# SSH подключение
ssh root@89.23.101.91

# Пароль (хранить в безопасности!)
# aQtdwW*BZy7pDV
```

**Рекомендация безопасности:** После начальной настройки замените парольную аутентификацию на SSH-ключи.

---

## 2. Регистрация и настройка VPS (пошагово)

### Шаг 1: Регистрация на Timeweb

1. Откройте https://timeweb.cloud/
2. Нажмите "Зарегистрироваться"
3. Заполните данные и подтвердите email

### Шаг 2: Создание VPS

1. Перейдите в **"Серверы"** → **"Создать сервер"**
2. Выберите:
   - **Локация:** Москва (MSK)
   - **ОС:** Ubuntu 24.04 LTS
   - **Конфигурация:** Cloud MSK 2 GB (1 vCPU, 2 GB RAM, 10 GB NVMe)
3. **Настройки сети:**
   - Публичный IPv4: Включено
   - IPv6: Опционально (не критично, если ISP не поддерживает)
4. **Авторизация:**
   - Выберите "Пароль" (по умолчанию)
   - Сохраните сгенерированный пароль
5. Нажмите **"Создать сервер"**

### Шаг 3: Получение доступа

После создания сервера (1-3 минуты):
1. Скопируйте **IP-адрес** (89.23.101.91)
2. Скопируйте **пароль root**
3. Проверьте SSH доступ:
   ```bash
   ssh root@89.23.101.91
   ```

---

## 3. Развернутая архитектура

### Схема сервисов

```
┌─────────────────────────────────────────────────┐
│            Timeweb Cloud VPS                    │
│         89.23.101.91 (Ubuntu 24.04)             │
│                                                 │
│  ┌──────────────────────────────────────────┐  │
│  │   Docker Compose Ecosystem               │  │
│  │                                          │  │
│  │  ┌────────────────────────────────────┐ │  │
│  │  │  telegram-bot-api                  │ │  │
│  │  │  (aiogram/telegram-bot-api)        │ │  │
│  │  │  Ports: 8081 (API), 8082 (Stats)   │ │  │
│  │  │  ├─ Local Bot API (2GB file limit) │ │  │
│  │  │  └─ API ID: 36746484               │ │  │
│  │  └────────────────────────────────────┘ │  │
│  │                    ↓                     │  │
│  │  ┌────────────────────────────────────┐ │  │
│  │  │  postgres                          │ │  │
│  │  │  (postgres:16-alpine)              │ │  │
│  │  │  Port: 5432 (internal)             │ │  │
│  │  │  ├─ Schema: shared (CRM)           │ │  │
│  │  │  └─ Schema: mpcabinet (bot-spec)   │ │  │
│  │  └────────────────────────────────────┘ │  │
│  │                    ↓                     │  │
│  │  ┌────────────────────────────────────┐ │  │
│  │  │  mpcabinet-picture-bot             │ │  │
│  │  │  (custom Python 3.11)              │ │  │
│  │  │  ├─ aiogram 3.x                    │ │  │
│  │  │  ├─ ffmpeg (HLS → MP4)             │ │  │
│  │  │  └─ 2GB file upload support        │ │  │
│  │  └────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

### Структура файлов на сервере

```
/opt/telegram-ecosystem/
├── docker-compose.yml          # Конфигурация всех сервисов
├── .env                        # Секреты (токены, пароли)
├── bot-api-data/              # Persistent storage для Bot API
│   └── (telegram-bot-api data)
├── postgres-data/             # Persistent storage для PostgreSQL
│   └── (database files)
├── postgres/
│   └── init/
│       └── 01-init.sql        # SQL схемы инициализации
└── bots/
    └── mpcabinet_picture_bot/
        ├── Dockerfile         # Сборка образа бота
        ├── main.py
        ├── config/
        ├── bot/
        ├── services/
        ├── utils/
        └── requirements.txt
```

---

## 4. Docker Compose конфигурация

### Сервисы

| Сервис | Image | Порты | Назначение |
|--------|-------|-------|------------|
| **telegram-bot-api** | aiogram/telegram-bot-api:latest | 8081, 8082 | Local Bot API (2GB лимит) |
| **postgres** | postgres:16-alpine | 5432 | База данных (multi-tenant) |
| **mpcabinet-picture-bot** | custom build | - | Telegram бот |

### Переменные окружения (.env)

```bash
# Telegram Bot API Server
TELEGRAM_API_ID=36746484
TELEGRAM_API_HASH=68612f498a559c14d36bd35ecb5475b6

# PostgreSQL
POSTGRES_USER=telegram_admin
POSTGRES_PASSWORD=Tg3c0syst3m_2024!
POSTGRES_DB=telegram_ecosystem

# Database URL для ботов
DATABASE_URL=postgresql://telegram_admin:Tg3c0syst3m_2024!@postgres:5432/telegram_ecosystem

# MPCabinet Picture Bot
MPCABINET_BOT_TOKEN=8432797164:AAEkA-ErFPV_ntZCFdmJDhkIhRLdJ-f586M
TELEGRAM_API_BASE_URL=http://telegram-bot-api:8081
TELEGRAM_API_LOCAL=true
HLS_MAX_VIDEO_SIZE_MB=2000
```

---

## 5. Команды для управления инфраструктурой

### Подключение к серверу

```bash
# SSH подключение
ssh root@89.23.101.91

# С увеличенным таймаутом (если сеть нестабильна)
ssh -o ConnectTimeout=60 root@89.23.101.91
```

### Docker Compose управление

```bash
# Перейти в директорию проекта
cd /opt/telegram-ecosystem

# Запустить все сервисы
docker compose up -d

# Остановить все сервисы
docker compose down

# Перезапустить все сервисы
docker compose restart

# Перезапустить конкретный сервис
docker compose restart mpcabinet-picture-bot

# Пересобрать и перезапустить бота (после изменений кода)
docker compose up -d --build mpcabinet-picture-bot

# Остановить сервисы и удалить контейнеры
docker compose down

# Остановить сервисы, удалить контейнеры И volumes (ВНИМАНИЕ: удаляет БД!)
docker compose down -v
```

### Просмотр логов

```bash
# Логи всех сервисов
docker compose logs

# Логи конкретного сервиса
docker compose logs mpcabinet-picture-bot
docker compose logs postgres
docker compose logs telegram-bot-api

# Логи в реальном времени (follow)
docker compose logs -f mpcabinet-picture-bot

# Последние 100 строк логов
docker compose logs --tail 100 mpcabinet-picture-bot

# Логи за последний час
docker compose logs --since 1h mpcabinet-picture-bot
```

### Статус и мониторинг

```bash
# Статус всех контейнеров
docker compose ps

# Подробная информация о сервисах
docker compose ps -a

# Использование ресурсов
docker stats

# Использование ресурсов конкретным контейнером
docker stats telegram-ecosystem-mpcabinet-picture-bot-1

# Проверка healthcheck
docker inspect telegram-ecosystem-postgres-1 | grep -A 10 Health
```

### Работа с контейнерами

```bash
# Выполнить команду в контейнере бота
docker compose exec mpcabinet-picture-bot ls -la

# Открыть bash в контейнере
docker compose exec mpcabinet-picture-bot bash

# Посмотреть переменные окружения
docker compose exec mpcabinet-picture-bot env

# Проверить ffmpeg в контейнере
docker compose exec mpcabinet-picture-bot ffmpeg -version
```

---

## 6. Работа с PostgreSQL

### Подключение к БД

```bash
# Открыть psql в контейнере
docker compose exec postgres psql -U telegram_admin -d telegram_ecosystem

# Или через docker exec
docker exec -it telegram-ecosystem-postgres-1 psql -U telegram_admin -d telegram_ecosystem
```

### Полезные SQL команды

```sql
-- Список всех схем
\dn

-- Список таблиц в схеме shared
\dt shared.*

-- Список таблиц в схеме mpcabinet
\dt mpcabinet.*

-- Просмотр структуры таблицы
\d shared.users

-- Количество пользователей
SELECT COUNT(*) FROM shared.users;

-- Последние 10 событий аналитики
SELECT * FROM shared.analytics_events ORDER BY created_at DESC LIMIT 10;

-- Размер базы данных
SELECT pg_size_pretty(pg_database_size('telegram_ecosystem'));

-- Размер таблиц
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname IN ('shared', 'mpcabinet')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Выход из psql
\q
```

### Бэкап базы данных

```bash
# Создать бэкап
docker compose exec postgres pg_dump -U telegram_admin telegram_ecosystem > backup_$(date +%Y%m%d_%H%M%S).sql

# Или через docker exec
docker exec telegram-ecosystem-postgres-1 pg_dump -U telegram_admin telegram_ecosystem > backup.sql

# Создать сжатый бэкап
docker compose exec postgres pg_dump -U telegram_admin telegram_ecosystem | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz

# Бэкап только схемы (без данных)
docker compose exec postgres pg_dump -U telegram_admin --schema-only telegram_ecosystem > schema_backup.sql

# Бэкап только данных
docker compose exec postgres pg_dump -U telegram_admin --data-only telegram_ecosystem > data_backup.sql
```

### Восстановление из бэкапа

```bash
# Восстановить бэкап
cat backup.sql | docker compose exec -T postgres psql -U telegram_admin telegram_ecosystem

# Восстановить сжатый бэкап
gunzip -c backup.sql.gz | docker compose exec -T postgres psql -U telegram_admin telegram_ecosystem
```

### Автоматический бэкап (cron)

```bash
# Создать скрипт бэкапа
cat > /opt/telegram-ecosystem/scripts/backup-postgres.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/telegram-ecosystem/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

cd /opt/telegram-ecosystem
docker compose exec -T postgres pg_dump -U telegram_admin telegram_ecosystem | gzip > $BACKUP_DIR/backup_$DATE.sql.gz

# Удалить бэкапы старше 7 дней
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete

echo "Backup completed: backup_$DATE.sql.gz"
EOF

# Сделать скрипт исполняемым
chmod +x /opt/telegram-ecosystem/scripts/backup-postgres.sh

# Добавить в crontab (бэкап каждый день в 3:00)
crontab -e
# Добавить строку:
# 0 3 * * * /opt/telegram-ecosystem/scripts/backup-postgres.sh >> /var/log/postgres-backup.log 2>&1
```

---

## 7. Проверка работоспособности

### Telegram Bot API

```bash
# Проверить статус Bot API
curl http://localhost:8082

# Проверить getMe через Local Bot API
curl http://localhost:8081/bot8432797164:AAEkA-ErFPV_ntZCFdmJDhkIhRLdJ-f586M/getMe

# Ожидаемый ответ:
# {"ok":true,"result":{"id":8432797164,"is_bot":true,"first_name":"MPCabinet Picture Bot",...}}
```

### PostgreSQL

```bash
# Проверить healthcheck
docker compose exec postgres pg_isready -U telegram_admin

# Ожидаемый вывод:
# /var/run/postgresql:5432 - accepting connections
```

### Бот

```bash
# Проверить, что бот запущен
docker compose ps mpcabinet-picture-bot

# Проверить логи бота
docker compose logs --tail 20 mpcabinet-picture-bot

# Должны видеть:
# Using Local Bot API: http://telegram-bot-api:8081
# Bot starting...
# Starting long polling...
```

### Системные ресурсы

```bash
# Использование диска
df -h

# Использование памяти
free -h

# Загрузка процессора и памяти
top

# Или с docker stats
docker stats --no-stream
```

---

## 8. Деплой кода бота

### Первичный деплой (уже выполнен)

```bash
# На локальной машине: упаковать код
cd /c/Users/SFran/Documents/GitHub/MPCabinet_Picture_Bot
tar -czf mpcabinet-bot.tar.gz \
  --exclude='.git' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.env' \
  --exclude='bot.log' \
  .

# Загрузить на сервер
scp mpcabinet-bot.tar.gz root@89.23.101.91:/tmp/

# На сервере: распаковать
ssh root@89.23.101.91
cd /opt/telegram-ecosystem/bots
rm -rf mpcabinet_picture_bot
mkdir -p mpcabinet_picture_bot
cd mpcabinet_picture_bot
tar -xzf /tmp/mpcabinet-bot.tar.gz
rm /tmp/mpcabinet-bot.tar.gz

# Пересобрать и перезапустить
cd /opt/telegram-ecosystem
docker compose up -d --build mpcabinet-picture-bot
```

### Обновление кода (quick deploy)

```bash
# На локальной машине
cd /c/Users/SFran/Documents/GitHub/MPCabinet_Picture_Bot

# Синхронизировать изменения (rsync быстрее scp)
rsync -avz --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' --exclude='.env' --exclude='bot.log' \
  ./ root@89.23.101.91:/opt/telegram-ecosystem/bots/mpcabinet_picture_bot/

# На сервере: перезапустить
ssh root@89.23.101.91 "cd /opt/telegram-ecosystem && docker compose up -d --build mpcabinet-picture-bot"
```

### Git-based деплой (рекомендуется для production)

```bash
# На сервере: клонировать репозиторий (один раз)
ssh root@89.23.101.91
cd /opt/telegram-ecosystem/bots
git clone https://github.com/<your-repo>/MPCabinet_Picture_Bot.git mpcabinet_picture_bot

# Обновление кода через git pull
cd /opt/telegram-ecosystem/bots/mpcabinet_picture_bot
git pull origin photoVideo  # или main

# Перезапустить
cd /opt/telegram-ecosystem
docker compose up -d --build mpcabinet-picture-bot
```

---

## 9. Диагностика проблем

### Бот не отвечает

```bash
# 1. Проверить статус контейнеров
docker compose ps

# 2. Проверить логи бота
docker compose logs --tail 50 mpcabinet-picture-bot

# 3. Проверить подключение к Bot API
docker compose exec mpcabinet-picture-bot curl http://telegram-bot-api:8081

# 4. Перезапустить бота
docker compose restart mpcabinet-picture-bot
```

### База данных недоступна

```bash
# 1. Проверить статус PostgreSQL
docker compose ps postgres

# 2. Проверить логи PostgreSQL
docker compose logs --tail 50 postgres

# 3. Проверить pg_isready
docker compose exec postgres pg_isready -U telegram_admin

# 4. Проверить подключение изнутри бота
docker compose exec mpcabinet-picture-bot nc -zv postgres 5432

# 5. Перезапустить PostgreSQL
docker compose restart postgres
```

### Local Bot API не работает

```bash
# 1. Проверить логи Bot API
docker compose logs --tail 50 telegram-bot-api

# 2. Проверить порты
docker compose exec telegram-bot-api netstat -tlnp

# 3. Проверить переменные окружения
docker compose exec telegram-bot-api env | grep TELEGRAM

# 4. Перезапустить Bot API
docker compose restart telegram-bot-api
```

### Нехватка места на диске

```bash
# Проверить использование диска
df -h

# Очистить неиспользуемые Docker данные
docker system prune -a

# Удалить старые логи
docker compose logs --tail 0 mpcabinet-picture-bot
journalctl --vacuum-time=7d

# Удалить старые образы
docker image prune -a
```

### Высокое использование памяти

```bash
# Посмотреть, какой контейнер ест память
docker stats --no-stream

# Перезапустить проблемный контейнер
docker compose restart <service-name>

# Ограничить память для сервиса (в docker-compose.yml):
# deploy:
#   resources:
#     limits:
#       memory: 512M
```

---

## 10. Безопасность

### Настройка firewall (UFW)

```bash
# Установить UFW (если не установлен)
apt install -y ufw

# Разрешить SSH
ufw allow 22/tcp

# Запретить доступ к PostgreSQL извне
ufw deny 5432/tcp

# Запретить доступ к Bot API извне (опционально)
ufw deny 8081/tcp
ufw deny 8082/tcp

# Включить firewall
ufw enable

# Проверить статус
ufw status verbose
```

### Настройка SSH (рекомендуется)

```bash
# Создать SSH ключ на локальной машине (если нет)
ssh-keygen -t ed25519 -C "mpcabinet-vps"

# Скопировать публичный ключ на сервер
ssh-copy-id root@89.23.101.91

# На сервере: отключить парольную аутентификацию
nano /etc/ssh/sshd_config
# Изменить:
# PasswordAuthentication no
# PermitRootLogin prohibit-password

# Перезапустить SSH
systemctl restart sshd
```

### Обновление системы

```bash
# Обновить пакеты
apt update && apt upgrade -y

# Автоматические обновления безопасности
apt install -y unattended-upgrades
dpkg-reconfigure --priority=low unattended-upgrades
```

---

## 11. Мониторинг и алерты

### Проверка uptime

```bash
# Установить uptimerobot или использовать встроенный мониторинг Timeweb
# В панели Timeweb: Серверы → Мониторинг

# Или установить простой health check скрипт
cat > /opt/telegram-ecosystem/scripts/health-check.sh << 'EOF'
#!/bin/bash
BOT_STATUS=$(docker compose -f /opt/telegram-ecosystem/docker-compose.yml ps mpcabinet-picture-bot | grep -c "Up")

if [ $BOT_STATUS -eq 0 ]; then
    echo "Bot is DOWN! Restarting..."
    cd /opt/telegram-ecosystem
    docker compose restart mpcabinet-picture-bot
fi
EOF

chmod +x /opt/telegram-ecosystem/scripts/health-check.sh

# Добавить в crontab (проверка каждые 5 минут)
# */5 * * * * /opt/telegram-ecosystem/scripts/health-check.sh >> /var/log/health-check.log 2>&1
```

### Логирование

```bash
# Настроить ротацию логов Docker
cat > /etc/docker/daemon.json << 'EOF'
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF

systemctl restart docker
```

---

## 12. Масштабирование

### Добавление второго бота

```bash
# 1. Создать директорию для нового бота
cd /opt/telegram-ecosystem/bots
mkdir second_bot

# 2. Добавить сервис в docker-compose.yml
# second-bot:
#   build: ./bots/second_bot
#   environment:
#     BOT_TOKEN: ${SECOND_BOT_TOKEN}
#     TELEGRAM_API_BASE_URL: http://telegram-bot-api:8081
#     TELEGRAM_API_LOCAL: "true"
#     DATABASE_URL: ${DATABASE_URL}
#   depends_on:
#     - telegram-bot-api
#     - postgres

# 3. Создать схему в PostgreSQL
docker compose exec postgres psql -U telegram_admin -d telegram_ecosystem -c "CREATE SCHEMA IF NOT EXISTS second_bot;"

# 4. Добавить токен в .env
# SECOND_BOT_TOKEN=<token>

# 5. Запустить
docker compose up -d second-bot
```

### Upgrade тарифа

Если текущего VPS недостаточно:

1. **В панели Timeweb:**
   - Серверы → Выбрать сервер
   - Нажать "Изменить конфигурацию"
   - Выбрать новый тариф (например, Cloud MSK 4 GB)

2. **Рекомендации:**
   - При 3-4 ботах → 4 GB RAM
   - При 5-8 ботах → 6 GB RAM (или переход на WebHOST1)

---

## 13. Стоимость и биллинг

### Текущие расходы

| Услуга | Стоимость |
|--------|----------|
| Timeweb Cloud MSK 2 GB | 550 ₽/мес |
| **Итого** | **550 ₽/мес** |

### Прогноз при масштабировании

| Конфигурация | Ботов | Тариф | Цена |
|--------------|-------|-------|------|
| 2 GB RAM | 1-2 | Cloud MSK 2 GB | 550 ₽/мес |
| 4 GB RAM | 3-4 | Cloud MSK 4 GB | 1 062 ₽/мес |
| WebHOST1 6 GB | 6-8 | RU NVME 80 | 1 575 ₽/мес |

### Оплата

- **Личный кабинет:** https://timeweb.cloud/my/finance
- **Автопродление:** Настроить в разделе "Биллинг"
- **Уведомления:** Включить email-уведомления о балансе

---

## 14. Полезные ссылки

### Документация

- [Timeweb Cloud документация](https://timeweb.cloud/help/)
- [Docker Compose CLI](https://docs.docker.com/compose/reference/)
- [PostgreSQL 16 документация](https://www.postgresql.org/docs/16/)
- [aiogram/telegram-bot-api](https://github.com/aiogram/telegram-bot-api)
- [aiogram Custom Server docs](https://docs.aiogram.dev/en/dev-3.x/api/session/custom_server.html)

### Панели управления

- [Timeweb панель управления](https://timeweb.cloud/my/servers)
- Мониторинг сервера: доступен в панели Timeweb

---

## 15. Чеклист перед production

- [ ] Настроен firewall (UFW)
- [ ] Отключена парольная аутентификация SSH
- [ ] Настроены автоматические бэкапы PostgreSQL (cron)
- [ ] Настроен health check и автоперезапуск
- [ ] Настроена ротация логов Docker
- [ ] Включены автоматические обновления безопасности
- [ ] Мониторинг uptime (Timeweb или внешний)
- [ ] Документированы все пароли и токены (password manager)
- [ ] Протестирована отправка файлов > 50 MB через Local Bot API
- [ ] Проверена запись в PostgreSQL (shared.analytics_events)

---

## 16. Контакты и поддержка

### Техподдержка Timeweb

- **Email:** support@timeweb.ru
- **Телефон:** 8 (800) 700-06-08
- **Telegram:** @timeweb_support
- **Тикеты:** https://timeweb.cloud/my/tickets

### Экстренное восстановление

Если VPS недоступен:
1. Проверить статус в панели Timeweb
2. Создать тикет в поддержку
3. При полной потере данных: восстановить из бэкапа PostgreSQL

---

**Документ создан:** 22.01.2026
**Версия:** 1.0
**Автор:** Claude (на основе развертывания MPCabinet Picture Bot)
