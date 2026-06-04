# MAX × Python echo-бот — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Заполнить последнюю ячейку матрицы — `max/python` — минимальным запускаемым echo-ботом на официальном SDK `maxapi`, следуя конвенциям ячеек `max/typescript` и `telegram/python`.

**Architecture:** Самостоятельный стартер в `max/python/`: `bot.py` (echo на `maxapi` long polling, `/start` + эхо текста), `verify_local.py` (мок-харнесс — настоящий SDK против фейкового MAX-сервера на aiohttp), конфиги (`requirements.txt`, `.env.example`, `.gitignore`), README. Живой тест невозможен (токен MAX недоступен физлицам/самозанятым), поэтому приёмка полностью оффлайн: import-smoke + guard без токена + мок-харнесс.

**Tech Stack:** Python ≥ 3.10, `maxapi` 0.9.4 (aiogram-подобный: `Bot`/`Dispatcher`/`@dp.message_created`/`F`), `python-dotenv`, `aiohttp` (транзитивно от `maxapi` — используется в харнессе).

**Спека:** `docs/superpowers/specs/2026-06-04-max-python-design.md`

---

## Замечание о верификации (нет тест-фреймворка)

Эта ячейка — «тонкий» стартер без pytest (как `max/typescript` и `telegram/python`). Роль «теста» играют: import-smoke (`python -c "import bot"`), guard-поведение (запуск без `BOT_TOKEN` → выход с кодом 1, без сети) и **мок-харнесс** `verify_local.py` (прогон настоящего SDK против локального фейкового MAX). Живой round-trip против реального MAX **невозможен** — токен недоступен (выдаётся только верифицированным ИП/юрлицам — резидентам РФ).

## Ключевые факты SDK (выверено по исходникам `max-messenger/max-botapi-python`, v0.9.4)

Эти факты — основа корректности кода ниже. Не менять без сверки с исходниками.

- Импорты: `from maxapi import Bot, Dispatcher, F`; `from maxapi.types import MessageCreated, CommandStart`.
- Хендлер: `@dp.message_created(<фильтр>)`; функция получает `event: MessageCreated`.
- Текст входящего: `event.message.body.text` (НЕ `event.message.text`). Ответ: `await event.message.answer(text)`.
- `CommandStart()` SDK разворачивает в магик-фильтр `F.message.body.text.split()[0] == '/start'` (см. `maxapi/filters/handler.py`). Хендлеры матчатся в порядке регистрации, первый совпавший побеждает → `on_start` регистрируем ПЕРВЫМ.
- `Bot(token)` кладёт токен в `self.params = {'access_token': token}` → токен идёт **query-параметром** `access_token` на всех запросах (legacy-хост `https://botapi.max.ru`).
- `API_URL = 'https://botapi.max.ru'` — class-атрибут `BaseConnection`; читается при ленивом создании `aiohttp.ClientSession(base_url=...)` → переопределяется присваиванием `bot.API_URL = <url>` ДО первого запроса (основа харнесса).
- `dp.start_polling(bot)`: `__ready` → (если `auto_check_subscriptions` → `GET /subscriptions`) → `check_me` (`GET /me`) → цикл `bot.get_updates()` (`GET /updates`, БЕЗ `marker` в запросе) → `process_update_request` → `handle`.
- `auto_requests=True` (дефолт): `enrich_event` для message-апдейта с `recipient.chat_id is not None` вызывает `GET /chats/{id}` И проставляет `message.bot`. При `auto_requests=False` функция выходит рано и `message.bot` остаётся `None` → `event.message.answer()` падает с `RuntimeError`. **Поэтому `auto_requests` оставляем дефолтным.**
- `answer(text)` → `send_message(chat_id=recipient.chat_id, ...)` → `POST /messages?access_token=…&chat_id=…`, тело `{"attachments": [], "text": <text>, "notify": null}`, ответ парсится в `SendedMessage` (`{"message": <Message>}`).

## Структура файлов

```
max/python/
├── bot.py            ← Task 2 — echo-бот: /start + эхо текста
├── verify_local.py   ← Task 3 — мок-харнесс (импортирует dp из bot.py)
├── requirements.txt  ← Task 1 — maxapi, python-dotenv
├── .env.example      ← Task 1 — BOT_TOKEN + инструкция про токен MAX
├── .gitignore        ← Task 1 — .venv/, __pycache__/, *.pyc, .env
└── README.md         ← Task 4 — запуск, токен, «как устроено», проверка без токена
```
Плюс Task 5 — правка корневого `README.md` (матрица 4/4).

---

## Task 1: Скаффолдинг ячейки (конфиги + venv + установка зависимостей)

**Files:**
- Create: `max/python/requirements.txt`
- Create: `max/python/.gitignore`
- Create: `max/python/.env.example`

- [ ] **Step 1: Создать `max/python/requirements.txt`**

```
maxapi>=0.9,<1
python-dotenv>=1.0,<2
```

- [ ] **Step 2: Создать `max/python/.gitignore`**

```
.venv/
__pycache__/
*.pyc
.env
```

- [ ] **Step 3: Создать `max/python/.env.example`**

```
# Токен бота MAX.
# Токен выдаётся через бизнес-платформу business.max.ru (верификация ИП/юрлица — резидента РФ).
# Физлицам и самозанятым токен недоступен — для проверки кода используйте `python verify_local.py`.
# Скопируйте этот файл в .env и вставьте токен.
BOT_TOKEN=
```

- [ ] **Step 4: Создать venv и установить зависимости**

Run:
```bash
cd max/python
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
Expected: установка без ошибок; `pip show maxapi` показывает `Version: 0.9.4` (или новее в пределах `<1`).

- [ ] **Step 5: Проверить, что SDK импортируется**

Run: `source .venv/bin/activate && python -c "from maxapi import Bot, Dispatcher, F; from maxapi.types import MessageCreated, CommandStart; print('ok')"`
Expected: вывод `ok`, без traceback. (Подтверждает, что имена из плана существуют в установленной версии SDK.)

- [ ] **Step 6: Commit**

```bash
git add max/python/requirements.txt max/python/.gitignore max/python/.env.example
git commit -m "chore(max/python): скаффолдинг ячейки (maxapi, конфиги)"
```

---

## Task 2: `bot.py` — echo-бот

**Files:**
- Create: `max/python/bot.py`

- [ ] **Step 1: Создать `max/python/bot.py`**

```python
import asyncio
import logging
import os
import sys

from maxapi import Bot, Dispatcher, F
from maxapi.types import MessageCreated, CommandStart
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger("echo-bot")

# Все хендлеры регистрируются на диспетчере (аналог aiogram Dispatcher).
# Порядок регистрации важен: /start раньше echo, чтобы команду не «съело» эхо.
dp = Dispatcher()


@dp.message_created(CommandStart())
async def on_start(event: MessageCreated) -> None:
    await event.message.answer("Привет! Я эхо-бот. Напиши мне что-нибудь — отвечу тем же.")


# Эхо: отвечаем тем же текстом. Фильтр F.message.body.text — только сообщения с текстом
# (на вложения без текста не реагируем, чтобы не слать пустой ответ).
@dp.message_created(F.message.body.text)
async def echo(event: MessageCreated) -> None:
    text = event.message.body.text
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
    logger.info("🤖 MAX echo-бот запущен (long polling). Напишите ему в MAX.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 2: Import-smoke — модуль импортируется, хендлеры регистрируются**

Run:
```bash
cd max/python && source .venv/bin/activate
python -c "import bot; print('handlers:', len(bot.dp.event_handlers))"
```
Expected: вывод `handlers: 2` (зарегистрированы `on_start` и `echo`), без traceback. `main()` не запускается (под `__main__`), в сеть не лезет.

- [ ] **Step 3: Guard без токена — чистый выход с кодом 1**

Run (без `.env`/`BOT_TOKEN` в окружении):
```bash
cd max/python && source .venv/bin/activate
env -u BOT_TOKEN python bot.py; echo "exit=$?"
```
Expected: печатается подсказка про `BOT_TOKEN`, `exit=1`, процесс завершается сразу (не висит на поллинге, в сеть не обращается).

> Примечание: если в `max/python/.env` уже лежит токен, `load_dotenv()` его подхватит и guard не сработает. Для этой проверки `.env` быть не должно (на этом этапе его и нет — создаётся только пользователем).

- [ ] **Step 4: Commit**

```bash
git add max/python/bot.py
git commit -m "feat(max/python): echo-бот на maxapi (long polling, /start + текст)"
```

---

## Task 3: `verify_local.py` — мок-харнесс

Прогоняет НАСТОЯЩИЙ SDK (`dp.start_polling`) против локального фейкового MAX-сервера. Хендлеры импортируются из `bot.py` (`from bot import dp`) — тестируются реальные обработчики, без дублирования.

**Files:**
- Create: `max/python/verify_local.py`

- [ ] **Step 1: Создать `max/python/verify_local.py`**

```python
# Локальная проверка echo-бота БЕЗ реального токена и БЕЗ обращения к проду MAX.
# Поднимаем фейковый MAX-сервер (aiohttp), направляем настоящий SDK на него (bot.API_URL),
# симулируем GET /updates и ловим исходящие POST /messages (это и есть эхо).
# Хендлеры берём из bot.py напрямую (from bot import dp) — гоняем реальные обработчики бота.
import asyncio
import socket
import sys

from aiohttp import web

from maxapi import Bot
from bot import dp  # реальные хендлеры on_start + echo, зарегистрированные на dp

# --- фикстуры входящих апдейтов ---
ECHO_TEXT = "Привет, MAX!"
GREETING = "Привет! Я эхо-бот. Напиши мне что-нибудь — отвечу тем же."
ECHO_CHAT_ID = 777
START_CHAT_ID = 779
PROBE_CHAT_ID = 888
TS = 1700000000000

posts = []            # пойманные POST /messages: {chat_id, text, access_token}
batch_delivered = False


def _user(uid, name, is_bot=False, username=None):
    return {
        "user_id": uid,
        "first_name": name,
        "username": username,
        "is_bot": is_bot,
        "last_activity_time": TS,
    }


def _message_update(chat_id, text):
    return {
        "update_type": "message_created",
        "timestamp": TS,
        "message": {
            "sender": _user(42, "Tester", username="tester"),
            "recipient": {"chat_id": chat_id, "chat_type": "dialog"},
            "timestamp": TS,
            "body": {"mid": f"mid-{chat_id}", "seq": 1, "text": text, "attachments": []},
        },
    }


# --- эндпоинты фейкового MAX ---
async def handle_me(request):
    return web.json_response(_user(1, "Echo Bot", is_bot=True, username="echo_bot"))


async def handle_updates(request):
    global batch_delivered
    if not batch_delivered:
        batch_delivered = True
        print("[mock] → отдаю 3 апдейта: текст, /start, probe(text=null)")
        return web.json_response({
            "marker": 100,
            "updates": [
                _message_update(ECHO_CHAT_ID, ECHO_TEXT),
                _message_update(START_CHAT_ID, "/start"),
                _message_update(PROBE_CHAT_ID, None),  # probe: нет текста → ответа быть не должно
            ],
        })
    # эмуляция long-poll: пусто с небольшой задержкой, чтобы не было busy-loop
    await asyncio.sleep(0.3)
    return web.json_response({"marker": 100, "updates": []})


async def handle_chat(request):
    # enrich_event дозапрашивает чат для каждого message-апдейта (auto_requests=True)
    chat_id = int(request.match_info["chat_id"])
    return web.json_response({
        "chat_id": chat_id,
        "type": "dialog",
        "status": "active",
        "last_event_time": TS,
        "participants_count": 2,
        "is_public": False,
    })


async def handle_messages(request):
    chat_id = request.query.get("chat_id")
    access_token = request.query.get("access_token")
    body = await request.json()
    print(f"[mock] ← POST /messages chat_id={chat_id} text={body.get('text')!r} access_token={access_token}")
    posts.append({"chat_id": chat_id, "text": body.get("text"), "access_token": access_token})
    resp_msg = {
        "sender": _user(1, "Echo Bot", is_bot=True),
        "recipient": {"chat_id": int(chat_id) if chat_id else None, "chat_type": "dialog"},
        "timestamp": TS,
        "body": {"mid": "srv-1", "seq": 2, "text": body.get("text"), "attachments": []},
    }
    return web.json_response({"message": resp_msg})


async def _shutdown(polling_task, runner, bot):
    dp.polling = False
    polling_task.cancel()
    try:
        await polling_task
    except asyncio.CancelledError:
        pass
    if bot.session:
        await bot.session.close()
    await runner.cleanup()


async def main() -> int:
    app = web.Application()
    app.router.add_get("/me", handle_me)
    app.router.add_get("/updates", handle_updates)
    app.router.add_get("/chats/{chat_id}", handle_chat)
    app.router.add_post("/messages", handle_messages)

    # пред-биндим сокет, чтобы узнать порт без приватных атрибутов aiohttp
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.SockSite(runner, sock)
    await site.start()

    base_url = f"http://127.0.0.1:{port}"
    print(f"[mock] фейковый MAX слушает {base_url}\n")

    # настоящий SDK, направленный на мок
    bot = Bot("test-token")
    bot.API_URL = base_url                  # перенаправляем на фейковый сервер
    bot.auto_check_subscriptions = False    # не дёргать GET /subscriptions перед поллингом
    # auto_requests НЕ трогаем (дефолт True) — иначе SDK не проставит message.bot и answer() упадёт

    polling_task = asyncio.create_task(dp.start_polling(bot))

    # ждём 2 ожидаемых POST'а (эхо + приветствие) максимум ~10с
    for _ in range(100):
        if len(posts) >= 2:
            break
        await asyncio.sleep(0.1)
    # пауза: дать шанс на возможный (нежелательный) ответ на probe
    await asyncio.sleep(1.0)

    await _shutdown(polling_task, runner, bot)

    # --- проверки ---
    echo_post = next((p for p in posts if p["chat_id"] == str(ECHO_CHAT_ID)), None)
    start_post = next((p for p in posts if p["chat_id"] == str(START_CHAT_ID)), None)

    text_ok = echo_post is not None and echo_post["text"] == ECHO_TEXT
    start_ok = start_post is not None and start_post["text"] == GREETING
    auth_ok = len(posts) > 0 and all(p["access_token"] == "test-token" for p in posts)
    probe_ok = len(posts) == 2 and not any(p["chat_id"] == str(PROBE_CHAT_ID) for p in posts)

    print("\n=== РЕЗУЛЬТАТ ===")
    print(f"✅ happy path — эхо текста:   {(echo_post['text'] if echo_post else None)!r}  (ожидали {ECHO_TEXT!r})  {'✅' if text_ok else '❌'}")
    print(f"✅ /start — приветствие:      {(start_post['text'] if start_post else None)!r}  (НЕ эхо '/start')  {'✅' if start_ok else '❌'}")
    print(f"✅ авторизация — access_token query на POST /messages  {'✅' if auth_ok else '❌'}")
    print(f"🔍 probe — POST'ов всего: {len(posts)}  (ожидали 2; на text=null ответа быть не должно)  {'✅' if probe_ok else '❌'}")

    ok = text_ok and start_ok and auth_ok and probe_ok
    print("\n✅ PASS: echo round-trip через настоящий SDK; /start отдельным хендлером; пустой текст проигнорирован."
          if ok else "\n❌ FAIL: см. отметки выше.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
```

- [ ] **Step 2: Запустить мок-харнесс**

Run:
```bash
cd max/python && source .venv/bin/activate
python verify_local.py; echo "exit=$?"
```
Expected: лог `[mock] → отдаю 3 апдейта…`, две строки `[mock] ← POST /messages` (chat 777 с текстом `Привет, MAX!`; chat 779 с приветствием), блок `=== РЕЗУЛЬТАТ ===` со всеми ✅, итоговое `✅ PASS`, `exit=0`.

- [ ] **Step 3: Если FAIL — отладка (НЕ менять факты SDK наугад)**

При расхождении сверяться с исходниками `maxapi` (раздел «Ключевые факты SDK» выше). Частые точки:
- pydantic-ошибка на `GET /updates`/`/chats`/`/messages` → не хватает обязательного поля в фикстуре (сверить с `maxapi/types/message.py`, `maxapi/types/chats.py`, `maxapi/types/users.py`).
- 0 POST'ов → `message.bot` не проставлен: проверить, что `auto_requests` НЕ выключен и мок отвечает на `GET /chats/{id}`.
- 3 POST'а вместо 2 → probe с `text=null` всё же сматчился: проверить фильтр `F.message.body.text`.

- [ ] **Step 4: Commit**

```bash
git add max/python/verify_local.py
git commit -m "test(max/python): мок-харнесс verify_local (настоящий SDK против фейкового MAX)"
```

---

## Task 4: `README.md` ячейки

**Files:**
- Create: `max/python/README.md`

- [ ] **Step 1: Создать `max/python/README.md`**

````markdown
# MAX × Python — echo-бот (стартер)

Минимальный запускаемый бот для мессенджера **MAX** на **Python**, использующий официальный
SDK [`maxapi`](https://github.com/max-messenger/max-botapi-python) (aiogram-подобный API).
Бот отвечает тем же текстом, что ему прислали (echo).

## Требования

- **Python ≥ 3.10**
- Аккаунт в мессенджере MAX (для боевого запуска — токен бота, см. ниже)

## 1. Получить токен бота

Токен бота MAX выдаётся через бизнес-платформу [business.max.ru](https://business.max.ru):
регистрация → верификация по ИНН (ИП/юрлицо — резидент РФ) → создание бота → модерация →
токен в разделе «Чат-боты → Интеграция».

> ⚠️ **Токен недоступен физлицам и самозанятым** (только верифицированным ИП/юрлицам — резидентам РФ).
> Чтобы убедиться, что код работает, без токена — есть локальная проверка `python verify_local.py`
> (см. раздел ниже). Токен — прямой доступ к боту, не публикуйте его.

## 2. Настроить и запустить

```bash
cd max/python

# виртуальное окружение
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# зависимости
pip install -r requirements.txt

# конфигурация
cp .env.example .env               # затем впишите BOT_TOKEN=... в .env

# запуск (long polling)
python bot.py
```

Напишите боту в MAX — он ответит тем же текстом; на `/start` пришлёт приветствие.

## Как это устроено

```python
dp = Dispatcher()

@dp.message_created(CommandStart())
async def on_start(event: MessageCreated):
    await event.message.answer("Привет! ...")

@dp.message_created(F.message.body.text)
async def echo(event: MessageCreated):
    await event.message.answer(event.message.body.text)

await dp.start_polling(bot)
```

- `Dispatcher` маршрутизирует апдейты; хендлеры вешаются декораторами `@dp.message_created(...)`
  (≈ aiogram). `CommandStart()` отбирает `/start`, `F.message.body.text` — текстовые сообщения.
- `event.message.answer(...)` отправляет ответ в тот же чат; текст входящего — `event.message.body.text`.
- `dp.start_polling(bot)` запускает long polling (опрос `GET /updates`).

### Нюанс MAX-API (Python SDK)

`maxapi` работает с **legacy-хостом `https://botapi.max.ru`** и передаёт токен **query-параметром**
`access_token`. (Для сравнения: современный TypeScript-SDK `@maxhub/max-bot-api` из соседней ячейки
использует хост `platform-api.max.ru` и заголовок `Authorization: <token>`.)

## Проверка без токена (`python verify_local.py`)

Токен MAX недоступен физлицам/самозанятым, поэтому живой запуск не для всех возможен. Локальная
проверка [`verify_local.py`](verify_local.py) поднимает **фейковый MAX-сервер** на `localhost`,
направляет на него настоящий SDK (через `bot.API_URL`), симулирует входящие апдейты и проверяет
исходящие ответы:

```bash
python verify_local.py
```

- ✅ на текст бот отвечает тем же текстом в тот же чат;
- ✅ на `/start` приходит приветствие (отдельным хендлером, не эхом);
- ✅ авторизация — токен query-параметром `access_token`;
- 🔍 на сообщение без текста ответа нет.

> Проверка подтверждает корректность **кода и интеграции с SDK**; она не заменяет проверку против
> реального MAX (для неё нужен токен), но это максимально близкий воспроизводимый аналог. Хендлеры
> импортируются из `bot.py` — харнесс гоняет настоящие обработчики бота.

## Источники

- Официальный SDK: <https://github.com/max-messenger/max-botapi-python> (PyPI `maxapi`)
- Документация Bot API: <https://dev.max.ru/docs-api>
- Получение токена: <https://business.max.ru>
````

- [ ] **Step 2: Проверить ссылки и команды глазами**

Прочитать README, сверить: команды запуска совпадают с Task 1–3; имена файлов (`verify_local.py`, `bot.py`) и SDK-фактов (хост, `access_token`) — с реализацией.
Expected: расхождений нет.

- [ ] **Step 3: Commit**

```bash
git add max/python/README.md
git commit -m "docs(max/python): README со стартом, обзором maxapi и проверкой без токена"
```

---

## Task 5: Обновить корневой `README.md` (матрица 4/4)

**Files:**
- Modify: `README.md` (корень репозитория, строка таблицы матрицы со строкой **MAX**)

- [ ] **Step 1: Заменить ячейку MAX × Python в таблице**

В таблице «Матрица стартеров» строка **MAX** меняет правую ячейку с `—` на ссылку.

Было:
```markdown
| **MAX**               | ✅ [`max/typescript`](max/typescript) | — |
```
Стало:
```markdown
| **MAX**               | ✅ [`max/typescript`](max/typescript) | ✅ [`max/python`](max/python) |
```

- [ ] **Step 2: Проверить, что матрица полна (4/4)**

Run: `grep -c "✅" README.md`
Expected: `4` (все четыре ячейки готовы).

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: матрица — MAX × Python готов (4/4)"
```

---

## Финальная приёмка (после всех задач)

Все команды из `max/python/` при активированном `.venv`:

- [ ] `python -c "import bot; print(len(bot.dp.event_handlers))"` → `2`, без traceback.
- [ ] `env -u BOT_TOKEN python bot.py; echo $?` → подсказка про `BOT_TOKEN` + код `1` (в сеть не лезет).
- [ ] `python verify_local.py; echo $?` → `✅ PASS` + код `0`.
- [ ] `git status` → чисто; корневой README показывает матрицу 4/4.

## Вне области (YAGNI)

Не включаем: Docker, pytest, webhook-сервер (`maxapi[webhook]`/FastAPI), middleware, FSM/состояния, graceful shutdown, CI, эхо нетекстовых вложений. Могут появиться позже отдельными тирами.
