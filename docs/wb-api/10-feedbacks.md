# Отзывы и вопросы

[← Назад к оглавлению](./README.md)

**Base URL:** `https://feedbacks-api.wildberries.ru`

**Лимит:** 3 запроса/сек

---

## Вопросы

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/api/v1/new-feedbacks-questions` | Непросмотренные отзывы и вопросы |
| GET | `/api/v1/questions/count-unanswered` | Количество неотвеченных вопросов |
| GET | `/api/v1/questions/count` | Количество вопросов за период |
| GET | `/api/v1/questions` | Список вопросов |
| PATCH | `/api/v1/questions` | Работа с вопросами (просмотр, отклонение, ответ) |
| GET | `/api/v1/question` | Вопрос по ID |

**Состояния (state):**
- `none` — просмотрен
- `wbRu` — ответ опубликован
- `rejected` — отклонён

---

## Отзывы

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/api/v1/feedbacks/count-unanswered` | Количество неотвеченных отзывов |
| GET | `/api/v1/feedbacks/count` | Количество отзывов за период |
| GET | `/api/v1/feedbacks` | Список отзывов |
| POST | `/api/v1/feedbacks/answer` | Ответить на отзыв |
| PATCH | `/api/v1/feedbacks/answer` | Редактировать ответ |
| POST | `/api/v1/feedbacks/order/return` | Запрос возврата товара по отзыву |
| GET | `/api/v1/feedback` | Отзыв по ID |
| GET | `/api/v1/feedbacks/archive` | Архивные отзывы |

**Важно:** Редактировать ответ можно только 1 раз в течение 60 дней.

---

## Закреплённые отзывы

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/api/feedbacks/v1/pins` | Список закреплённых/незакреплённых |
| POST | `/api/feedbacks/v1/pins` | Закрепить отзывы |
| DELETE | `/api/feedbacks/v1/pins` | Открепить отзывы |
| GET | `/api/feedbacks/v1/pins/count` | Количество закреплённых |
| GET | `/api/feedbacks/v1/pins/limits` | Лимиты закрепления |

**Лимит:** 3-5 закреплённых отзывов на карточку (зависит от тарифа).

---

[← Реклама](./09-promotion.md) | [Назад к оглавлению](./README.md) | [Далее: Чат →](./11-chat.md)
