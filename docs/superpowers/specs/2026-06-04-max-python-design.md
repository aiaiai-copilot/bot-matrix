# Дизайн: ячейка `max/python` — echo-бот на maxapi

**Дата:** 2026-06-04
**Статус:** одобрен пользователем, готов к плану реализации

## Контекст

`bot-matrix` — учебная коллекция стартеров ботов, матрица «мессенджер × технология»
(раскладка `<мессенджер>/<технология>/`). На момент написания готовы 3 из 4 ячеек:
`max/typescript` (echo на `@maxhub/max-bot-api` + мок-харнесс), `telegram/python`
(echo на aiogram 3, live-проверен) и `telegram/typescript` (echo на grammY, live-проверен).
Задача — заполнить последнюю ячейку **MAX × Python**: минимальный запускаемый echo-бот,
следующий конвенциям уже готовых ячеек. Это закрывает матрицу до 4/4.

Зачем: завершить матрицу; дать ученику воспроизводимый, стилистически согласованный с
остальными ячейками пример MAX-бота на Python.

## Решения (приняты при брейншторме)

- **SDK — `maxapi`** (PyPI-пакет `maxapi`, репозиторий официальной org `max-messenger/max-botapi-python`,
  v0.9.4, Python ≥ 3.10). Его API почти 1:1 совпадает с aiogram: `Bot`, `Dispatcher`,
  `@dp.message_created(...)`, `event.message.answer(...)`, `dp.start_polling(bot)`. Это даёт
  согласованность сразу по двум осям матрицы — с MAX-осью (официальный SDK, как в `max/typescript`)
  и с Python-осью (aiogram-стиль, как в `telegram/python`). Альтернатива — сырой HTTP-клиент к
  modern-хосту `platform-api.max.ru` — отклонена: рвёт стилевую согласованность ради ухода с
  legacy-хоста, что для учебного стартера не оправдано.
- **Верификация — мок-харнесс `verify_local.py`** (как `verify-local.mjs` в `max/typescript`).
  Токен MAX недоступен физлицам/самозанятым (выдаётся только верифицированным ИП/юрлицам — резидентам
  РФ через business.max.ru), поэтому живой round-trip невозможен. Уверенность даёт прогон НАСТОЯЩЕГО
  SDK против локального фейкового MAX-сервера. Лёгкий юнит-тест хендлера и «только import-smoke»
  отклонены — мок-харнесс уже задал планку в `max/typescript`, держим её.
- **Поведение — `/start` + эхо.** Отдельный хендлер на `/start` с приветствием + эхо на остальной
  текст. Зеркалит Python-ось (`telegram/python`, `telegram/typescript`). (В `max/typescript` было
  чистое эхо без `/start` — здесь сознательно следуем Python-конвенции ячейки.)

## Ключевые факты SDK `maxapi` (выверены по исходникам, 2026-06-04)

- **Хост:** `API_URL = 'https://botapi.max.ru'` — legacy-хост, заданный class-атрибутом на
  `BaseConnection` (родитель `Bot`). Читается при создании `aiohttp.ClientSession(base_url=...)` →
  **переопределяется присваиванием `bot.API_URL = ...` до первого запроса** (основа мок-харнесса).
- **Токен:** передаётся в `Bot(token)` и кладётся в `self.params = {'access_token': token}` —
  то есть уходит **query-параметром** `access_token` (legacy-стиль MAX). В отличие от modern-хоста
  и TS-SDK, где токен идёт заголовком `Authorization: <token>`. Это образовательный нюанс для README.
- **Поллинг:** `dp.start_polling(bot)`; при активной webhook-подписке апдейты не приходят. У `Bot`
  есть флаг `auto_check_subscriptions` (по умолчанию проверяет подписки перед поллингом) и метод
  `bot.delete_webhook()`.
- **`auto_requests`** (по умолчанию `True`): SDK может дозапрашивать поля `chat`/`from_user` через API.
  В харнессе выключим (`auto_requests=False`), чтобы не плодить эндпоинты в моке.

## Структура файлов

Зеркалит `telegram/python` + `max/typescript`:

```
max/python/
├── bot.py            ← echo-бот: /start + эхо текста
├── verify_local.py   ← мок-харнесс: настоящий SDK против фейкового MAX
├── requirements.txt  ← maxapi, python-dotenv
├── .env.example      ← BOT_TOKEN= + инструкция про @MasterBot / business.max.ru
├── .gitignore        ← .venv/  __pycache__/  *.pyc  .env
└── README.md         ← запуск, токен, «как устроено», блок проверки без токена
```

## Компоненты

### `bot.py` — бот

Стиль как у `telegram/python` (asyncio, logging, async-хендлеры):

```python
import asyncio
import logging
import os
import sys

from maxapi import Bot, Dispatcher
from maxapi.types import MessageCreated, Command
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger("echo-bot")

dp = Dispatcher()


@dp.message_created(Command("start"))
async def on_start(event: MessageCreated) -> None:
    await event.message.answer("Привет! Я эхо-бот. Напиши мне что-нибудь — отвечу тем же.")


@dp.message_created()
async def echo(event: MessageCreated) -> None:
    text = event.message.body.text
    if not text:
        return
    logger.info("← получено: %s  → отвечаю тем же", text)
    await event.message.answer(text)


async def main() -> None:
    token = os.getenv("BOT_TOKEN")
    if not token:
        sys.exit(
            "BOT_TOKEN не задан. Скопируйте .env.example в .env и вставьте токен бота MAX "
            "(см. README — токен выдаётся через business.max.ru)."
        )
    bot = Bot(token)
    await bot.delete_webhook()  # иначе при активной webhook-подписке поллинг молчит
    logger.info("🤖 MAX echo-бот запущен (long polling). Напишите ему в MAX.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
```

Поведение:
- `/start` → приветствие. Командный фильтр перехватывает апдейт раньше echo-хендлера —
  приветствие не дублируется эхом (как `CommandStart` vs `F.text` в `telegram/python`).
- Любой текст → тот же текст обратно, с логом `← получено: ...` (единый формат лога матрицы).
- Пустой/нетекстовый body → `if not text: return` (не шлём пустой ответ — как guard в `max/typescript`).
- Нет токена → `sys.exit(...)` с подсказкой, в сеть не лезет.

> На этапе реализации против исходников `maxapi` финально выверяются (это деталь плана, не дизайна):
> точное имя атрибута входящего текста (`event.message.body.text` vs `event.message.text`); сигнатуры
> фильтров (`Command`, `message_created`); имя метода сброса webhook перед поллингом
> (`bot.delete_webhook()` vs `bot.unsubscribe_webhook(...)`) — либо вовсе опора на дефолтный
> `auto_check_subscriptions=True`, если явный сброс не нужен.

### `verify_local.py` — мок-харнесс (ключевая часть)

Идея ровно как у `max/typescript/verify-local.mjs`, но на Python + `aiohttp` (он и так в зависимостях `maxapi`):

- Поднимает фейковый MAX-сервер на `127.0.0.1:<random-port>`, переопределяет `bot.API_URL` на него.
- Бот создаётся с `auto_requests=False` и `auto_check_subscriptions=False`, чтобы SDK не дёргал
  лишние эндпоинты. Мок отвечает на минимум: `GET /me`, `GET /updates` (один `message_created` с
  текстом + probe-апдейт с пустым текстом), `POST /messages` (ловим эхо).
- Обработчик в харнессе — дословная копия логики `bot.py` (как в TS-ячейке; та же оговорка
  «правьте оба места»).
- Проверяет:
  - ✅ happy path: на текст бот ответил **тем же текстом** в **тот же чат** (`POST /messages` с
    нужным `chat_id` и `body.text`);
  - ✅ авторизация: токен ушёл **query-параметром `access_token`** (legacy-MAX, не заголовок);
  - 🔍 probe: на пустой текст ответа НЕ было (ровно один `POST /messages`).
- Exit `0` при PASS, `1` при FAIL/таймауте.

> Формы JSON в ответах мока должны проходить pydantic-валидацию моделей `maxapi`
> (`GET /updates` → модель `GettedUpdates`, `GET /me` → `User`). Точные поля выверяются на этапе
> реализации против `maxapi/types` и `maxapi/methods/types`. Это деталь плана.

### `requirements.txt`

```
maxapi>=0.9,<1
python-dotenv>=1.0,<2
```

### `.env.example`

```
# Токен бота MAX.
# Токен выдаётся через бизнес-платформу business.max.ru (верификация ИП/юрлица — резидента РФ).
# Физлицам и самозанятым токен недоступен — для проверки кода используйте `python verify_local.py`.
# Скопируйте этот файл в .env и вставьте токен.
BOT_TOKEN=
```

### `.gitignore`

`.venv/`, `__pycache__/`, `*.pyc`, `.env` (как в `telegram/python`).

### `README.md`

По образцу соседей, адаптировано под MAX/Python:
- Что это: минимальный echo-бот для MAX на Python, официальный SDK `maxapi`.
- Требования: Python ≥ 3.10, аккаунт MAX.
- Получить токен: через `business.max.ru` (верификация ИП/юрлица — резидента РФ); честная оговорка,
  что физлицам/самозанятым токен недоступен → для проверки есть `verify_local.py`.
- Настроить и запустить: `python3 -m venv .venv` → `pip install -r requirements.txt` →
  `cp .env.example .env` (вписать токен) → `python bot.py`.
- «Как устроено»: `Dispatcher`, `@dp.message_created(...)`, `event.message.answer(...)`,
  `dp.start_polling(bot)`; событие `message_created`, `/start` отдельным хендлером.
- Блок **«Проверка без токена»**: `python verify_local.py` — что делает мок-харнесс и что проверяет.
- Образовательный нюанс: legacy-хост `botapi.max.ru` + токен query-параметром `access_token`
  (vs modern `platform-api.max.ru` + заголовок `Authorization` у TS-SDK).
- Источники: SDK `maxapi` (<https://github.com/max-messenger/max-botapi-python>),
  Bot API MAX (<https://dev.max.ru/docs-api>), получение токена (<https://business.max.ru>).

### Корневой `README.md`

В таблице матрицы ячейка `MAX × Python` меняется с `—` на `✅ [`max/python`](max/python)`.
Матрица становится 4/4.

## Верификация (приёмка)

Живой тест невозможен (токен недоступен) — приёмка полностью оффлайн:

1. `cd max/python` → `python3 -m venv .venv` → `pip install -r requirements.txt`.
2. **Import-smoke:** `python -c "import bot"` — модуль импортируется без падения (хендлеры
   регистрируются на уровне модуля; `main()` не запускается без `__main__`).
3. **Guard без токена:** запуск `python bot.py` без `BOT_TOKEN` → `exit 1`, в сеть не лезет.
4. **Мок-харнесс (главное):** `python verify_local.py` → PASS (happy path + auth + probe).

## Вне области (YAGNI)

Не включаем (как и в других «тонких» стартерах): Docker, тест-фреймворк (pytest), webhook-сервер,
middleware, FSM/состояния, graceful shutdown, CI, эхо нетекстовых вложений. Могут появиться позже
отдельными тирами.
