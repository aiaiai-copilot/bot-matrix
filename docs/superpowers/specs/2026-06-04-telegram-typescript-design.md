# Дизайн: ячейка `telegram/typescript` — echo-бот на grammY

**Дата:** 2026-06-04
**Статус:** одобрен пользователем, готов к плану реализации

## Контекст

`bot-matrix` — учебная коллекция стартеров ботов, матрица «мессенджер × технология»
(раскладка `<мессенджер>/<технология>/`). На момент написания готовы 2 из 4 ячеек:
`max/typescript` (echo на `@maxhub/max-bot-api`) и `telegram/python` (echo на aiogram 3,
проверен вживую через BotFather). Задача — заполнить ячейку **Telegram × TypeScript**:
минимальный запускаемый echo-бот, следующий конвенциям уже готовых ячеек.

Зачем: завершить ещё одну ячейку матрицы; дать ученику воспроизводимый, стилистически
согласованный с остальными ячейками пример Telegram-бота на TypeScript.

## Решения (приняты при брейншторме)

- **Фреймворк — grammY.** Современный TypeScript-first фреймворк; его ctx-API почти 1:1
  совпадает с `@maxhub/max-bot-api` из ячейки MAX (`bot.on(...)`, `ctx.reply`, `bot.catch`,
  `bot.start()`) — максимальная стилевая согласованность с остальной матрицей. Альтернативы
  (Telegraf — больше легаси/слабее TS; голый Bot API на fetch — много бойлерплейта) отклонены.
- **Верификация — live (BotFather) + `typecheck`/`build`, без мок-харнесса.** В отличие от
  `max/typescript` (там `verify:local` нужен, т.к. токен MAX недоступен физлицам), токен
  Telegram бесплатен. Оффлайн-уверенность даёт компилятор TS; живую проверку делаем через
  BotFather, как уже сделали для `telegram/python`. Мок — YAGNI.

## Структура файлов

Зеркалит `max/typescript`:

```
telegram/typescript/
├── src/index.ts        ← echo-бот на grammY
├── package.json        ← deps: grammy, dotenv; scripts: dev/start/build/typecheck
├── tsconfig.json       ← strict, NodeNext, ES2022 (та же конвенция, что max/typescript)
├── .env.example        ← BOT_TOKEN= + инструкция про @BotFather
├── .gitignore          ← node_modules/, dist/, .env, *.log
└── README.md           ← запуск, токен через BotFather, «как устроено»
```

## Компоненты

### `src/index.ts` — бот

Минимальный echo, паттерн как у MAX-ячейки и `telegram/python`:

```ts
import 'dotenv/config';
import { Bot } from 'grammy';

const token = process.env.BOT_TOKEN;
if (!token) {
  console.error('BOT_TOKEN не задан. Скопируйте .env.example в .env и вставьте токен от @BotFather (https://t.me/BotFather).');
  process.exit(1);
}

const bot = new Bot(token);

// /start — приветствие (аналог on_start в telegram/python)
bot.command('start', (ctx) => ctx.reply('Привет! Я эхо-бот. Напиши мне что-нибудь — отвечу тем же.'));

// Эхо: на текст отвечаем тем же текстом (нетекстовые апдейты игнорируем фильтром 'message:text')
bot.on('message:text', (ctx) => {
  console.log(`← получено: ${ctx.message.text}  → отвечаю тем же`);
  return ctx.reply(ctx.message.text);
});

bot.catch((err) => console.error('Ошибка бота:', err));

// long polling; onStart логируем после реального старта (bot.start() у grammY — async)
bot.start({ onStart: (me) => console.log(`🤖 Telegram echo-бот @${me.username} запущен (long polling).`) });
```

Поведение:
- `/start` → приветствие. `bot.command('start', ...)` не вызывает `next()`, поэтому до
  echo-хендлера не доходит — приветствие не дублируется эхом (как `CommandStart` vs `F.text`
  в `telegram/python`).
- Любой текст → тот же текст обратно, с логом `← получено: ...` (тот же формат лога, что в
  остальных ячейках).
- Нетекстовые сообщения (стикеры/фото и т.п.) фильтр `message:text` отсекает — пустой ответ
  не шлём.
- `bot.catch` — бот не падает молча на ошибке.

### `package.json`

- `name: "telegram-typescript-echo-bot-starter"`, `version: "0.1.0"`, `private: true`, `type: "module"`
- `engines.node: ">=18.18.0"` (Node 18+ для grammY и встроенного fetch)
- dependencies: `grammy` (^1.x — последняя стабильная), `dotenv` (^16)
- devDependencies: `@types/node`, `tsx`, `typescript`
- scripts: `dev` (`tsx watch src/index.ts`), `start` (`tsx src/index.ts`),
  `build` (`tsc`), `typecheck` (`tsc --noEmit`)
- **`verify:local` НЕ добавляем** (см. решение о верификации).

### `tsconfig.json`

Копия конвенции `max/typescript`: `target ES2022`, `module/moduleResolution NodeNext`,
`strict`, `esModuleInterop`, `skipLibCheck`, `outDir dist`, `rootDir src`,
`include ["src/**/*.ts"]`.

### `.env.example`

```
# Токен Telegram-бота.
# Получите его у @BotFather: https://t.me/BotFather → /newbot → задайте имя и username (на конце "bot").
# Скопируйте этот файл в .env и вставьте свой токен (вида 123456:ABC-DEF..., без кавычек).
BOT_TOKEN=
```

### `.gitignore`

`node_modules/`, `dist/`, `.env`, `*.log`.

### `README.md`

По образцу `max/typescript`, адаптировано под Telegram/BotFather:
- Требования: Node.js ≥ 18.18, аккаунт Telegram.
- Получить токен: @BotFather → `/newbot` → имя + username → токен.
- Настроить и запустить: `npm install` → `cp .env.example .env` (вписать токен) → `npm run dev` / `npm start`.
- Таблица скриптов (`dev`/`start`/`build`/`typecheck`).
- «Как устроено»: grammY long polling (`getUpdates`), `message:text`, `ctx.reply`.
- Короткая заметка «long polling vs webhook».
- Источники: grammY (<https://grammy.dev>), Telegram Bot API (<https://core.telegram.org/bots/api>), BotFather.
- Раздела про мок-проверку нет.

### Корневой `README.md`

В таблице матрицы ячейка `Telegram × TypeScript` меняется с `—` на
`✅ [`telegram/typescript`](telegram/typescript)`.

## Верификация (приёмка)

1. **Оффлайн (обязательно):** `cd telegram/typescript` → `npm install` →
   `npm run typecheck` (без ошибок) → `npm run build` (компиляция в `dist/` без ошибок).
2. **Live (опционально, только по явной команде пользователя):** запуск `npm run dev` с
   реальным токеном (тест-бот `@bm_ts_demo_bot` уже существует, либо новый через BotFather),
   проверка round-trip `/start` → приветствие, текст → эхо. Это обращение к реальному
   Telegram Bot API — запускать строго по явному «да» (правило из CLAUDE.md).

## Вне области (YAGNI)

Не включаем (как и в других «тонких» стартерах): Docker, тест-фреймворк, middleware,
сессии/FSM, webhook-сервер, graceful shutdown, CI. Могут появиться позже отдельными тирами.
