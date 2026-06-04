# HANDOFF

**Date:** 2026-06-04
**Branch:** `main` — матрица ячеек **готова 4/4**. Последний содержательный коммит `417175c` docs(spec,plan) (2026-06-04); поверх — `docs(handoff)` этой сессии. Все коммиты сессии (и 4 неотправленных с прошлой сессии) **запушены** в `origin/main` — main синхронен с origin, дерево чистое.

Проект `bot-matrix` — учебная коллекция стартеров ботов (матрица «мессенджер × технология», раскладка `<мессенджер>/<технология>/`). Приватный GitHub `aiaiai-copilot/bot-matrix`. Реализованы **все 4/4** ячейки: `max/typescript`, `max/python`, `telegram/python`, `telegram/typescript`. Контекст — корневой `README.md` и memory (`~/.claude/projects/-Users-alexanderlapygin-Projects-bot-matrix/memory/`).

## Session 2026-06-04 (исполнение ячейки max/python → матрица 4/4 + пуш)

### Что сделано
- Реализована последняя ячейка **MAX × Python** по плану `docs/superpowers/plans/2026-06-04-max-python.md` через **subagent-driven-development** (имплементер + spec-ревью + quality-ревью на каждую задачу). Файлы `max/python/`: `requirements.txt`, `.gitignore`, `.env.example`, `bot.py` (echo + `/start`, long polling на `maxapi`), `verify_local.py` (мок-харнесс), `README.md`. Корневой README — матрица **4/4**.
- Финальное holistic-ревью всей ячейки: **«Ship it»** (нет Critical/Important). Оффлайн-приёмка зелёная: import-smoke (`handlers: 2`), guard без токена (`exit=1`, в сеть не лезет), `python verify_local.py` → `✅ PASS` (`exit=0`, все 4 проверки: эхо текста, `/start` отдельным хендлером, заголовок `Authorization`, пустой текст игнорируется).
- Актуализирован раздел получения токена в `max/typescript/README.md` (был устаревший путь через @MasterBot `/create` — теперь business.max.ru, как в `max/python`; обе MAX-ячейки больше не противоречат друг другу).
- **Полировка доков:** инлайн SDK-факты в `docs/superpowers/{specs,plans}/2026-06-04-max-python*.md` переписаны под 0.9.18 (хост `platform-api.max.ru`, заголовок `Authorization`, `bot.api_url`); встроенный код `verify_local.py` в плане и шаблон README в Task 4 выровнены с shipped; ⚠️-предупреждения заменены на нейтральную пометку «ℹ️ Версия». Секция «Решения» (исторический брейншторм) намеренно не тронута.

### Ключевой факт: maxapi 0.9.18 ≠ 0.9.4 (выверено по исходникам ДВАЖДЫ, независимо)
План/спека/прошлый handoff/память изначально описывали SDK по версии **0.9.4**. По факту установилась **0.9.18**, где SDK **мигрировал** на современный транспорт:
- Хост по умолчанию — **`https://platform-api.max.ru`** (`connection/base.py:33`), legacy `botapi.max.ru` в SDK **больше нет**.
- Авторизация — **HTTP-заголовок `Authorization`** (`bot.py:153`), НЕ query-параметр `access_token`.
- Override хоста — инстанс-атрибут **`bot.api_url`** (или `bot.set_api_url(...)`), НЕ class-attr `API_URL`.
- Подтвердилось и в 0.9.18 (не переоткрывать): импорты `from maxapi import Bot, Dispatcher, F` / `from maxapi.types import MessageCreated, CommandStart`; фильтры `CommandStart()` и `F.message.body.text`; порядок хендлеров (`/start` раньше echo); `auto_requests=True` (дефолт) обязателен; эндпоинты `/me`,`/updates`,`/chats/{id}`,`/messages`; `dp.event_handlers` (== 2); `event.message.body.text` / `event.message.answer(text)`.
- **Источник истины по SDK-фактам — `max/python/{verify_local.py,README.md}` и `memory/max-botapi-facts.md`** (обновлена). Spec/plan теперь тоже актуальны под 0.9.18 (см. «Полировка доков» выше).

### Коммиты этой сессии (все запушены)
- `957b5f9` chore(max/python): скаффолдинг ячейки (maxapi, конфиги)
- `9c1335d` feat(max/python): echo-бот на maxapi (long polling, /start + текст)
- `a725391` test(max/python): мок-харнесс verify_local (настоящий SDK против фейкового MAX)
- `fe23205` docs(max/python): README со стартом, обзором maxapi и проверкой без токена
- `41ff759` docs: матрица — MAX × Python готов (4/4)
- `5d6b0bb` docs(spec,plan): пометка о миграции maxapi 0.9.18 (platform-api.max.ru + Authorization)
- `2f8f3ee` docs(max/typescript): актуализировать получение токена
- `417175c` docs(spec,plan): актуализировать инлайн SDK-факты под maxapi 0.9.18
- (+ `docs(handoff)` этой сессии)

### Локальное состояние (не в git)
- `max/python/.venv` — **Python 3.12.13** (системный `python3` = 3.9.6 слишком стар для maxapi `>=3.10`; venv создан на `/opt/homebrew/bin/python3.12`). Gitignored. Установлен **maxapi 0.9.18**.
- `max/python/.env` **не создан** (guard рассчитывает на его отсутствие; создаётся только пользователем с реальным токеном).
- Запущенных процессов/ботов нет.

### Осталось недоделанным / carry-forward
- Матрица завершена 4/4, доки актуальны — открытых задач по стартерам нет.
- Уборка из прошлых сессий (НЕ блокирует ничего): тест-бот Telegram `@bm_ts_demo_bot` не удалён; `.env` в `telegram/python` и `telegram/typescript` не чищены (если не нужны — `/revoke` или `/deletebot` в BotFather + почистить оба `.env`).
- ⚠️ **НЕ переиспользовать токен `@showcase_notification_demo_bot`** (id `8434549141`): рабочий бот с активным webhook на живой Supabase-сервис `register-telegram-subscriber`; `deleteWebhook` сломал бы интеграцию. Деталь инцидента — `git show c732cc2:HANDOFF.md`. (К MAX-ячейкам не относится — MAX токена не требует; safety-контекст для будущих Telegram-тестов.)
