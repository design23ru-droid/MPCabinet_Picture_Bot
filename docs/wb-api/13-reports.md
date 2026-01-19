# Статистика и отчёты

[← Назад к оглавлению](./README.md)

**Base URL:** `https://statistics-api.wildberries.ru`

---

## Основные отчёты

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/api/v1/supplier/stocks` | Остатки на складах WB |
| GET | `/api/v1/supplier/orders` | Заказы (до 90 дней) |
| GET | `/api/v1/supplier/sales` | Продажи и возвраты (до 90 дней) |

**Параметры:**
- `dateFrom` — дата начала
- `flag` — 0 (все данные) или 1 (только изменения)

**Важно:**
- Данные хранятся до 90 дней
- Обновление каждые 30 минут
- Лимит: 1 запрос/мин для некоторых методов

---

## Остатки на складах

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/api/v1/warehouse_remains` | Создать отчёт |
| GET | `/api/v1/warehouse_remains/tasks/{task_id}/status` | Статус отчёта |
| GET | `/api/v1/warehouse_remains/tasks/{task_id}/download` | Скачать отчёт |

---

## Удержания

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/api/analytics/v1/measurement-penalties` | Занижение габаритов |
| GET | `/api/analytics/v1/warehouse-measurements` | Замеры склада |
| GET | `/api/analytics/v1/deductions` | Подмены и неверные вложения |
| GET | `/api/v1/analytics/antifraud-details` | Самовыкупы |
| GET | `/api/v1/analytics/goods-labeling` | Маркировка товара |

---

## Платная приёмка

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/api/v1/acceptance_report` | Создать отчёт |
| GET | `/api/v1/acceptance_report/tasks/{task_id}/status` | Статус отчёта |
| GET | `/api/v1/acceptance_report/tasks/{task_id}/download` | Скачать отчёт |

---

## Платное хранение

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/api/v1/paid_storage` | Создать отчёт |
| GET | `/api/v1/paid_storage/tasks/{task_id}/status` | Статус отчёта |
| GET | `/api/v1/paid_storage/tasks/{task_id}/download` | Скачать отчёт |

---

## Прочие отчёты

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/api/v1/analytics/excise-report` | Маркированные товары |
| GET | `/api/v1/analytics/region-sale` | Продажи по регионам |
| GET | `/api/v1/analytics/brand-share/brands` | Бренды продавца |
| GET | `/api/v1/analytics/brand-share/parent-subjects` | Родительские категории бренда |
| GET | `/api/v1/analytics/brand-share` | Доля бренда в продажах |
| GET | `/api/v1/analytics/banned-products/blocked` | Заблокированные карточки |
| GET | `/api/v1/analytics/banned-products/shadowed` | Скрытые из каталога |
| GET | `/api/v1/analytics/goods-return` | Возвраты и перемещения |

---

[← Аналитика](./12-analytics.md) | [Назад к оглавлению](./README.md) | [Далее: Финансы →](./14-finances.md)
