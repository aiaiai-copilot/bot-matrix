# HANDOFF

**Date:** 2026-06-11
**Branch:** `main` — дерево чистое, **2 коммита впереди origin** (не запушены: `7c1193c` handoff прошлой сессии + `1b46c45` спек VK; push — решение пользователя). Последний коммит `1b46c45` docs(spec) (2026-06-11).

Проект `bot-matrix` — учебная коллекция стартеров ботов (матрица «мессенджер × технология», раскладка `<мессенджер>/<технология>/`). Приватный GitHub `aiaiai-copilot/bot-matrix`. Исходная матрица **4/4 готова** (`max/{python,typescript}`, `telegram/{python,typescript}`); идёт расширение — **строка VK** (→ 6/6). Контекст — корневой `README.md` и memory (`~/.claude/projects/-Users-alexanderlapygin-Projects-bot-matrix/memory/`).

## Session 2026-06-11 (брейншторм + спек строки VK; план — в следующей сессии)

### Что сделано
- **Брейншторм строки VK** (superpowers:brainstorming, дизайн одобрен пользователем). Решения: **обе ячейки сразу** (`vk/python` + `vk/typescript`), один спек на строку; SDK — **vkbottle 4.9.0 + vk-io 4.10.1** (де-факто стандарты; vk_api/vkwave/node-vk-bot-api отклонены); приветствие — **по payload `{"command":"start"}`** (конвенция кнопки «Начать», в VK нет `/start`); мок-харнессы в обеих ячейках (настоящий SDK против фейкового VK); **живая приёмка будет** — пользователь создаст тестовое сообщество VK (токен бесплатный/мгновенный).
- **Исследование выполнено и зафиксировано в спеке** — НЕ переисследовать: 2 агента по реестрам/исходникам + 2 агента с эмпирическими прогонами настоящих SDK против локальных моков. Все факты (домен `api.vk.ru`, API 5.199, формы апдейтов/ответов, ловушки моков: `fwd_messages: []` и `version` у vkbottle, `agent: undefined` и `client_info` у vk-io, `BotLabeler`-паттерн для переиспользования хендлеров) — в спеке.
- **Спек написан, самопроверен, закоммичен:** `docs/superpowers/specs/2026-06-11-vk-row-design.md` (включая эскизы `bot.py` и `src/handlers.ts`+`src/index.ts`, дизайн обоих verify_local, README-планы, приёмку).
- Memory: создан `telegram-prod-bot-safety.md` (туда переехало ⚠️-предупреждение о токене `@showcase_notification_demo_bot` и carry-forward уборки Telegram из старых handoff-блоков).

### Следующий шаг (указание пользователя: «Переходи к плану, но в новой сессии»)
1. Прочитать спек `docs/superpowers/specs/2026-06-11-vk-row-design.md` (он самодостаточен).
2. Invoke **superpowers:writing-plans** → план в `docs/superpowers/plans/2026-06-11-vk-row.md` (один план, задачи по ячейкам; образец — `docs/superpowers/plans/2026-06-04-max-python.md`).
3. Исполнение — subagent-driven-development (имплементер + spec-ревью + quality-ревью на задачу), как в max/python.
4. Перед **живой** приёмкой — явное «да» пользователя (глобальное правило про тесты к живым сервисам); по спеку живой прогон: сначала «Начать» → приветствие, потом текст → эхо.
5. После приёмки: memory-файл `vk-botapi-facts.md` + строка в `MEMORY.md` (по спеку).

### Коммиты этой сессии
- `1b46c45` docs(spec): дизайн строки VK — ячейки vk/python (vkbottle) и vk/typescript (vk-io)
- (+ `docs(handoff)` этой сессии)

### Локальное состояние (не в git)
- Ничего нового не запущено; внешних side-effects нет (живых VK/Telegram-вызовов не было).
- Из прошлых сессий остаётся: `max/python/.venv` (Python 3.12.13 с `/opt/homebrew/bin/python3.12`; системный `python3` = 3.9.6 — слишком стар и для vkbottle ≥3.10, для `vk/python` использовать тот же путь); `.env` в `telegram/{python,typescript}` (см. memory `telegram-prod-bot-safety.md`).

### Осталось недоделанным
- **План и реализация строки VK** — сознательно отложены в следующую сессию (см. «Следующий шаг»).
- Тестовое сообщество VK ещё не создано (понадобится к живой приёмке, создаёт пользователь).
- Уборка Telegram-артефактов — перенесена в memory `telegram-prod-bot-safety.md`, здесь больше не дублируется.
