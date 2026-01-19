# Продвижение и реклама

[← Назад к оглавлению](./README.md)

**Base URL:** `https://advert-api.wildberries.ru`

---

## Кампании

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/adv/v1/promotion/count` | Списки кампаний по типам и статусам |
| GET | `/api/advert/v2/adverts` | Информация о кампаниях |

---

## Создание кампаний

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/api/advert/v1/bids/min` | Минимальные ставки для товаров |
| POST | `/adv/v2/seacat/save-ad` | Создать кампанию |
| GET | `/adv/v1/supplier/subjects` | Предметы для кампаний |
| POST | `/adv/v2/supplier/nms` | Карточки товаров для кампаний |

**Типы кампаний (bid_type):**
- `unified` — единая ставка
- `manual` — ручная ставка

**Типы размещения (placement_types):**
- `search` — в поиске
- `recommendations` — в рекомендациях

---

## Управление кампаниями

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/adv/v0/delete` | Удалить кампанию |
| POST | `/adv/v0/rename` | Переименовать кампанию |
| GET | `/adv/v0/start` | Запустить кампанию |
| GET | `/adv/v0/pause` | Приостановить кампанию |
| GET | `/adv/v0/stop` | Завершить кампанию |
| PATCH | `/api/advert/v1/bids` | Изменить ставки |
| PUT | `/adv/v0/auction/placements` | Изменить размещения |
| PATCH | `/adv/v0/auction/nms` | Изменить список товаров |

---

## Поисковые кластеры

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/adv/v0/normquery/get-bids` | Получить ставки кластеров |
| POST | `/adv/v0/normquery/bids` | Установить ставки |
| DELETE | `/adv/v0/normquery/bids` | Удалить ставки |
| POST | `/adv/v0/normquery/get-minus` | Получить минус-фразы |
| POST | `/adv/v0/normquery/set-minus` | Установить минус-фразы |

---

## Финансы рекламы

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/adv/v1/balance` | Баланс рекламного кабинета |
| GET | `/adv/v1/budget` | Бюджет кампании |
| POST | `/adv/v1/budget/deposit` | Пополнить бюджет кампании |
| GET | `/adv/v1/upd` | История затрат |
| GET | `/adv/v1/payments` | История пополнений |

---

## Медиа-кампании

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/adv/v1/count` | Количество медиа-кампаний |
| GET | `/adv/v1/adverts` | Список медиа-кампаний |
| GET | `/adv/v1/advert` | Детали медиа-кампании |

---

## Статистика рекламы

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/adv/v0/normquery/stats` | Статистика кластеров |
| POST | `/adv/v2/fullstats` | Статистика кампаний (POST) |
| GET | `/adv/v3/fullstats` | Статистика кампаний (GET) |
| GET | `/adv/v2/auto/stat-words` | Статистика единой ставки |
| GET | `/adv/v1/stat/words` | Статистика ручной ставки |
| GET | `/adv/v0/stats/keywords` | Статистика ключевых слов |
| POST | `/adv/v1/stats` | Медиа-статистика |

**Важно:** Данные обновляются с задержкой до 3 часов.

---

## Календарь акций

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/api/v1/calendar/promotions` | Список акций |
| GET | `/api/v1/calendar/promotions/details` | Детали акции |
| GET | `/api/v1/calendar/promotions/nomenclatures` | Товары для акции |
| POST | `/api/v1/calendar/promotions/upload` | Добавить товар в акцию |

---

[← Поставки FBW](./08-supplies-fbw.md) | [Назад к оглавлению](./README.md) | [Далее: Отзывы →](./10-feedbacks.md)
