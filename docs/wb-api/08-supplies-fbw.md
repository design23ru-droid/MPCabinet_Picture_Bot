# Поставки FBW

[← Назад к оглавлению](./README.md)

**Base URL:** `https://supplies-api.wildberries.ru`

> FBW (Fulfillment by Wildberries) — хранение и доставка силами WB

---

## Методы

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/api/v1/acceptance/options` | Опции приёмки |
| GET | `/api/v1/warehouses` | Список складов WB |
| GET | `/api/v1/transit-tariffs` | Транзитные направления |
| POST | `/api/v1/supplies` | Список поставок |
| GET | `/api/v1/supplies/{ID}` | Детали поставки |
| GET | `/api/v1/supplies/{ID}/goods` | Товары поставки |
| GET | `/api/v1/supplies/{ID}/package` | Упаковка поставки |

---

## Коэффициенты приёмки

Для получения коэффициентов используйте метод из раздела [Тарифы](./15-tariffs.md):

```
GET /api/tariffs/v1/acceptance/coefficients
```

**Рекомендация:** Выбирайте склады с минимальным коэффициентом — это снижает стоимость приёмки.

---

[← Самовывоз](./07-click-collect.md) | [Назад к оглавлению](./README.md) | [Далее: Реклама →](./09-promotion.md)
