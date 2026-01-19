# Самовывоз (Click & Collect)

[← Назад к оглавлению](./README.md)

**Base URL:** `https://marketplace-api.wildberries.ru`

---

## Сборочные задания

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/api/v3/click-collect/orders/new` | Новые задания |
| GET | `/api/v3/click-collect/orders` | Завершённые задания |
| POST | `/api/v3/click-collect/orders/status` | Статусы заданий |
| PATCH | `/api/v3/click-collect/orders/{orderId}/confirm` | Перевести на сборку |
| PATCH | `/api/v3/click-collect/orders/{orderId}/prepare` | Готово к выдаче |
| POST | `/api/v3/click-collect/orders/client` | Информация о покупателе |
| POST | `/api/v3/click-collect/orders/client/identity` | Проверить принадлежность заказа |
| PATCH | `/api/v3/click-collect/orders/{orderId}/receive` | Заказ принят покупателем |
| PATCH | `/api/v3/click-collect/orders/{orderId}/reject` | Покупатель отказался |
| PATCH | `/api/v3/click-collect/orders/{orderId}/cancel` | Отменить задание |

---

## Метаданные

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/api/v3/click-collect/orders/{orderId}/meta` | Получить метаданные |
| DELETE | `/api/v3/click-collect/orders/{orderId}/meta` | Удалить метаданные |
| PUT | `/api/v3/click-collect/orders/{orderId}/meta/sgtin` | Добавить код маркировки |
| PUT | `/api/v3/click-collect/orders/{orderId}/meta/uin` | Добавить УИН |
| PUT | `/api/v3/click-collect/orders/{orderId}/meta/imei` | Добавить IMEI |
| PUT | `/api/v3/click-collect/orders/{orderId}/meta/gtin` | Добавить GTIN |

---

[← Заказы DBW](./06-orders-dbw.md) | [Назад к оглавлению](./README.md) | [Далее: Поставки FBW →](./08-supplies-fbw.md)
