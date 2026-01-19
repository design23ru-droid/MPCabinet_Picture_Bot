# Заказы FBS

[← Назад к оглавлению](./README.md)

**Base URL:** `https://marketplace-api.wildberries.ru`

---

## Сборочные задания

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/api/v3/orders/new` | Новые сборочные задания |
| GET | `/api/v3/orders` | Информация о заданиях |
| POST | `/api/v3/orders/status` | Статусы заданий |
| GET | `/api/v3/supplies/orders/reshipment` | Задания для повторной отгрузки |
| PATCH | `/api/v3/orders/{orderId}/cancel` | Отменить задание |
| POST | `/api/v3/orders/stickers` | Получить стикеры |
| POST | `/api/v3/orders/stickers/cross-border` | Стикеры кроссбордера (PDF) |
| POST | `/api/v3/orders/status/history` | История статусов кроссбордера |
| POST | `/api/v3/orders/client` | Информация о клиенте |

**Важно:** Заказы автоматически переходят в "На сборке" через 10 минут.

---

## Метаданные (маркировка)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/api/marketplace/v3/orders/meta` | Получить метаданные заданий |
| DELETE | `/api/v3/orders/{orderId}/meta` | Удалить метаданные |
| PUT | `/api/v3/orders/{orderId}/meta/sgtin` | Добавить код маркировки |
| PUT | `/api/v3/orders/{orderId}/meta/uin` | Добавить УИН |
| PUT | `/api/v3/orders/{orderId}/meta/imei` | Добавить IMEI |
| PUT | `/api/v3/orders/{orderId}/meta/gtin` | Добавить GTIN |
| PUT | `/api/v3/orders/{orderId}/meta/expiration` | Добавить срок годности |
| PUT | `/api/marketplace/v3/orders/{orderId}/meta/customs-declaration` | Добавить номер ГТД |

---

## Поставки

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/api/v3/supplies` | Создать поставку |
| GET | `/api/v3/supplies` | Список поставок |
| GET | `/api/v3/supplies/{supplyId}` | Информация о поставке |
| DELETE | `/api/v3/supplies/{supplyId}` | Удалить поставку |
| PATCH | `/api/marketplace/v3/supplies/{supplyId}/orders` | Добавить заказы в поставку |
| GET | `/api/marketplace/v3/supplies/{supplyId}/order-ids` | ID заказов в поставке |
| PATCH | `/api/v3/supplies/{supplyId}/deliver` | Передать в доставку |
| GET | `/api/v3/supplies/{supplyId}/barcode` | QR-код поставки |

---

## Короба

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/api/v3/supplies/{supplyId}/trbx` | Список коробов поставки |
| POST | `/api/v3/supplies/{supplyId}/trbx` | Добавить короба |
| DELETE | `/api/v3/supplies/{supplyId}/trbx` | Удалить короба |
| POST | `/api/v3/supplies/{supplyId}/trbx/stickers` | Стикеры коробов |

---

## Пропуска

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/api/v3/passes/offices` | Склады, требующие пропуск |
| GET | `/api/v3/passes` | Список пропусков |
| POST | `/api/v3/passes` | Создать пропуск |
| PUT | `/api/v3/passes/{passId}` | Обновить пропуск |
| DELETE | `/api/v3/passes/{passId}` | Удалить пропуск |

---

[← Остатки](./03-stocks.md) | [Назад к оглавлению](./README.md) | [Далее: Заказы DBS →](./05-orders-dbs.md)
