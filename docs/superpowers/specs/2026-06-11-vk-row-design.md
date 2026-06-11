# Дизайн: строка VK — ячейки `vk/python` и `vk/typescript`

**Дата:** 2026-06-11
**Статус:** одобрен пользователем, готов к плану реализации

## Контекст

`bot-matrix` — учебная коллекция стартеров ботов, матрица «мессенджер × технология»
(раскладка `<мессенджер>/<технология>/`). Готовы 4/4 ячейки исходной матрицы:
`telegram/{python,typescript}` и `max/{python,typescript}` — все по одному контракту
(echo + приветствие, long polling, `.env.example`, README, в max-ячейках — мок-харнесс).
Задача — добавить строку **VK**: две ячейки сразу, `vk/python` и `vk/typescript`.
Матрица становится 6/6.

Зачем: расширить матрицу третьим мессенджером; дать ученику согласованные с остальными
ячейками примеры VK-бота сообщества на двух стеках.

## Решения (приняты при брейншторме)

- **Обе ячейки сразу, один спек на строку.** Ячейки зеркальны, платформенные VK-факты общие —
  один спек и один план с задачами по ячейкам экономят дублирование.
- **SDK: `vkbottle` (Python) + `vk-io` (TypeScript)** — де-факто стандарты экосистемы, оба активны
  (vkbottle 4.9.0 от 03.06.2026; vk-io 4.10.1 от 31.10.2025, коммиты до 02.2026). У VK нет
  первопартийного SDK ни для одного языка. Альтернативы отклонены: `vk_api` — жив, но sync, без
  декораторов, в режиме поддержки, base URL захардкожен (мок сложнее); `vkwave`, `node-vk-bot-api`,
  `easyvk` — мертвы (2021–2022); raw HTTP — рвёт стилевую согласованность матрицы (все ячейки на SDK).
- **Поведение — echo + приветствие по payload.** В VK нет `/start`; конвенция платформы — кнопка
  **«Начать»**, которая шлёт сообщение с `payload = {"command":"start"}` (подтверждено докой
  dev.vk.com). Хендлер приветствия матчится **по payload**, не по тексту: если юзер руками напишет
  слово «Начать» без payload — это обычный текст, сработает эхо. Нюанс документируется в README.
  Сообщение без текста (только вложения) — игнор. Без токена — выход с подсказкой, в сеть не лезем.
- **Верификация — мок-харнесс в обеих ячейках** (настоящий SDK против фейкового VK на localhost).
  Улучшение против старых TS-ячеек (где логика копировалась): хендлеры объявляются отдельно от
  создания бота и переиспользуются харнессом — в Python через `labeler` (аналог `from bot import dp`
  в max/python), в TS через `src/handlers.ts` с `registerHandlers(vk)`.
- **Живая приёмка будет:** пользователь создаёт тестовое сообщество VK (токен бесплатный, мгновенный),
  оба бота проверяются вживую. Мок-харнессы при этом остаются основной воспроизводимой проверкой.

## Ключевые факты платформы VK (выверены 2026-06-11)

- **Домен API — `api.vk.ru`** (с 30.09.2025 VK требует его вместо `api.vk.com`; оба SDK уже переехали).
- **Версия API — 5.199** (актуальная по dev.vk.com/ru/reference/versions; оба SDK пинят её же).
- **Bots Long Poll** — рекомендуемый транспорт без публичного URL: бот сам опрашивает сервер,
  очередь событий на стороне VK (в отличие от Callback API). При версии API ≥ 5.103 событие
  `message_new` имеет **вложенную** структуру: `object = {message: {...}, client_info: {...}}`.
- **Токен сообщества:** «Управление → Работа с API → Ключи доступа → Создать ключ» (права на
  сообщения). Дополнительно для бота: включить **сообщения сообщества** и на вкладке **Long Poll API**
  включить Long Poll, выставить **версию 5.199** и отметить тип события **«Входящее сообщение»**
  (`message_new`) — невключённые события = классическое «бот молчит».
- **Кнопка «Начать»:** показывается, если включена и переписки ещё нет; отправляет сообщение,
  у которого `payload` = `{"command":"start"}` (в raw JSON — строка `"{\"command\":\"start\"}"`).

## Ключевые факты `vkbottle` 4.9.0 (выверены по исходникам + эмпирически, 2026-06-11)

Проверено двояко: по исходникам тега `v4.9.0` (+ `vkbottle-types` 5.199.99.21) и эмпирическим
прогоном настоящего SDK против локального aiohttp-мока (полный цикл прошёл).

- **Импорты:** `from vkbottle.bot import Bot, BotLabeler, Message` (все три реэкспортированы в
  `vkbottle/bot.py`, проверено по `__all__` тега v4.9.0); `API` — `from vkbottle import API`.
- **Хендлеры на labeler:** `Bot(token=None, api=None, ..., labeler=None, ...)` — принимает и `api`,
  и `labeler` (`framework/bot/bot.py`). Паттерн ячейки: `labeler = BotLabeler()` на уровне модуля,
  `@labeler.message(...)`-декораторы, `Bot(token, labeler=labeler)` в `main()`. Харнесс собирает
  `Bot(api=мок_api, labeler=labeler)` с теми же хендлерами.
- **Правило payload:** `@labeler.message(payload={"command": "start"})` → `PayloadRule`
  (`dispatch/rules/base.py:266`): `json.loads(message.payload)` и **точное равенство** словарей
  (суперсет не матчится; для «содержит» есть `payload_contains=`). Порядок регистрации важен
  (blocking=True): payload-хендлер раньше echo.
- **Message:** текст — `message.text: str` (обязательное поле; у attachment-only сообщений `""`,
  не None). Ответ — `await message.answer(text)`: уходит `messages.send` с `peer_ids=[peer_id]`
  (не `peer_id`!) и автозаполненным `random_id=0`.
- **Запуск/остановка:** sync — `bot.run()` (`run_forever()` — deprecated, FutureWarning);
  async — `await bot.run_polling()`. Остановка — `bot.polling.stop()` (ставит stop-event; цикл
  выходит после завершения текущего long-poll запроса). Ошибки поллинга логируются и ретраятся,
  процесс не валится.
- **Транспорт:** HTTP **POST** на `{API_URL}{method}`; **`access_token` и `v` — в query string**,
  параметры метода — form data (`application/x-www-form-urlencoded`). Заголовка Authorization нет.
- **Override URL:** `API_URL` — классовый атрибут `API` (дефолт `https://api.vk.ru/method/`).
  Для мока: `api = API("mock-token"); api.API_URL = f"http://127.0.0.1:{port}/method/"` —
  инстанс-атрибут перекрывает классовый; код делает конкатенацию `API_URL + method`, поэтому
  **обязателен хвост `/method/` со слэшем**.
- **`groups.getById`:** BotPolling резолвит group_id, читает `response["groups"][0]["id"]` →
  мок отвечает `{"response": {"groups": [{"id": 42}]}}` (голый массив = ошибка).
- **`groups.getLongPollServer`:** ответ `{"response": {"key": str, "server": str, "ts": str}}`;
  `server` используется **дословно как URL** → мок возвращает свой `http://127.0.0.1:{port}/longpoll`.
  Сам long-poll запрос — **POST** (не GET) с query `act=a_check&key&ts&wait=25&rps_delay=0`.
- **Форма апдейта** (`{"ts": "2", "updates": [{"type": "message_new", "object": {"client_info": {...},
  "message": {...}}, "group_id": 42}]}`). Обязательные поля `message` (pydantic): `id`, `date`,
  `peer_id`, `from_id`, `text`, `conversation_message_id`, `out`, **`version`** (int). **Ловушка:**
  обязателен **`"fwd_messages": []`** — при его отсутствии `MessageMin` падает с ValidationError,
  которую роутер молча глотает (хендлер просто не вызывается). `client_info`:
  `{"button_actions": ["text"], "keyboard": true, "inline_keyboard": true, "carousel": false, "lang_id": 0}`.
- **Ответ `messages.send`:** при `peer_ids` SDK ждёт **список**:
  `{"response": [{"peer_id": N, "message_id": 555, "conversation_message_id": 7}]}` (голый int —
  ValidationError).
- **Побочный эффект:** BotPolling пишет файл `./.vkbottle/bot-polling/{group_id}.json` в cwd →
  каталог `.vkbottle/` в `.gitignore`; харнесс подчищает его на teardown.
- **Ошибки API:** `{"error": {"error_code": N, "error_msg": "...", "request_params": []}}` →
  `VKAPIError[N]`.

## Ключевые факты `vk-io` 4.10.1 (выверены по исходникам + эмпирически, 2026-06-11)

Проверено по тегу `vk-io@4.10.1` и эмпирическим прогоном настоящего пакета против локального мока.

- **Конструктор:** `new VK({ token, ... })`, опции плоско. Дефолты: `apiVersion: '5.199'`,
  `apiBaseUrl: 'https://api.vk.ru/method'` (именно `.ru` с 4.10.0). `pollingGroupId` задаёт группу
  заранее (тогда `groups.getById` не вызывается).
- **Ловушка для мока:** дефолтный `agent` — `https.globalAgent`; с `apiBaseUrl: 'http://127.0.0.1:...'`
  запрос падает (`Protocol "http:" not supported`). Лекарство: **`agent: undefined`** в конструкторе
  (типобезопасно: конструктор принимает `Partial<VKOptions>`).
- **Хендлер:** `vk.updates.on('message_new', async (context) => ...)`, context — `MessageContext`.
- **MessageContext:** `context.text` — `undefined`, если текста нет (не `''`); к тексту применяется
  `unescapeHTML`. `context.isOutbox` — `Boolean(message.out)`. **`context.messagePayload`** —
  `JSON.parse` сырой строки `payload` (undefined, если payload нет). Ответ — `await context.send(text)`:
  уходит `messages.send` с `peer_ids` (контекст из группового поллинга) и случайным `random_id`.
- **Запуск/остановка:** `vk.updates.start()` (резолвит group_id через `groups.getById`, если
  `pollingGroupId` не задан) / `vk.updates.stop()` (цикл выходит после завершения текущего long-poll
  запроса — мок должен отвечать на long-poll быстро, чтобы процесс завершался; плюс
  `server.closeAllConnections()` на teardown).
- **Транспорт:** **POST** на `{apiBaseUrl}/{method}`; **`access_token` и `v` — в form-encoded теле**
  (не в query — в отличие от vkbottle). `undefined`-параметры фильтруются.
- **`groups.getById`:** читается `groups[0].id` → мок отвечает `{"response": {"groups": [{"id": 42}]}}`.
- **`groups.getLongPollServer`:** ответ `key`/`server`/`ts`; для групп `server` — **дословно полный URL**
  → мок возвращает `http://127.0.0.1:{port}/longpoll`. Long-poll запрос — **GET** с query
  `key, act=a_check, wait=25, mode=202, version=19, ts` (мок игнорирует лишние параметры).
  `failed:1` → взять `ts` из ответа; `failed:2/3` → перезапрос сервера.
- **Форма апдейта:** та же вложенная (`type`/`object`/`group_id`); **`client_info` обязателен** —
  без него `object` трактуется как голое сообщение и структура ломается. Жёстко обязательных полей
  меньше, чем у vkbottle, но для эхо-логики нужны: `peer_id`, `from_id`, `text`, `out`, `id`,
  `conversation_message_id`, `date` (+ `attachments: []`, `payload` — опциональны). `group_id`
  апдейта попадает в `context.$groupId` (из-за этого send идёт через `peer_ids`).
- **Ответ `messages.send`:** число или массив; естественный для `peer_ids` —
  `{"response": [{"peer_id": N, "message_id": 555, "conversation_message_id": 7}]}`.
  Не-массивный объект сломает `rawDestination[0]`.
- **Ошибки API:** `{"error": {"error_code": N, "error_msg": "...", "request_params": []}}` →
  reject с `APIError`. Исключение в хендлере не валит процесс (composer ловит и логирует).
- **Пакет:** dual ESM/CJS + типы в комплекте; Node ≥ 12.20 (ячейка держит `>=18.18.0`, как max).

## Структура файлов

```
vk/python/                          vk/typescript/
├── bot.py            ← labeler +   ├── src/
│   хендлеры + main()               │   ├── handlers.ts   ← registerHandlers(vk) + GREETING
├── verify_local.py   ← мок-харнесс │   └── index.ts      ← dotenv, guard, VK, start()
├── requirements.txt  ← vkbottle,   ├── verify-local.ts   ← мок-харнесс (запуск: tsx)
│   python-dotenv                   ├── package.json      ← vk-io, dotenv; tsx, typescript
├── .env.example      ← BOT_TOKEN=  ├── tsconfig.json     ← как в max/typescript
├── .gitignore        ← .venv/,     ├── .env.example      ← BOT_TOKEN=
│   __pycache__/, *.pyc, .env,      ├── .gitignore        ← node_modules/, dist/, .env
│   .vkbottle/                      └── README.md
└── README.md
```

## Компоненты: `vk/python`

### `bot.py`

Стиль как у `max/python` (logging, async-хендлеры), но хендлеры на **labeler** — чтобы
`verify_local.py` пересобрал бота с моковым API без дублирования логики:

```python
import logging
import os
import sys

from dotenv import load_dotenv
from vkbottle.bot import Bot, BotLabeler, Message

load_dotenv()

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger("echo-bot")

# Хендлеры регистрируются на labeler, а не на Bot, — verify_local.py собирает
# Bot(api=<мок>, labeler=labeler) с этими же хендлерами. Порядок важен:
# payload-приветствие раньше echo (blocking-правила, первый матч выигрывает).
labeler = BotLabeler()

GREETING = "Привет! Я эхо-бот. Напиши мне что-нибудь — отвечу тем же."


# Кнопка «Начать» шлёт сообщение с payload {"command": "start"} — матчимся по payload,
# а не по тексту (текст «Начать», набранный руками, — обычное сообщение, уйдёт в эхо).
@labeler.message(payload={"command": "start"})
async def on_start(message: Message) -> None:
    await message.answer(GREETING)


@labeler.message()
async def echo(message: Message) -> None:
    if not message.text:  # вложение без текста — молчим (text у таких "")
        return
    logger.info("← получено: %s  → отвечаю тем же", message.text)
    await message.answer(message.text)


def main() -> None:
    token = os.getenv("BOT_TOKEN")
    if not token:
        sys.exit(
            "BOT_TOKEN не задан. Скопируйте .env.example в .env и вставьте токен сообщества VK "
            "(см. README — «Управление → Работа с API → Ключи доступа»)."
        )
    bot = Bot(token, labeler=labeler)
    logger.info("🤖 VK echo-бот запущен (Bots Long Poll). Напишите сообществу в VK.")
    bot.run()


if __name__ == "__main__":
    main()
```

Поведение: payload `{"command":"start"}` → приветствие; непустой текст → эхо; текст `""`
(attachment-only) → молчание; нет токена → `sys.exit(...)`, в сеть не лезем.

### `verify_local.py` — мок-харнесс

Архитектура как в `max/python` (aiohttp-сервер + настоящий SDK), VK-эндпоинты:

- `POST /method/groups.getById` → `{"response": {"groups": [{"id": 42}]}}`;
- `POST /method/groups.getLongPollServer` → `{"response": {"key": "k", "server": "http://127.0.0.1:{port}/longpoll", "ts": "1"}}` — мок замыкает long poll на себя;
- `POST /longpoll` (`act=a_check`) → **один раз** батч из 3 апдейтов `message_new`
  (формы из «Ключевых фактов», включая `version` и `fwd_messages: []`):
  1. текст `«Привет, VK!»` (peer 2000000001) — ждём эхо;
  2. текст `«Начать»` + `"payload": "{\"command\": \"start\"}"` (peer 2000000002) — ждём
     приветствие, НЕ эхо;
  3. probe: `"text": ""` + вложение-заглушка не нужна, пустого текста достаточно (peer 2000000003) —
     ответа быть не должно;
  далее — пустые ответы с задержкой ~0.3 c (anti-busy-loop, и чтобы `stop()` выходил быстро);
- `POST /method/messages.send` → ловим `{peer_ids, message, random_id}` из form data и
  `access_token`, `v` из query; отвечаем `{"response": [{"peer_id": ..., "message_id": 555,
  "conversation_message_id": 7}]}`.

Сборка бота: `from bot import labeler` → `api = API("mock-token")`, `api.API_URL =
f"http://127.0.0.1:{port}/method/"` → `Bot(api=api, labeler=labeler)` →
`task = asyncio.create_task(bot.run_polling())`; ждём 2 POST'а (таймаут ~10 с) + пауза ~1 с на
нежелательный ответ probe; останов — `bot.polling.stop()` + отмена task; teardown подчищает
`./.vkbottle/`.

Проверки (зеркало max/python):
- ✅ эхо: на текст — тот же текст в тот же peer (`peer_ids=2000000001`, `message=«Привет, VK!»`);
- ✅ «Начать»: приветствие (НЕ эхо текста «Начать») — подтверждает payload-маршрутизацию;
- ✅ авторизация: на `messages.send` в query есть `access_token=mock-token` и `v=5.199`;
- 🔍 probe: POST'ов ровно 2 (на пустой текст ответа не было).

Exit `0`/`1`.

### `requirements.txt`

```
vkbottle>=4.9,<5
python-dotenv>=1.0,<2
```

### `.env.example`

```
# Токен сообщества VK (бот работает от имени сообщества).
# Получение: ваше сообщество → Управление → Работа с API → Ключи доступа → Создать ключ
# (права на сообщения). Там же: включить сообщения сообщества и Long Poll API
# (версия 5.199, событие «Входящее сообщение») — иначе бот молчит.
# Скопируйте этот файл в .env и вставьте токен.
BOT_TOKEN=
```

### `.gitignore`

`.venv/`, `__pycache__/`, `*.pyc`, `.env`, **`.vkbottle/`** (служебный каталог BotPolling).

### `README.md`

По образцу `max/python`, адаптировано под VK:
- Что это: минимальный echo-бот сообщества VK на Python, SDK `vkbottle` (де-факто стандарт,
  async + декораторы; первопартийного SDK у VK нет).
- Требования: Python ≥ 3.10, сообщество VK (токен бесплатный и мгновенный — в отличие от MAX).
- Получить токен: шаги из «Ключевых фактов платформы» (ключ доступа + сообщения + Long Poll API
  с версией 5.199 и событием «Входящее сообщение» — выделить как главные грабли).
- Настроить и запустить: venv → `pip install -r requirements.txt` → `cp .env.example .env` →
  `python bot.py`.
- «Как устроено»: labeler, `@labeler.message(...)`, payload-конвенция «Начать»
  (точное совпадение `{"command":"start"}`), `message.answer(...)`, `bot.run()`.
- Блок «Проверка без токена»: `python verify_local.py` — что мокается и что проверяется.
- Нюанс VK-API: домен `api.vk.ru` (с 30.09.2025), версия 5.199, токен query-параметром
  `access_token` (у TS-соседа — в form-теле; оба варианта валидны для VK API).
- Источники: vkbottle (GitHub/доки), dev.vk.com (Bots Long Poll, ключи доступа, кнопка «Начать»).

## Компоненты: `vk/typescript`

### `src/handlers.ts`

```typescript
import { VK, MessageContext } from 'vk-io';

export const GREETING = 'Привет! Я эхо-бот. Напиши мне что-нибудь — отвечу тем же.';

// Хендлеры вынесены из index.ts, чтобы verify-local.ts гонял ровно эту же логику
// против фейкового VK (улучшение против max/typescript, где код копировался).
export function registerHandlers(vk: VK): void {
  vk.updates.on('message_new', async (context: MessageContext) => {
    if (context.isOutbox) return;
    // Кнопка «Начать» шлёт payload {"command":"start"} — матчимся по payload, не по тексту.
    if (context.messagePayload?.command === 'start') {
      await context.send(GREETING);
      return;
    }
    if (!context.text) return; // вложение без текста (text === undefined) — молчим
    console.log(`← получено: ${context.text}  → отвечаю тем же`);
    await context.send(context.text);
  });
}
```

### `src/index.ts`

```typescript
import 'dotenv/config';
import { VK } from 'vk-io';
import { registerHandlers } from './handlers.js';

const token = process.env.BOT_TOKEN;
if (!token) {
  console.error(
    'BOT_TOKEN не задан. Скопируйте .env.example в .env и вставьте токен сообщества VK ' +
    '(см. README — «Управление → Работа с API → Ключи доступа»).',
  );
  process.exit(1);
}

const vk = new VK({ token });
registerHandlers(vk);

console.log('🤖 VK echo-бот запущен (Bots Long Poll). Напишите сообществу в VK.');
vk.updates.start().catch((error) => {
  console.error('Не удалось запустить long polling:', error);
  process.exit(1);
});
```

### `verify-local.ts` — мок-харнесс (запуск `npm run verify:local` → `tsx verify-local.ts`)

`node:http`-сервер (как в max/typescript), VK-эндпоинты — те же 4, что в Python-ячейке, с отличиями
vk-io: long-poll запрос — **GET**; `access_token`/`v` парсятся из **form-тела** `messages.send`;
ответ `messages.send` — массив. Сборка бота:

```typescript
const vk = new VK({
  token: 'test-token',
  apiBaseUrl: `http://127.0.0.1:${port}/method`,
  agent: undefined, // дефолтный https.globalAgent не умеет http:// (ловушка)
});
registerHandlers(vk);
await vk.updates.start();
```

`pollingGroupId` НЕ задаём — пусть харнесс покрывает и резолв через `groups.getById`, как у живого
бота. Фикстуры апдейтов — те же 3 сценария (эхо / «Начать» с payload / probe без текста:
`"text"` отсутствует → `context.text === undefined`); `client_info` обязателен в каждом апдейте.
Остановка: `vk.updates.stop()` + `server.closeAllConnections()`; мок отвечает на long-poll
быстро (~0.3–0.5 c), чтобы процесс завершался без зависания.

Проверки (те же 4): эхо в тот же peer; приветствие на payload (не эхо «Начать»); `access_token` и
`v=5.199` в form-теле `messages.send`; probe — отправок ровно 2. Exit `0`/`1`.

### `package.json` / `tsconfig.json`

Зеркало `max/typescript`: `type: module`, engines `node >=18.18.0`, скрипты
`dev`/`start` (tsx), `build`/`typecheck` (tsc), `verify:local` (`tsx verify-local.ts`).
Зависимости: `vk-io ^4.10.1`, `dotenv`; dev: `typescript`, `tsx`, `@types/node`.
tsconfig — копия max/typescript (`src/` → `dist/`, strict).

### `.env.example`, `.gitignore`, `README.md`

`.env.example` — тот же текст, что в Python-ячейке. `.gitignore`: `node_modules/`, `dist/`, `.env`.
README — зеркало Python-ячейки с TS-спецификой: vk-io, `updates.on('message_new')`,
`context.messagePayload`, запуск через `tsx`, проверка `npm run verify:local`; нюанс — токен в
form-теле запроса (у Python-соседа — в query; оба варианта валидны для VK API).

## Корневой `README.md`

В таблицу матрицы добавляется строка **VK**: `✅ [vk/typescript](vk/typescript)` и
`✅ [vk/python](vk/python)`. Матрица 6/6.

## Верификация (приёмка)

Оффлайн (обе ячейки, как в max/python):

1. `vk/python`: venv 3.12 (`/opt/homebrew/bin/python3.12`, системный 3.9.6 слишком стар) →
   `pip install -r requirements.txt` → import-smoke (`python -c "import bot"`) → guard без токена
   (`python bot.py` → exit 1, в сеть не лезет) → **`python verify_local.py` → PASS**.
2. `vk/typescript`: `npm install` → `npm run typecheck` → guard без токена (`npm start` без `.env` →
   exit 1) → **`npm run verify:local` → PASS**.

Живая приёмка (пользователь подтвердил на брейншторме; цель — его свежесозданное **тестовое**
сообщество, не прод):

3. Пользователь создаёт тестовое сообщество VK, включает сообщения + Long Poll API
   (версия 5.199, событие «Входящее сообщение»), создаёт ключ доступа → токен в `.env`
   (gitignored) каждой ячейки.
4. По очереди: `python bot.py` / `npm start` → в VK сначала нажать **«Начать»** (кнопка
   показывается только до первой переписки с сообществом — ждём приветствие), затем написать текст
   (ждём эхо). Для второй ячейки кнопки уже не будет — payload-ветку подтверждает мок-харнесс, живым
   остаётся эхо. Перед живым прогоном — подтвердить у пользователя готовность (правило: тесты против
   живых сервисов — только с явного «да»).

После приёмки: memory-файл `vk-botapi-facts.md` (домен/версия/payload-конвенция/ловушки моков
обоих SDK) + строка в `MEMORY.md`.

## Вне области (YAGNI)

Не включаем (как в остальных «тонких» стартерах): Docker, тест-фреймворк, Callback API
(webhook), клавиатуры/карусели (кроме упоминания кнопки «Начать»), FSM/состояния, middleware,
graceful shutdown, CI, эхо вложений. Могут появиться позже отдельными тирами.
