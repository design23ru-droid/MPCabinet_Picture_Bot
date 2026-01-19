# Заказы DBW

[← Назад к оглавлению](./README.md)

**Base URL:** `https://marketplace-api.wildberries.ru`

> DBW — доставка со склада продавца курьером Wildberries

---

## Сборочные задания

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/api/v3/dbw/orders/new` | Новые задания |
| GET | `/api/v3/dbw/orders` | Завершённые задания |
| POST | `/api/v3/dbw/orders/delivery-date` | Дата и время доставки |
| POST | `/api/v3/dbw/orders/status` | Статусы заданий |
| PATCH | `/api/v3/dbw/orders/{orderId}/confirm` | Перевести на сборку |
| POST | `/api/v3/dbw/orders/stickers` | Получить стикеры |
| PATCH | `/api/v3/dbw/orders/{orderId}/assemble` | Перевести в доставку |
| POST | `/api/v3/dbw/orders/courier` | Информация о курьере |
| PATCH | `/api/v3/dbw/orders/{orderId}/cancel` | Отменить задание |

---

## Метаданные

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/api/v3/dbw/orders/{orderId}/meta` | Получить метаданные |
| DELETE | `/api/v3/dbw/orders/{orderId}/meta` | Удалить метаданные |
| PUT | `/api/v3/dbw/orders/{orderId}/meta/sgtin` | Добавить код маркировки |
| PUT | `/api/v3/dbw/orders/{orderId}/meta/uin` | Добавить УИН |
| PUT | `/api/v3/dbw/orders/{orderId}/meta/imei` | Добавить IMEI |
| PUT | `/api/v3/dbw/orders/{orderId}/meta/gtin` | Добавить GTIN |

---

[← Заказы DBS](./05-orders-dbs.md) | [Назад к оглавлению](./README.md) | [Далее: Самовывоз →](./07-click-collect.md)
