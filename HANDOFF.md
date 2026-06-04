# HANDOFF

**Date:** 2026-06-04
**Branch:** `main` — последний коммит `1167fe8` docs(plan): план реализации ячейки max/python (2026-06-04). `main` на **3 коммита впереди `origin/main`** (spec + план ячейки `max/python` — **не запушены** по решению пользователя). Ранее в этой сессии 9 накопленных коммитов **были запушены** в origin.

Проект `bot-matrix` — учебная коллекция стартеров ботов (матрица «мессенджер × технология», раскладка `<мессенджер>/<технология>/`). Приватный GitHub `aiaiai-copilot/bot-matrix`. Реализовано **3/4** ячейки: `max/typescript`, `telegram/python`, `telegram/typescript`. Для последней — **MAX × Python** — готовы spec и план реализации (код ещё **не написан**). Контекст — корневой `README.md` и memory (`~/.claude/projects/-Users-alexanderlapygin-Projects-bot-matrix/memory/`).

## Session 2026-06-04 (план ячейки max/python + пуш)

### Что сделано
- **Запушены** в `origin/main` 9 ранее накопленных коммитов (ячейка `telegram/typescript` + прежние хэндофы): диапазон `a5fca12..a0e7d2b`. Секреты не утекли (`.env` gitignored, в коммитах только `.env.example`). `main` теперь синхронен с origin по этим коммитам.
- Полный pre-implementation workflow для последней ячейки **MAX × Python** (brainstorm → spec → план), всё inline в этой сессии:
  - **Spec:** `docs/superpowers/specs/2026-06-04-max-python-design.md`.
  - **План:** `docs/superpowers/plans/2026-06-04-max-python.md` — 5 задач, реальный (не плейсхолдерный) код в каждом шаге, выверен по исходникам SDK.
- Глубокое исследование официального Python-SDK MAX по исходникам (репозиторий `max-messenger/max-botapi-python`, PyPI-пакет `maxapi` v0.9.4).

### Коммиты этой сессии (после пуша, НЕ запушены)
- `2dc7aef` docs(spec): дизайн ячейки max/python (echo на maxapi + мок-харнесс)
- `ec4c9dc` docs(spec): выверка max/python по исходникам maxapi (auto_requests, мок 4 эндпоинта)
- `1167fe8` docs(plan): план реализации ячейки max/python + правка spec (import dp в харнессе)

### Решения
- **SDK — `maxapi`** (aiogram-подобный: `Bot`/`Dispatcher`/`@dp.message_created`/`F`). Согласован с обеими осями матрицы (офиц. SDK как у MAX-оси + aiogram-стиль как у Python-оси). Альтернатива — сырой HTTP к modern-хосту `platform-api.max.ru` — отклонена (рвёт стилевую согласованность ради ухода с legacy-хоста).
- **Поведение — `/start` + эхо** (как Python-ось матрицы; в `max/typescript` было чистое эхо).
- **Верификация — мок-харнесс `verify_local.py`** (живой тест невозможен — токен MAX недоступен самозанятым/физлицам). Харнесс импортирует реальный `dp` из `bot.py` и гоняет настоящий SDK против фейкового MAX-сервера на `aiohttp`.
- **Исполнение плана отложено в НОВУЮ сессию**, выбран вариант **subagent-driven** (свежий субагент на задачу + ревью между задачами).

### Ключевые SDK-факты для max/python (выверены по исходникам — не переоткрывать заново)
- `maxapi` v0.9.4, Python ≥ 3.10. Импорты: `from maxapi import Bot, Dispatcher, F`; `from maxapi.types import MessageCreated, CommandStart`.
- Хост **legacy `https://botapi.max.ru`** (class-attr `Bot.API_URL`; переопределяется присваиванием на инстансе → основа мока). Токен — **query-параметр `access_token`** (НЕ заголовок `Authorization`).
- `auto_requests=True` (дефолт) ОБЯЗАТЕЛЕН: иначе `enrich_event` не проставит `message.bot` → `event.message.answer()` упадёт. Поэтому мок отвечает на **4** эндпоинта: `GET /me`, `GET /updates`, `GET /chats/{id}`, `POST /messages`.
- Текст входящего — `event.message.body.text`; ответ — `event.message.answer(text)`. `CommandStart()` SDK разворачивает в `F.message.body.text.split()[0] == '/start'`.
- Метода `bot.delete_webhook()` в SDK **нет** (только `subscribe/unsubscribe_webhook`) — в `bot.py` сброса webhook не делаем (свежий long-polling бот подписок не имеет).

### Следующий шаг (для новой сессии)
- Исполнить план `docs/superpowers/plans/2026-06-04-max-python.md` через **superpowers:subagent-driven-development**. Порядок задач: скаффолдинг (configs + venv + `pip install`) → `bot.py` → `verify_local.py` (мок-харнесс) → README ячейки → корневой README (матрица 4/4). Приёмка оффлайн: import-smoke + guard без токена + `python verify_local.py` → PASS.

### Локальное состояние (не в git)
- Запущенных процессов/ботов нет. `max/python/` ещё не существует (создаётся при исполнении плана) — venv/`.env` появятся на шаге скаффолдинга.

### Осталось недоделанным / carry-forward
- Матрица **3/4**: ячейка **max/python** — spec и план готовы, код НЕ написан.
- **3 коммита (spec+plan) не запушены** в origin (по решению пользователя).
- Уборка из прошлой сессии (НЕ блокирует max/python): тест-бот Telegram `@bm_ts_demo_bot` не удалён; `.env` в `telegram/python` и `telegram/typescript` не чищены (если не нужны — `/revoke` или `/deletebot` в BotFather + почистить оба `.env`).
- ⚠️ **НЕ переиспользовать токен `@showcase_notification_demo_bot`** (id `8434549141`): рабочий бот с активным webhook на живой Supabase-сервис `register-telegram-subscriber`; `deleteWebhook` сломал бы интеграцию. Деталь инцидента — `git show c732cc2:HANDOFF.md`. (К `max/python` не относится — MAX токена не требует; сохраняем как safety-контекст для будущих Telegram-тестов.)
