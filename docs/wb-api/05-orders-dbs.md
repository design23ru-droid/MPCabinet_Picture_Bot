# Заказы DBS

[← Назад к оглавлению](./README.md)

**Base URL:** `https://marketplace-api.wildberries.ru`

> DBS (Delivery by Seller) — доставка силами продавца

---

## Сборочные задания

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/api/v3/dbs/orders/new` | Новые задания |
| GET | `/api/v3/dbs/orders` | Завершённые задания |
| POST | `/api/v3/dbs/groups/info` | Информация о платной доставке |
| POST | `/api/v3/dbs/orders/client` | Информация о покупателе (адрес, телефон) |
| POST | `/api/v3/dbs/orders/delivery-date` | Дата и время доставки |

---

## Управление статусами

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/api/marketplace/v3/dbs/orders/status/info` | Получить статусы |
| POST | `/api/marketplace/v3/dbs/orders/status/cancel` | Отменить задания |
| POST | `/api/marketplace/v3/dbs/orders/status/confirm` | Перевести на сборку |
| POST | `/api/marketplace/v3/dbs/orders/status/deliver` | Перевести в доставку |
| POST | `/api/marketplace/v3/dbs/orders/status/receive` | Подтвердить получение |
| POST | `/api/marketplace/v3/dbs/orders/status/reject` | Сообщить об отказе |

---

## Метаданные

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/api/marketplace/v3/dbs/orders/meta/info` | Получить метаданные |
| POST | `/api/marketplace/v3/dbs/orders/meta/delete` | Удалить метаданные |
| POST | `/api/marketplace/v3/dbs/orders/meta/sgtin` | Добавить коды маркировки |
| POST | `/api/marketplace/v3/dbs/orders/meta/uin` | Добавить УИН |
| POST | `/api/marketplace/v3/dbs/orders/meta/imei` | Добавить IMEI |
| POST | `/api/marketplace/v3/dbs/orders/meta/gtin` | Добавить GTIN |
| POST | `/api/marketplace/v3/dbs/meta/customs-declaration` | Добавить номер ГТД |

---

[← Заказы FBS](./04-orders-fbs.md) | [Назад к оглавлению](./README.md) | [Далее: Заказы DBW →](./06-orders-dbw.md)
