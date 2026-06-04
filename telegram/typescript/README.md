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
