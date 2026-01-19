# API Wildberries — Справочник

> Полный справочник методов API Wildberries, организованный по бизнес-задачам.
> Официальная документация: [dev.wildberries.ru](https://dev.wildberries.ru)

---

## Разделы

| # | Раздел | Описание |
|---|--------|----------|
| 1 | [Товары](./01-products.md) | Карточки, медиа, теги, справочники |
| 2 | [Цены](./02-prices.md) | Установка цен, скидки, акции |
| 3 | [Остатки](./03-stocks.md) | Склады продавца, обновление остатков |
| 4 | [Заказы FBS](./04-orders-fbs.md) | Сборочные задания, поставки, стикеры |
| 5 | [Заказы DBS](./05-orders-dbs.md) | Доставка продавцом |
| 6 | [Заказы DBW](./06-orders-dbw.md) | Доставка курьером WB |
| 7 | [Самовывоз](./07-click-collect.md) | Click & Collect |
| 8 | [Поставки FBW](./08-supplies-fbw.md) | Поставки на склад WB |
| 9 | [Реклама](./09-promotion.md) | Кампании, ставки, статистика, акции |
| 10 | [Отзывы](./10-feedbacks.md) | Отзывы, вопросы, закрепление |
| 11 | [Чат](./11-chat.md) | Чат с покупателями |
| 12 | [Аналитика](./12-analytics.md) | Воронка продаж, поисковые запросы |
| 13 | [Отчёты](./13-reports.md) | Статистика, удержания, хранение |
| 14 | [Финансы](./14-finances.md) | Баланс, документы |
| 15 | [Тарифы](./15-tariffs.md) | Комиссии, логистика |
| 16 | [Общие](./16-general.md) | Проверка, пользователи, новости |

**Промпты для разработки:** [PROMPTS.md](./PROMPTS.md)

---

## Base URLs

| Категория | Base URL |
|-----------|----------|
| Common (общие) | `https://common-api.wildberries.ru` |
| Content (товары) | `https://content-api.wildberries.ru` |
| Prices (цены) | `https://discounts-prices-api.wildberries.ru` |
| Marketplace (заказы) | `https://marketplace-api.wildberries.ru` |
| Supplies (поставки FBW) | `https://supplies-api.wildberries.ru` |
| Statistics (статистика) | `https://statistics-api.wildberries.ru` |
| Analytics (аналитика) | `https://seller-analytics-api.wildberries.ru` |
| Advert (реклама) | `https://advert-api.wildberries.ru` |
| Feedbacks (отзывы) | `https://feedbacks-api.wildberries.ru` |
| Buyer Chat (чат) | `https://buyer-chat-api.wildberries.ru` |
| Sandbox (тест) | `https://*-api-sandbox.wildberries.ru` |

---

## Лимиты

| Категория | Лимит |
|-----------|-------|
| Content | 100 запросов/мин |
| Marketplace | 600 запросов/мин |
| Statistics | 1 запрос/мин (некоторые методы) |
| Analytics | 1 запрос/мин |
| Advert | 300 запросов/мин |
| Feedbacks | 3 запроса/сек |
| Buyer Chat | 10 запросов/10 сек |

---

## Частые сценарии

### Создать товар и установить цену

```
1. GET  /content/v2/object/charcs/{subjectId}  — характеристики категории
2. POST /content/v2/cards/upload               — создать карточку
3. POST /api/v2/upload/task                    — установить цену
```
**Раздел:** [Товары](./01-products.md), [Цены](./02-prices.md)

---

### Обновить карточку товара

```
1. POST /content/v2/get/cards/list   — получить текущие данные
2. POST /content/v2/cards/update     — обновить (полная перезапись)
```
**Раздел:** [Товары](./01-products.md)

---

### Обработать FBS заказ (полный цикл)

```
1. GET   /api/v3/orders/new                           — новые заказы
2. POST  /api/marketplace/v3/orders/meta              — метаданные
3. PUT   /api/v3/orders/{orderId}/meta/sgtin          — код маркировки
4. POST  /api/v3/supplies                             — создать поставку
5. PATCH /api/marketplace/v3/supplies/{id}/orders     — добавить заказы
6. POST  /api/v3/orders/stickers                      — стикеры
7. PATCH /api/v3/supplies/{supplyId}/deliver          — в доставку
```
**Раздел:** [Заказы FBS](./04-orders-fbs.md)

---

### Создать поставку FBS

```
1. POST  /api/v3/supplies                         — создать
2. PATCH /api/marketplace/v3/supplies/{id}/orders — добавить заказы
3. GET   /api/v3/supplies/{id}/barcode            — QR-код
4. PATCH /api/v3/supplies/{id}/deliver            — в доставку
```
**Раздел:** [Заказы FBS](./04-orders-fbs.md)

---

### Обработать DBS заказ

```
1. GET  /api/v3/dbs/orders/new                        — новые заказы
2. POST /api/v3/dbs/orders/client                     — данные покупателя
3. POST /api/marketplace/v3/dbs/orders/status/confirm — на сборку
4. POST /api/marketplace/v3/dbs/orders/status/deliver — в доставку
5. POST /api/marketplace/v3/dbs/orders/status/receive — получен
```
**Раздел:** [Заказы DBS](./05-orders-dbs.md)

---

### Ответить на отзывы

```
1. GET  /api/v1/feedbacks         — список отзывов
2. POST /api/v1/feedbacks/answer  — ответить
```
**Раздел:** [Отзывы](./10-feedbacks.md)

---

### Получить статистику продаж

```
1. GET /api/v1/supplier/sales   — продажи и возвраты
2. GET /api/v1/supplier/orders  — заказы
3. GET /api/v1/supplier/stocks  — остатки на складах WB
```
**Раздел:** [Отчёты](./13-reports.md)

---

### Создать рекламную кампанию

```
1. POST /api/advert/v1/bids/min    — минимальные ставки
2. POST /adv/v2/seacat/save-ad     — создать кампанию
3. POST /adv/v1/budget/deposit     — пополнить бюджет
4. GET  /adv/v0/start              — запустить
```
**Раздел:** [Реклама](./09-promotion.md)

---

### Участие в акции WB

```
1. GET  /api/v1/calendar/promotions               — список акций
2. GET  /api/v1/calendar/promotions/details       — детали
3. GET  /api/v1/calendar/promotions/nomenclatures — товары
4. POST /api/v1/calendar/promotions/upload        — добавить товар
```
**Раздел:** [Реклама](./09-promotion.md)

---

### Получить баланс

```
1. GET /api/v1/account/balance                — баланс
2. GET /api/v5/supplier/reportDetailByPeriod  — отчёт о реализации
```
**Раздел:** [Финансы](./14-finances.md)

---

> **Версия:** 2026-01
> **Источник:** [dev.wildberries.ru](https://dev.wildberries.ru)
