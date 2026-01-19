# Аналитика

[← Назад к оглавлению](./README.md)

**Base URL:** `https://seller-analytics-api.wildberries.ru`

---

## Воронка продаж

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/api/analytics/v3/sales-funnel/products` | Статистика карточек за период |
| POST | `/api/analytics/v3/sales-funnel/products/history` | Статистика карточек по дням |
| POST | `/api/analytics/v3/sales-funnel/grouped/history` | Группированная статистика |

**Данные включают:**
- Просмотры карточки
- Добавления в корзину
- Заказы
- Выкупы
- Конверсии на каждом этапе

**Важно:** Максимум 7 дней за один запрос.

---

## Поисковые запросы

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/api/v2/search-report/report` | Основная страница отчёта |
| POST | `/api/v2/search-report/table/groups` | Данные по группам |
| POST | `/api/v2/search-report/table/details` | Детализация по товарам |
| POST | `/api/v2/search-report/product/search-texts` | Топ поисковых запросов по товару |
| POST | `/api/v2/search-report/product/orders` | Заказы по поисковым запросам |

**Данные включают:**
- По каким запросам находят товар
- Позиция в выдаче
- Количество показов и кликов
- Конверсия в заказ

---

## История остатков

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/api/v2/stocks-report/products/groups` | По группам |
| POST | `/api/v2/stocks-report/products/products` | По товарам |
| POST | `/api/v2/stocks-report/products/sizes` | По размерам |
| POST | `/api/v2/stocks-report/offices` | По складам |

---

## Отчёты CSV

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/api/v2/nm-report/downloads` | Создать отчёт |
| GET | `/api/v2/nm-report/downloads` | Список отчётов |
| POST | `/api/v2/nm-report/downloads/retry` | Пересоздать отчёт |
| GET | `/api/v2/nm-report/downloads/file/{downloadId}` | Скачать отчёт |

---

[← Чат](./11-chat.md) | [Назад к оглавлению](./README.md) | [Далее: Отчёты →](./13-reports.md)
