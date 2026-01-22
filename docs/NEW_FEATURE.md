# Руководство по разработке и деплою новых функций

**Для:** MPCabinet Picture Bot
**Обновлено:** 22.01.2026
**Версия:** 0.4.0

---

## Архитектура разработки

```
┌─────────────────────────────────────────────────────┐
│  ЛОКАЛЬНАЯ МАШИНА (разработка)                      │
│  - Windows                                          │
│  - Python 3.11                                      │
│  - Git                                              │
│  - VSCode                                           │
│  - Тестовый бот (отдельный токен)                   │
└─────────────────────────────────────────────────────┘
                    ↓ git push
                    ↓ ssh деплой
┌─────────────────────────────────────────────────────┐
│  VPS (production)                                   │
│  89.23.101.91                                       │
│  - Ubuntu 24.04                                     │
│  - Docker Compose                                   │
│  - Local Bot API                                    │
│  - PostgreSQL                                       │
│  - Продакшн бот (текущий токен)                     │
└─────────────────────────────────────────────────────┘
```

---

## Полный цикл разработки (пошагово)

### 1. Разработка новой фичи (локально)

```bash
# Переключаемся на новую ветку
git checkout -b feature/new-awesome-feature

# Пишем код в VSCode
# Редактируем файлы...

# Запускаем бота ЛОКАЛЬНО для проверки
python main.py
```

**Важно:** Для локальной разработки используйте **отдельного тестового бота**:
- Идите к @BotFather → `/newbot`
- Назовите его `MPCabinet Picture Bot TEST` (username: `mpcabinet_picture_bot_test`)
- Скопируйте токен
- Используйте этот токен в локальном `.env`

**Структура `.env` (локально):**
```env
# Локальный тестовый бот
BOT_TOKEN=1234567890:AAExxxTESTxxxBOTxxxTOKENxxx

# Локально НЕ используем Local API (если не надо тестировать 2GB файлы)
# TELEGRAM_API_BASE_URL=
# TELEGRAM_API_LOCAL=false

LOG_LEVEL=DEBUG  # DEBUG для разработки
```

---

### 2. Тестирование локально

```bash
# Запустить бота
python main.py

# Проверить в Telegram (через тестового бота)
# Отправить артикул, проверить новую фичу

# Если есть юнит-тесты
pytest tests/ -v

# Если добавили новый код — добавьте тесты!
pytest tests/test_my_new_feature.py -v
```

---

### 3. Коммит изменений

```bash
# Посмотреть что изменилось
git status

# Добавить файлы
git add services/my_new_feature.py
git add bot/handlers/new_handler.py

# Коммит (по правилам из CLAUDE.md)
git commit -m "Добавлена новая фича: описание

- Детали изменения 1
- Детали изменения 2

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# Push в ветку
git push origin feature/new-awesome-feature
```

---

### 4. Merge в основную ветку

```bash
# Переключиться на основную ветку
git checkout photoVideo  # или main

# Смержить фичу
git merge feature/new-awesome-feature

# Или через Pull Request на GitHub (рекомендуется)
# - Создаете PR в GitHub
# - Проверяете код
# - Мержите через веб-интерфейс
```

---

## Деплой на VPS (три способа)

### Способ 1: Git Pull (рекомендуется для production)

**На VPS:**
```bash
# Подключиться к VPS
ssh root@89.23.101.91

# Перейти в директорию бота
cd /opt/telegram-ecosystem/bots/mpcabinet_picture_bot

# Скачать изменения из GitHub
git pull origin photoVideo

# Пересобрать и перезапустить контейнер
cd /opt/telegram-ecosystem
docker compose up -d --build mpcabinet-picture-bot

# Проверить логи
docker compose logs -f mpcabinet-picture-bot
```

**Этот способ:**
- ✅ Безопасный (версионируется через Git)
- ✅ Можно откатиться (`git checkout <commit>`)
- ✅ Виден history изменений
- ❌ Требует коммита перед деплоем

---

### Способ 2: rsync (для быстрых правок)

**С локальной машины:**
```bash
# Синхронизировать изменения напрямую
rsync -avz --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' --exclude='.env' --exclude='bot.log' \
  /c/Users/SFran/Documents/GitHub/MPCabinet_Picture_Bot/ \
  root@89.23.101.91:/opt/telegram-ecosystem/bots/mpcabinet_picture_bot/

# Затем на VPS перезапустить
ssh root@89.23.101.91 "cd /opt/telegram-ecosystem && docker compose up -d --build mpcabinet-picture-bot"
```

**Этот способ:**
- ✅ Быстро (не нужен git push)
- ✅ Удобно для отладки
- ❌ Опасно (можно задеплоить недотестированный код)
- ❌ Нет истории изменений на VPS

---

### Способ 3: CI/CD (автоматический деплой)

**Настраивается один раз, работает автоматически:**

GitHub Actions → при push в main → автоматически деплоит на VPS

**Файл `.github/workflows/deploy.yml`:**
```yaml
name: Deploy to VPS

on:
  push:
    branches: [ photoVideo ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to VPS
        uses: appleboy/ssh-action@master
        with:
          host: 89.23.101.91
          username: root
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /opt/telegram-ecosystem/bots/mpcabinet_picture_bot
            git pull origin photoVideo
            cd /opt/telegram-ecosystem
            docker compose up -d --build mpcabinet-picture-bot
```

**Этот способ:**
- ✅ Полностью автоматический
- ✅ Надежный
- ✅ Production-ready
- ❌ Требует настройки один раз

---

## Рекомендуемый workflow

### Для мелких правок (bug fixes, косметика)

```bash
# 1. Локально: править код
nano services/wb_parser.py

# 2. Локально: тестировать
python main.py  # проверить работает ли

# 3. Локально: коммит
git add services/wb_parser.py
git commit -m "Исправлен баг с поиском basket"
git push origin photoVideo

# 4. На VPS: деплой через git pull
ssh root@89.23.101.91
cd /opt/telegram-ecosystem/bots/mpcabinet_picture_bot
git pull origin photoVideo
cd /opt/telegram-ecosystem
docker compose up -d --build mpcabinet-picture-bot
docker compose logs -f mpcabinet-picture-bot  # проверить логи
```

---

### Для новых фичей (требуют тестирования)

```bash
# 1. Создать ветку feature
git checkout -b feature/mass-download
# Пишете код...
# Тестируете локально с тестовым ботом

# 2. Коммиты в feature ветку
git add .
git commit -m "Добавлена массовая загрузка артикулов"
git push origin feature/mass-download

# 3. Создать Pull Request на GitHub
# - Открыть GitHub → ваш репозиторий
# - Compare & pull request: feature/mass-download → photoVideo
# - Review кода (можно попросить Claude проверить)
# - Merge PR

# 4. На VPS: деплой merged изменений
ssh root@89.23.101.91
cd /opt/telegram-ecosystem/bots/mpcabinet_picture_bot
git pull origin photoVideo
cd /opt/telegram-ecosystem
docker compose up -d --build mpcabinet-picture-bot
```

---

## Откат к предыдущей версии (если что-то сломалось)

```bash
# На VPS: посмотреть историю коммитов
cd /opt/telegram-ecosystem/bots/mpcabinet_picture_bot
git log --oneline -5

# Откатиться на конкретный коммит (например, 0690807)
git checkout 0690807

# Перезапустить
cd /opt/telegram-ecosystem
docker compose up -d --build mpcabinet-picture-bot

# Проверить работает ли
docker compose logs -f mpcabinet-picture-bot

# Если работает — вернуться к разработке фикса локально
# Если не работает — откатиться еще дальше
```

---

## Тестирование новых фич БЕЗ влияния на продакшн

### Вариант 1: Используйте тестового бота локально

```bash
# Локально (.env)
BOT_TOKEN=<тестовый_бот_токен>

# Запускаете локально
python main.py

# Тестируете сколько угодно — продакшн бот не затрагивается
```

**Ограничения:**
- Нет Local Bot API (лимит 50 MB)
- Нет доступа к production PostgreSQL

---

### Вариант 2: Второй Docker контейнер на VPS (staging)

**Структура:**
```
VPS:
  - mpcabinet-picture-bot (production, порт 8081)
  - mpcabinet-picture-bot-staging (тестовый, порт 8083)
```

**docker-compose.yml (добавить):**
```yaml
mpcabinet-picture-bot-staging:
  build: ./bots/mpcabinet_picture_bot
  environment:
    BOT_TOKEN: ${STAGING_BOT_TOKEN}  # отдельный тестовый бот
    TELEGRAM_API_BASE_URL: http://telegram-bot-api:8081  # тот же Bot API
    TELEGRAM_API_LOCAL: "true"
    DATABASE_URL: ${DATABASE_URL}  # та же БД, но можно отдельную
  depends_on:
    - telegram-bot-api
    - postgres
```

**Workflow:**
```bash
# 1. Деплоите изменения в staging контейнер
ssh root@89.23.101.91
cd /opt/telegram-ecosystem
docker compose up -d --build mpcabinet-picture-bot-staging

# 2. Тестируете через staging бота в Telegram
# 3. Если все ок — деплоите в production
docker compose up -d --build mpcabinet-picture-bot
```

---

## Мониторинг и проверка после деплоя

```bash
# Проверить статус контейнеров
docker compose ps

# Логи в реальном времени
docker compose logs -f mpcabinet-picture-bot

# Последние 50 строк логов
docker compose logs --tail 50 mpcabinet-picture-bot

# Проверить использование ресурсов
docker stats

# Проверить что бот отвечает
# Отправить /start боту в Telegram
```

---

## Checklist перед деплоем на production

- [ ] Код протестирован локально
- [ ] Все юнит-тесты проходят: `pytest tests/ -v`
- [ ] Логи не содержат критичных ошибок
- [ ] Commit сделан с описательным сообщением
- [ ] Push в GitHub: `git push origin photoVideo`
- [ ] (Опционально) Протестировано на staging боте
- [ ] Деплой через `git pull` на VPS
- [ ] Логи после деплоя проверены
- [ ] Бот отвечает в Telegram

---

## Типичные сценарии

### Сценарий 1: "Добавил кнопку в клавиатуру"

```bash
# Локально
git checkout -b feature/new-button
# Редактируете bot/keyboards/inline.py
python main.py  # тестируете
pytest tests/test_keyboards.py -v
git commit -m "Добавлена кнопка Скачать ZIP"
git push origin photoVideo

# На VPS
ssh root@89.23.101.91
cd /opt/telegram-ecosystem/bots/mpcabinet_picture_bot && git pull
cd /opt/telegram-ecosystem && docker compose up -d --build mpcabinet-picture-bot
```

---

### Сценарий 2: "Сломалось на production, нужно откатить"

```bash
# На VPS
ssh root@89.23.101.91
cd /opt/telegram-ecosystem/bots/mpcabinet_picture_bot
git log --oneline -5  # найти последний рабочий коммит
git checkout <working_commit>
cd /opt/telegram-ecosystem
docker compose up -d --build mpcabinet-picture-bot

# Проверить работает
docker compose logs -f mpcabinet-picture-bot
```

---

### Сценарий 3: "Хочу протестировать с файлами > 50 MB"

Вам нужен доступ к Local Bot API. Два варианта:

**Вариант A: Поднять Local Bot API локально (сложно)**
- Установить Docker на Windows
- Запустить telegram-bot-api контейнер локально
- Изменить `.env`: `TELEGRAM_API_BASE_URL=http://localhost:8081`

**Вариант B: Тестировать на VPS через staging бота (проще)**
- Создать staging контейнер (см. выше)
- Деплоить туда фичи до production

---

## Краткая шпаргалка

| Действие | Команды |
|----------|---------|
| **Разработка локально** | `python main.py` (с тестовым BOT_TOKEN) |
| **Тесты** | `pytest tests/ -v` |
| **Коммит** | `git add . && git commit -m "..."` |
| **Деплой на VPS** | `ssh VPS → git pull → docker compose up -d --build` |
| **Логи** | `docker compose logs -f mpcabinet-picture-bot` |
| **Откат** | `git checkout <commit> → docker compose up -d --build` |
| **Проверка** | Отправить `/start` боту в Telegram |

---

## Структура веток Git

```
main / photoVideo (production)
  ├── feature/new-feature-1 (в разработке)
  ├── feature/new-feature-2 (в разработке)
  ├── hotfix/critical-bug (экстренный фикс)
  └── staging (опционально, для pre-production тестов)
```

**Правила:**
- `photoVideo` (или `main`) — только стабильный, протестированный код
- `feature/*` — разработка новых функций
- `hotfix/*` — экстренные исправления критичных багов
- Всегда делайте `git pull` перед началом работы
- Мержите через Pull Request для code review

---

## Настройка staging окружения (опционально)

### 1. Создать staging бота у @BotFather

```
/newbot
Name: MPCabinet Picture Bot STAGING
Username: mpcabinet_picture_bot_staging
Token: <staging_token>
```

### 2. Добавить токен в .env на VPS

```bash
ssh root@89.23.101.91
nano /opt/telegram-ecosystem/.env
# Добавить:
# STAGING_BOT_TOKEN=<staging_token>
```

### 3. Добавить сервис в docker-compose.yml

```yaml
mpcabinet-picture-bot-staging:
  build:
    context: ./bots/mpcabinet_picture_bot
  environment:
    BOT_TOKEN: ${STAGING_BOT_TOKEN}
    TELEGRAM_API_BASE_URL: http://telegram-bot-api:8081
    TELEGRAM_API_LOCAL: "true"
    DATABASE_URL: ${DATABASE_URL}
    LOG_LEVEL: DEBUG
  depends_on:
    - telegram-bot-api
    - postgres
  restart: unless-stopped
```

### 4. Запустить staging

```bash
cd /opt/telegram-ecosystem
docker compose up -d mpcabinet-picture-bot-staging
docker compose logs -f mpcabinet-picture-bot-staging
```

### 5. Workflow с staging

```bash
# Деплой новой фичи в staging
ssh root@89.23.101.91
cd /opt/telegram-ecosystem/bots/mpcabinet_picture_bot
git checkout feature/new-feature
cd /opt/telegram-ecosystem
docker compose up -d --build mpcabinet-picture-bot-staging

# Тестируем через @mpcabinet_picture_bot_staging
# Если все ок — мержим в photoVideo и деплоим в production
git checkout photoVideo
git merge feature/new-feature
docker compose up -d --build mpcabinet-picture-bot
```

---

## Настройка CI/CD через GitHub Actions (опционально)

### 1. Создать SSH ключ для GitHub Actions

```bash
# На локальной машине
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github_actions_deploy

# Скопировать публичный ключ на VPS
ssh-copy-id -i ~/.ssh/github_actions_deploy.pub root@89.23.101.91

# Скопировать ПРИВАТНЫЙ ключ
cat ~/.ssh/github_actions_deploy
# Скопировать весь вывод
```

### 2. Добавить SSH ключ в GitHub Secrets

1. Откройте GitHub → ваш репозиторий
2. Settings → Secrets and variables → Actions
3. New repository secret:
   - Name: `SSH_PRIVATE_KEY`
   - Value: вставить приватный ключ

### 3. Создать workflow файл

```bash
# Локально
mkdir -p .github/workflows
nano .github/workflows/deploy.yml
```

```yaml
name: Deploy to Production

on:
  push:
    branches: [ photoVideo ]

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
    - name: Deploy to VPS
      uses: appleboy/ssh-action@master
      with:
        host: 89.23.101.91
        username: root
        key: ${{ secrets.SSH_PRIVATE_KEY }}
        script: |
          cd /opt/telegram-ecosystem/bots/mpcabinet_picture_bot
          git pull origin photoVideo
          cd /opt/telegram-ecosystem
          docker compose up -d --build mpcabinet-picture-bot

    - name: Check deployment
      uses: appleboy/ssh-action@master
      with:
        host: 89.23.101.91
        username: root
        key: ${{ secrets.SSH_PRIVATE_KEY }}
        script: |
          cd /opt/telegram-ecosystem
          docker compose ps mpcabinet-picture-bot
          docker compose logs --tail 20 mpcabinet-picture-bot
```

### 4. Коммит и пуш

```bash
git add .github/workflows/deploy.yml
git commit -m "Добавлен CI/CD для автоматического деплоя"
git push origin photoVideo

# Теперь каждый push в photoVideo автоматически деплоит на VPS!
```

---

## Полезные команды Git

```bash
# Посмотреть текущую ветку
git branch

# Создать и переключиться на новую ветку
git checkout -b feature/new-feature

# Переключиться на существующую ветку
git checkout photoVideo

# Обновить локальную ветку с удаленной
git pull origin photoVideo

# Посмотреть статус (что изменилось)
git status

# Посмотреть историю коммитов
git log --oneline -10

# Посмотреть изменения в файлах
git diff

# Откатить все незакоммиченные изменения
git restore .

# Удалить локальную ветку (после merge)
git branch -d feature/old-feature

# Посмотреть все ветки (включая удаленные)
git branch -a

# Синхронизировать список веток с GitHub
git fetch --prune
```

---

## Troubleshooting

### Проблема: Бот не запускается после деплоя

```bash
# 1. Проверить логи
docker compose logs --tail 50 mpcabinet-picture-bot

# 2. Проверить статус контейнера
docker compose ps

# 3. Перезапустить контейнер
docker compose restart mpcabinet-picture-bot

# 4. Пересобрать с нуля (если изменился Dockerfile)
docker compose down mpcabinet-picture-bot
docker compose build --no-cache mpcabinet-picture-bot
docker compose up -d mpcabinet-picture-bot
```

---

### Проблема: Git конфликты при pull

```bash
# Посмотреть какие файлы конфликтуют
git status

# Вариант 1: Сохранить локальные изменения
git stash
git pull origin photoVideo
git stash pop  # восстановить изменения, разрешить конфликты вручную

# Вариант 2: Отменить локальные изменения (ВНИМАНИЕ: потеря данных!)
git reset --hard HEAD
git pull origin photoVideo
```

---

### Проблема: Контейнер занимает много места

```bash
# Очистить неиспользуемые образы и контейнеры
docker system prune -a

# Посмотреть использование диска
df -h
docker system df
```

---

## Дополнительные ресурсы

- [CLAUDE.md](../CLAUDE.md) — правила разработки и коммитов
- [docs/PLAN.md](PLAN.md) — план разработки и история релизов
- [docs/VDS.md](VDS.md) — документация по работе с VPS
- [README.md](../README.md) — документация проекта
- [CONTEXT.md](../CONTEXT.md) — техническая документация

---

**Последнее обновление:** 22.01.2026
**Версия документа:** 1.0
**Автор:** Claude Sonnet 4.5
