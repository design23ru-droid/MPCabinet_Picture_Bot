# Ценообразование

[← Назад к оглавлению](./README.md)

**Base URL:** `https://discounts-prices-api.wildberries.ru`

---

## Установка цен

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/api/v2/upload/task` | Установить цены и скидки |
| POST | `/api/v2/upload/task/size` | Установить цены по размерам |
| POST | `/api/v2/upload/task/club-discount` | Установить скидки WB Club |

**Формат данных:**
```json
{
  "data": [
    {"nmID": 123, "price": 1000, "discount": 10}
  ]
}
```

**Важно:**
- Цена в рублях, скидка в процентах
- Изменения применяются до 15 минут
- Лимит: 1000 товаров за запрос

---

## Получение цен

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/api/v2/list/goods/filter` | Товары с ценами (фильтр) |
| POST | `/api/v2/list/goods/filter` | Товары по артикулам |
| GET | `/api/v2/list/goods/size/nm` | Размеры с ценами |

**Параметры GET:**
- `limit` — количество (макс. 1000)
- `offset` — смещение
- `filterNmID` — фильтр по nmID

---

## Статус загрузки

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/api/v2/history/tasks` | Статус обработанных загрузок |
| GET | `/api/v2/history/goods/task` | Детали обработки |
| GET | `/api/v2/buffer/tasks` | Статус необработанных загрузок |
| GET | `/api/v2/buffer/goods/task` | Детали необработанных |
| GET | `/api/v2/quarantine/goods` | Товары в карантине цен |

---

[← Товары](./01-products.md) | [Назад к оглавлению](./README.md) | [Далее: Остатки →](./03-stocks.md)
