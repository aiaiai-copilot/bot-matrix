# Telegram × TypeScript echo-бот — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Заполнить ячейку `telegram/typescript` минимальным запускаемым echo-ботом на grammY, следуя конвенциям ячейки `max/typescript`.

**Architecture:** Самостоятельный стартер в `telegram/typescript/`: один файл `src/index.ts` (echo на grammY long polling), конфиги (`package.json`, `tsconfig.json`, `.env.example`, `.gitignore`), README. Верификация — оффлайн через `npm run typecheck`/`build` + guard-запуск без токена; живая проверка через BotFather опциональна и только по явной команде пользователя. Тест-фреймворка нет (YAGNI, как в других ячейках).

**Tech Stack:** TypeScript 5.6 (strict, NodeNext, ESM), grammY 1.43, dotenv, tsx, Node ≥18.18.

**Спека:** `docs/superpowers/specs/2026-06-04-telegram-typescript-design.md`

---

## Замечание о верификации (нет тест-фреймворка)

Эта ячейка — «тонкий» стартер без юнит-тестов (так же, как `max/typescript` и `telegram/python`). Роль «теста» в каждой задаче играют: компиляция (`npm run typecheck`, `npm run build`) и guard-поведение (запуск без `BOT_TOKEN` → чистый выход с кодом 1, без обращения к сети). Живой round-trip через реальный Telegram Bot API — отдельная опциональная задача в конце, выполняется **только по явному «да» пользователя** (правило CLAUDE.md о тестах против внешних систем).

## Структура файлов

```
telegram/typescript/
├── src/index.ts        ← Task 2 — echo-бот на grammY
├── package.json        ← Task 1 — deps + scripts
├── tsconfig.json       ← Task 1 — strict/NodeNext/ES2022
├── .env.example        ← Task 1 — BOT_TOKEN + инструкция BotFather
├── .gitignore          ← Task 1 — node_modules/, dist/, .env, *.log
└── README.md           ← Task 3 — запуск, токен, «как устроено»
```
Плюс Task 4 — правка корневого `README.md` (матрица).

---

## Task 1: Скаффолдинг ячейки (конфиги + установка зависимостей)

**Files:**
- Create: `telegram/typescript/package.json`
- Create: `telegram/typescript/tsconfig.json`
- Create: `telegram/typescript/.gitignore`
- Create: `telegram/typescript/.env.example`

- [ ] **Step 1: Создать `telegram/typescript/package.json`**

```json
{
  "name": "telegram-typescript-echo-bot-starter",
  "version": "0.1.0",
  "description": "Минимальный echo-бот для Telegram на TypeScript (grammY)",
  "private": true,
  "type": "module",
  "engines": {
    "node": ">=18.18.0"
  },
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "start": "tsx src/index.ts",
    "build": "tsc",
    "typecheck": "tsc --noEmit"
  },
  "dependencies": {
    "grammy": "^1.43.0",
    "dotenv": "^16.4.5"
  },
  "devDependencies": {
    "@types/node": "^22.7.0",
    "tsx": "^4.19.0",
    "typescript": "^5.6.0"
  }
}
```

- [ ] **Step 2: Создать `telegram/typescript/tsconfig.json`** (копия конвенции `max/typescript`)

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "lib": ["ES2022"],
    "outDir": "dist",
    "rootDir": "src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "sourceMap": true,
    "declaration": false
  },
  "include": ["src/**/*.ts"],
  "exclude": ["node_modules", "dist"]
}
```

- [ ] **Step 3: Создать `telegram/typescript/.gitignore`**

```
node_modules/
dist/
.env
*.log
```

- [ ] **Step 4: Создать `telegram/typescript/.env.example`**

```
# Токен Telegram-бота.
# Получите его у @BotFather: https://t.me/BotFather → /newbot → задайте имя и username (на конце "bot").
# Скопируйте этот файл в .env и вставьте свой токен (вида 123456:ABC-DEF..., без кавычек).
BOT_TOKEN=
```

- [ ] **Step 5: Установить зависимости**

Run: `cd telegram/typescript && npm install`
Expected: установка без ошибок; появляются `node_modules/` и `package-lock.json`; в выводе нет `npm error`.

- [ ] **Step 6: Проверить, что grammY и tsc доступны**

Run: `cd telegram/typescript && npm ls grammy && npx tsc --version`
Expected: строка `grammy@1.43.x` и `Version 5.6.x` (или новее в пределах каретки).

- [ ] **Step 7: Commit**

```bash
git add telegram/typescript/package.json telegram/typescript/tsconfig.json telegram/typescript/.gitignore telegram/typescript/.env.example telegram/typescript/package-lock.json
git commit -m "chore(telegram/typescript): скаффолдинг ячейки (grammY, конфиги)"
```
Примечание: `node_modules/` в коммит не попадёт — он покрыт `telegram/typescript/.gitignore` (Step 3).

---

## Task 2: Реализовать echo-бота (`src/index.ts`)

**Files:**
- Create: `telegram/typescript/src/index.ts`

- [ ] **Step 1: Создать `telegram/typescript/src/index.ts`**

```ts
import 'dotenv/config';
import { Bot } from 'grammy';

// Токен бота Telegram (см. .env.example — получается у @BotFather: https://t.me/BotFather).
const token = process.env.BOT_TOKEN;
if (!token) {
  console.error(
    'BOT_TOKEN не задан. Скопируйте .env.example в .env и вставьте токен от @BotFather (https://t.me/BotFather).',
  );
  process.exit(1);
}

const bot = new Bot(token);

// /start — приветствие (аналог on_start в telegram/python). Команда не передаёт
// управление дальше, поэтому до echo-хендлера не доходит — приветствие не дублируется.
bot.command('start', (ctx) =>
  ctx.reply('Привет! Я эхо-бот. Напиши мне что-нибудь — отвечу тем же.'),
);

// Эхо: на текст отвечаем тем же текстом. Фильтр 'message:text' пропускает только
// текстовые сообщения (стикеры/фото и т.п. игнорируем, чтобы не слать пустой ответ).
bot.on('message:text', (ctx) => {
  console.log(`← получено: ${ctx.message.text}  → отвечаю тем же`);
  return ctx.reply(ctx.message.text);
});

// Логируем ошибки, чтобы бот не падал молча.
bot.catch((err) => console.error('Ошибка бота:', err));

// Запускаем long polling (под капотом — getUpdates к https://api.telegram.org).
// bot.start() у grammY асинхронный, поэтому строку о старте логируем в onStart —
// после реальной инициализации (getMe).
bot.start({
  onStart: (me) =>
    console.log(`🤖 Telegram echo-бот @${me.username} запущен (long polling). Напишите ему в Telegram.`),
});
```

- [ ] **Step 2: Проверка типов**

Run: `cd telegram/typescript && npm run typecheck`
Expected: завершается без ошибок (нет вывода `error TSxxxx`), exit code 0.

- [ ] **Step 3: Сборка**

Run: `cd telegram/typescript && npm run build`
Expected: без ошибок; появляется `dist/index.js`. (`dist/` уже в `.gitignore`.)

- [ ] **Step 4: Guard-проверка — запуск без токена (без сети)**

Убедитесь, что файла `telegram/typescript/.env` НЕ существует (иначе guard не сработает и бот пойдёт в сеть).
Run: `cd telegram/typescript && test ! -f .env && npm start; echo "exit=$?"`
Expected: печатает `BOT_TOKEN не задан. Скопируйте .env.example в .env ...` и `exit=1`. Сетевых обращений к Telegram нет (до `new Bot` дело не доходит).

- [ ] **Step 5: Commit**

```bash
git add telegram/typescript/src/index.ts
git commit -m "feat(telegram/typescript): echo-бот на grammY (long polling, /start + message:text)"
```

---

## Task 3: README ячейки

**Files:**
- Create: `telegram/typescript/README.md`

- [ ] **Step 1: Создать `telegram/typescript/README.md`**

````markdown
# Telegram × TypeScript — echo-бот (стартер)

Минимальный запускаемый бот для **Telegram** на **TypeScript**, использующий фреймворк
[grammY](https://grammy.dev). Бот отвечает тем же текстом, что ему прислали (echo).

## Требования

- **Node.js ≥ 18.18.0**
- Аккаунт в Telegram

## 1. Получить токен бота

Токен выдаёт сервисный бот **@BotFather**:

1. Откройте [@BotFather](https://t.me/BotFather) и нажмите **Start**.
2. Отправьте команду `/newbot`.
3. Задайте отображаемое имя и username (латиница, оканчивается на `bot`).
4. BotFather пришлёт **токен** вида `123456:ABC-DEF...` прямо в чат.

> Токен — прямой доступ к боту, не публикуйте его. Файл `.env` уже в `.gitignore`.

## 2. Настроить и запустить

```bash
cd telegram/typescript

# зависимости
npm install

# конфигурация: скопируйте пример и вставьте токен
cp .env.example .env
# затем впишите BOT_TOKEN=... в .env

# запуск (long polling)
npm run dev      # с авто-перезапуском при изменениях
# или
npm start
```

Напишите боту в Telegram (`/start`, затем любой текст) — он ответит тем же текстом.

## Скрипты

| Команда             | Что делает                               |
| ------------------- | ---------------------------------------- |
| `npm run dev`       | Запуск с авто-перезапуском (`tsx watch`) |
| `npm start`         | Запуск бота                              |
| `npm run build`     | Компиляция TypeScript → `dist/`          |
| `npm run typecheck` | Проверка типов без сборки                |

## Как это устроено

```ts
const bot = new Bot(token);
bot.command('start', (ctx) => ctx.reply('Привет! ...'));
bot.on('message:text', (ctx) => ctx.reply(ctx.message.text));
bot.start();
```

- `bot.start()` запускает **long polling** — grammY периодически опрашивает `getUpdates`
  на `https://api.telegram.org`, авторизуясь токеном из `.env`.
- `bot.command('start', ...)` — реакция на `/start` (приветствие).
- `bot.on('message:text', ...)` — новое текстовое сообщение; текст в `ctx.message.text`;
  `ctx.reply(text)` отправляет ответ (под капотом `sendMessage`).

### Long polling vs Webhook

Этот стартер использует **long polling** — проще всего для разработки. Для production
Telegram поддерживает **webhook** (`setWebhook`). Long polling и webhook
взаимоисключающи: при активном webhook метод `getUpdates` возвращает конфликт.

## Источники

- grammY: <https://grammy.dev> (npm `grammy`)
- Telegram Bot API: <https://core.telegram.org/bots/api>
- Получение токена: [@BotFather](https://t.me/BotFather)
````

- [ ] **Step 2: Commit**

```bash
git add telegram/typescript/README.md
git commit -m "docs(telegram/typescript): README со стартом и обзором grammY"
```

---

## Task 4: Обновить корневой `README.md` (матрица)

**Files:**
- Modify: `README.md` (строка матрицы Telegram)

- [ ] **Step 1: Заменить ячейку Telegram × TypeScript в таблице**

В файле `README.md` найдите строку:

```
| **Telegram**          | —          | ✅ [`telegram/python`](telegram/python) |
```

Замените на:

```
| **Telegram**          | ✅ [`telegram/typescript`](telegram/typescript) | ✅ [`telegram/python`](telegram/python) |
```

- [ ] **Step 2: Проверить таблицу**

Run: `grep -n "telegram/typescript" README.md`
Expected: одна строка с ячейкой Telegram × TypeScript.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: матрица — Telegram × TypeScript готов"
```

---

## Task 5 (опционально): Живая проверка через BotFather

> Выполнять **только по явному «да» пользователя** — это обращение к реальному Telegram Bot API (CLAUDE.md). Пропустить, если живая проверка не нужна.

**Files:** none (использует `telegram/typescript/.env`, который gitignored)

- [ ] **Step 1: Завести токен**

Создать тест-бота через @BotFather (`/newbot`) **или** переиспользовать существующий `@bm_ts_demo_bot` (токен в `telegram/python/.env`). Вписать токен в `telegram/typescript/.env` (`cp .env.example .env`, затем значение). Файл gitignored.

- [ ] **Step 2: Проверить, что у бота пустой webhook (нет конфликта с long polling)**

Перед запуском убедиться, что webhook не активен (иначе `getUpdates` даст конфликт). Для нового бота он пуст по умолчанию. Если бот переиспользуется и имел webhook — **не запускать**, см. инцидент в HANDOFF (бот с активным webhook на живой сервис трогать нельзя).

- [ ] **Step 3: Запустить и проверить round-trip**

Run: `cd telegram/typescript && npm run dev`
Expected: лог `🤖 Telegram echo-бот @<username> запущен (long polling)`.
Затем в Telegram: `/start` → приветствие; любой текст → тот же текст обратно; в консоли — `← получено: ...`. `Ctrl-C` — стоп.

- [ ] **Step 4: Остановить бота** (`Ctrl-C`); при необходимости почистить `telegram/typescript/.env`.

---

## Self-Review (выполнено при написании плана)

- **Покрытие спеки:** src/index.ts (Task 2), package.json/tsconfig/.env.example/.gitignore (Task 1), README ячейки (Task 3), правка корневого README (Task 4), верификация оффлайн+live (Tasks 2,5) — все разделы спеки покрыты.
- **Плейсхолдеры:** нет TBD/TODO; весь код и команды приведены целиком.
- **Согласованность типов/имён:** имена `BOT_TOKEN`, `bot`, `me.username`, события `message:text`/команда `start` совпадают между задачами и со спекой; версии (grammy ^1.43.0, typescript ^5.6.0, tsx ^4.19.0) согласованы.
