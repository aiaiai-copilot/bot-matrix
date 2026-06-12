# VK × TypeScript — echo-бот (стартер)

Минимальный запускаемый бот сообщества **VK** на **TypeScript**, использующий
[`vk-io`](https://github.com/negezor/vk-io) — де-факто стандарт экосистемы (первопартийного
SDK у VK нет). Бот отвечает тем же текстом, что ему прислали (echo), а на кнопку «Начать»
шлёт приветствие.

## Требования

- **Node.js ≥ 18.18**
- Сообщество VK (токен бесплатный и выдаётся мгновенно — в отличие от MAX)

## 1. Получить токен сообщества

В вашем сообществе VK: **Управление → Работа с API → Ключи доступа → Создать ключ**
(дать права на сообщения). Затем там же:

- включить **сообщения сообщества**;
- на вкладке **Long Poll API** включить Long Poll, выставить **версию 5.199** и
  отметить тип события **«Входящее сообщение»** (`message_new`).

> ⚠️ Невключённые события — самые частые грабли: «бот молчит», хотя токен верный.
> Токен — прямой доступ к сообществу, не публикуйте его.

## 2. Настроить и запустить

```bash
cd vk/typescript

# зависимости
npm install

# конфигурация
cp .env.example .env               # затем впишите BOT_TOKEN=... в .env

# запуск (Bots Long Poll, через tsx — без сборки)
npm start
```

Напишите сообществу в VK — бот ответит тем же текстом. Кнопка **«Начать»**
(показывается до первой переписки) пришлёт приветствие.

## Как это устроено

```typescript
// src/handlers.ts — логика вынесена отдельно, чтобы её же гонял verify-local.ts
export function registerHandlers(vk: VK): void {
  vk.updates.on('message_new', async (context) => {
    if (context.isOutbox) return;
    if (context.messagePayload?.command === 'start') {
      await context.send(GREETING);
      return;
    }
    if (!context.text) return;
    await context.send(context.text);
  });
}

// src/index.ts
const vk = new VK({ token });
registerHandlers(vk);
vk.updates.start();
```

- Хендлеры вынесены в `src/handlers.ts` (`registerHandlers(vk)`) — это позволяет
  `verify-local.ts` прогнать ровно ту же логику против фейкового VK.
- В VK нет `/start`; конвенция платформы — кнопка **«Начать»**, которая шлёт сообщение
  с `payload = {"command":"start"}`. Приветствие матчится **по `context.messagePayload`**,
  не по тексту: слово «Начать», набранное руками (без payload), — обычный текст, сработает эхо.
- `context.send(...)` отвечает в тот же диалог; текст входящего — `context.text`
  (`undefined`, если текста нет — тогда не отвечаем).

### Нюанс VK-API (TypeScript SDK)

`vk-io` работает с доменом **`api.vk.ru`** (VK требует его с 30.09.2025), версией API **5.199**
и передаёт токен в **form-теле** запроса. У соседней Python-ячейки (`vkbottle`) токен уходит
query-параметром `access_token` — **оба варианта валидны** для VK API.

## Проверка без токена (`npm run verify:local`)

[`verify-local.ts`](verify-local.ts) поднимает **фейковый VK-сервер** на `localhost`,
направляет на него настоящий SDK (через `apiBaseUrl`), симулирует Bots Long Poll и
проверяет исходящие `messages.send`:

```bash
npm run verify:local
```

- ✅ на текст бот отвечает тем же текстом в тот же диалог;
- ✅ на «Начать» (payload `{"command":"start"}`) приходит приветствие — отдельной веткой, не эхом;
- ✅ авторизация — `access_token` и `v=5.199` в form-теле `messages.send`;
- 🔍 на сообщение без текста ответа нет.

> Проверка подтверждает корректность **кода и интеграции с SDK** и не требует токена.
> Хендлеры импортируются из `src/handlers.ts` — харнесс гоняет настоящую логику бота.

## Источники

- SDK `vk-io`: <https://github.com/negezor/vk-io> (npm `vk-io`)
- Документация VK Bot API: <https://dev.vk.com/ru/api/bots/getting-started>
- Bots Long Poll: <https://dev.vk.com/ru/api/bots-long-poll/getting-started>
