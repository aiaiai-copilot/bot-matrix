# Telegram × Python — echo-бот (стартер)

Минимальный запускаемый бот для **Telegram** на **Python**, использующий
[aiogram](https://docs.aiogram.dev) (v3) — современный async-фреймворк.
Бот отвечает тем же текстом, что ему прислали (echo).

## Требования

- **Python ≥ 3.10** (требование aiogram 3)
- Аккаунт в Telegram

## 1. Получить токен бота

Токен выдаёт **@BotFather**:

1. Откройте https://t.me/BotFather и нажмите **Start**.
2. Отправьте команду `/newbot`.
3. Задайте имя и username (оканчивается на `bot`).
4. BotFather пришлёт **токен** вида `123456:ABC-DEF...`.

> Токен — полный доступ к боту, не публикуйте его.

## 2. Настроить и запустить

```bash
cd telegram/python

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

Напишите боту в Telegram — он ответит тем же текстом.

## Как это устроено

```python
dp = Dispatcher()

@dp.message(F.text)
async def echo(message: Message) -> None:
    await message.answer(message.text)

await dp.start_polling(bot)
```

- `Dispatcher` маршрутизирует апдейты; хендлеры вешаются декораторами `@dp.message(...)` (≈ `bot.on(...)`).
- Фильтр `F.text` — только текстовые сообщения; `message.answer(...)` отправляет ответ в тот же чат (≈ `ctx.reply(...)`).
- `dp.start_polling(bot)` запускает long polling (Telegram `getUpdates`).
- Команда `/start` обрабатывается отдельным хендлером с приветствием.

> Хотите эхо любого типа (фото, стикеры)? Замените тело на
> `await message.send_copy(chat_id=message.chat.id)` и снимите фильтр `F.text`.

## Источники

- aiogram: <https://docs.aiogram.dev>
- Получение токена: <https://t.me/BotFather>
- Telegram Bot API: <https://core.telegram.org/bots/api>
