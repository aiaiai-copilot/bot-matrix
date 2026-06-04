# HANDOFF

**Date:** 2026-06-04
**Branch:** `main` — код синхронен с origin на коммите `a5fca12` (последний запушенный, 2026-06-04). Всё, что после, **не запушено** (по решению пользователя): handoff'ы, spec/план и реализация ячейки `telegram/typescript` → после этого HANDOFF-коммита `main` на **9 коммитов впереди `origin/main`**.

Проект `bot-matrix` — учебная коллекция стартеров ботов (матрица «мессенджер × технология», раскладка `<мессенджер>/<технология>/`). Приватный GitHub `aiaiai-copilot/bot-matrix`. Готово **3/4** ячейки: `max/typescript`, `telegram/python`, `telegram/typescript` (все проверены — live или локально). Осталась `max/python`. Контекст — корневой `README.md` и memory (`~/.claude/projects/-Users-alexanderlapygin-Projects-bot-matrix/memory/`).

## Session 2026-06-04 (ячейка telegram/typescript)

Заполнена ячейка **Telegram × TypeScript** — echo-бот на grammY. Прошёл полный workflow: brainstorm → spec → план → реализация (inline) → live-тест.

### Что сделано
- Новая ячейка `telegram/typescript`: echo на **grammY 1.43** (long polling, `bot.command('start')` + `bot.on('message:text')` → `ctx.reply`). Структура зеркалит `max/typescript`: `src/index.ts`, `package.json`, `tsconfig.json`, `.env.example`, `.gitignore`, `README.md`; скрипты `dev`/`start`/`build`/`typecheck` (через `tsx`/`tsc`).
- **Оффлайн-приёмка:** `npm run typecheck` ✅, `npm run build` ✅, guard-запуск без токена → `exit 1` (в сеть не лезет). `verify:local` НЕ делали (в отличие от `max/typescript`) — токен Telegram бесплатен, проверка живая.
- **Live round-trip подтверждён** на тест-боте `@bm_ts_demo_bot`: `/start` → приветствие (эхом НЕ возвращается — `bot.command('start')` «съедает» апдейт, не доходя до echo-хендлера); текст `grammy тест 456` → эхо тем же. Серверный лог (`← получено: ...`) и чат пользователя сошлись.
- Обновлён корневой `README.md` — матрица: Telegram × TypeScript → готово.
- Артефакты процесса: spec `docs/superpowers/specs/2026-06-04-telegram-typescript-design.md`, план `docs/superpowers/plans/2026-06-04-telegram-typescript.md`.

### Решения
- **Фреймворк — grammY** (ctx-API почти 1:1 с `@maxhub/max-bot-api` из ячейки MAX → стилевая согласованность матрицы). Альтернативы (Telegraf, голый Bot API) отклонены.
- **Верификация — live (BotFather) + typecheck/build, без мок-харнесса** (мок нужен только `max/typescript`, т.к. токен MAX недоступен физлицам).
- Работали **прямо в `main`** по явному согласию пользователя (как и вся история проекта); ничего не пушим.

### Локальное состояние (не в git)
- `telegram/typescript/.env` — токен тест-бота `@bm_ts_demo_bot` (СКОПИРОВАН из `telegram/python/.env`). gitignored, не чистили.
- `telegram/typescript/node_modules` + `dist/` — установлены/собраны (gitignored).
- `telegram/python/.env` + `.venv` — без изменений с прошлой сессии (тот же токен `@bm_ts_demo_bot`, aiogram-venv).
- `/tmp/tg-ts-echo-bot.log` — лог прогона (эфемерный). Запущенных процессов/ботов нет (echo остановлен `SIGTERM`).
- В реальный Telegram уходили только `/start` и `grammy тест 456` тест-боту самого пользователя — безопасно.

### ⚠️ Carry-forward (важный контекст для будущих Telegram-тестов)
- Тест-бот `@bm_ts_demo_bot` (id `8967840150`) — одноразовый, под тесты; webhook пустой; токен лежит в **обоих** `.env` (`telegram/python`, `telegram/typescript`).
- **НЕ переиспользовать токен `@showcase_notification_demo_bot`** (id `8434549141`): это рабочий бот с активным webhook на живой Supabase-сервис `register-telegram-subscriber`; `deleteWebhook` сломал бы интеграцию. Подробности инцидента — `git show c732cc2:HANDOFF.md`.

### Осталось недоделанным
- Матрица **3/4**. Остаётся одна ячейка: **MAX × Python** (учесть: офиц. Python-клиент `max-botapi-python` пока на legacy `botapi.max.ru` + токен query-параметром).
- Тест-бот `@bm_ts_demo_bot` не удалён; `.env` в обеих ячейках не чищены. Если не нужен — `/revoke` или `/deletebot` в BotFather + почистить оба `.env`.
- Ничего не запушено в origin (по решению пользователя) — 9 коммитов впереди.
