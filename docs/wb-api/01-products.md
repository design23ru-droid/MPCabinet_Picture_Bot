# Управление товарами

[← Назад к оглавлению](./README.md)

**Base URL:** `https://content-api.wildberries.ru`

---

## Справочники

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/content/v2/object/parent/all` | Родительские категории товаров |
| GET | `/content/v2/object/all` | Список предметов (подкатегорий) |
| GET | `/content/v2/object/charcs/{subjectId}` | Характеристики предмета |
| GET | `/content/v2/directory/colors` | Справочник цветов |
| GET | `/content/v2/directory/kinds` | Справочник полов |
| GET | `/content/v2/directory/countries` | Справочник стран происхождения |
| GET | `/content/v2/directory/seasons` | Справочник сезонов |
| GET | `/content/v2/directory/vat` | Ставки НДС |
| GET | `/content/v2/directory/tnved` | Коды ТН ВЭД |
| GET | `/api/content/v1/brands` | Бренды по предмету |

---

## Создание карточек

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/content/v2/cards/limits` | Лимиты создания карточек |
| POST | `/content/v2/barcodes` | Генерация баркодов |
| POST | `/content/v2/cards/upload` | Создать карточки товаров |
| POST | `/content/v2/cards/upload/add` | Создать с объединением в существующую |

**Лимиты:**
- 100 карточек за запрос
- 30 номенклатур в каждой карточке
- 100 запросов/мин на контент

---

## Управление карточками

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/content/v2/get/cards/list` | Список карточек товаров |
| POST | `/content/v2/cards/error/list` | Карточки с ошибками |
| POST | `/content/v2/cards/update` | Редактирование карточек |
| POST | `/content/v2/cards/moveNm` | Объединить/разделить карточки |
| POST | `/content/v2/cards/delete/trash` | Переместить в корзину |
| POST | `/content/v2/cards/recover` | Восстановить из корзины |
| POST | `/content/v2/get/cards/trash` | Список карточек в корзине |

**Важно:** При обновлении передавайте ВСЕ поля карточки — она полностью перезаписывается.

---

## Медиафайлы

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/content/v3/media/file` | Загрузить медиафайл (multipart/form-data) |
| POST | `/content/v3/media/save` | Загрузить по ссылкам |

**Ограничения:**
- Фото: до 10 штук, JPG/PNG, до 10 МБ
- Видео: 1 штука, MP4, до 50 МБ

---

## Теги / Метки

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/content/v2/tags` | Список меток продавца |
| POST | `/content/v2/tag` | Создать метку |
| PATCH | `/content/v2/tag/{id}` | Редактировать метку |
| DELETE | `/content/v2/tag/{id}` | Удалить метку |
| POST | `/content/v2/tag/nomenclature/link` | Привязать/отвязать метку от товара |

**Лимит:** максимум 8 тегов на карточку

---

[← Назад к оглавлению](./README.md) | [Далее: Цены →](./02-prices.md)
