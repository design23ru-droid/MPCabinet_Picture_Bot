# Управление остатками

[← Назад к оглавлению](./README.md)

**Base URL:** `https://marketplace-api.wildberries.ru`

---

## Склады продавца

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/api/v3/offices` | Список офисов WB |
| GET | `/api/v3/warehouses` | Склады продавца |
| POST | `/api/v3/warehouses` | Создать склад |
| PUT | `/api/v3/warehouses/{warehouseId}` | Обновить склад |
| DELETE | `/api/v3/warehouses/{warehouseId}` | Удалить склад |
| GET | `/api/v3/dbw/warehouses/{warehouseId}/contacts` | Контакты склада |
| PUT | `/api/v3/dbw/warehouses/{warehouseId}/contacts` | Обновить контакты |

---

## Остатки

| Метод | Endpoint | Описание |
|-------|----------|----------|
| PUT | `/api/v3/stocks/{warehouseId}` | Обновить остатки |
| DELETE | `/api/v3/stocks/{warehouseId}` | Обнулить остатки |
| POST | `/api/v3/stocks/{warehouseId}` | Получить остатки |

**Формат обновления:**
```json
{
  "stocks": [
    {"sku": "артикул", "amount": 100}
  ]
}
```

---

[← Цены](./02-prices.md) | [Назад к оглавлению](./README.md) | [Далее: Заказы FBS →](./04-orders-fbs.md)
