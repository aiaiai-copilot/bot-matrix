# MAX × Python — echo-бот (стартер)

Минимальный запускаемый бот для мессенджера **MAX** на **Python**, использующий официальный
SDK [`maxapi`](https://github.com/max-messenger/max-botapi-python) (aiogram-подобный API).
Бот отвечает тем же текстом, что ему прислали (echo).

## Требования

- **Python ≥ 3.10**
- Аккаунт в мессенджере MAX (для боевого запуска — токен бота, см. ниже)

## 1. Получить токен бота

Токен бота MAX выдаётся через бизнес-платформу [business.max.ru](https://business.max.ru):
регистрация → верификация по ИНН (ИП/юрлицо — резидент РФ) → создание бота → модерация →
токен в разделе «Чат-боты → Интеграция».

> ⚠️ **Токен недоступен физлицам и самозанятым** (только верифицированным ИП/юрлицам — резидентам РФ).
> Чтобы убедиться, что код работает, без токена — есть локальная проверка `python verify_local.py`
> (см. раздел ниже). Токен — прямой доступ к боту, не публикуйте его.

## 2. Настроить и запустить

```bash
cd max/python

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

Напишите боту в MAX — он ответит тем же текстом; на `/start` пришлёт приветствие.

## Как это устроено

```python
dp = Dispatcher()

@dp.message_created(CommandStart())
async def on_start(event: MessageCreated):
    await event.message.answer("Привет! ...")

@dp.message_created(F.message.body.text)
async def echo(event: MessageCreated):
    await event.message.answer(event.message.body.text)

await dp.start_polling(bot)
```

- `Dispatcher` маршрутизирует апдейты; хендлеры вешаются декораторами `@dp.message_created(...)`
  (≈ aiogram). `CommandStart()` отбирает `/start`, `F.message.body.text` — текстовые сообщения.
- `event.message.answer(...)` отправляет ответ в тот же чат; текст входящего — `event.message.body.text`.
- `dp.start_polling(bot)` запускает long polling (опрос `GET /updates`).

### Нюанс MAX-API (Python SDK)

`maxapi` (версии `0.9.x`) работает с хостом **`https://platform-api.max.ru`** и передаёт токен
**HTTP-заголовком** `Authorization: <token>` (сырой токен, без префикса `Bearer`) — так же, как
официальный TypeScript-SDK `@maxhub/max-bot-api` из соседней ячейки (тот же современный хост и тот
же способ авторизации).

> Хост можно переопределить через `bot.api_url = <url>` (или `bot.set_api_url(<url>)`) до первого
> запроса — на этом построена локальная проверка `verify_local.py` (SDK направляется на фейковый MAX).

## Проверка без токена (`python verify_local.py`)

Токен MAX недоступен физлицам/самозанятым, поэтому живой запуск не для всех возможен. Локальная
проверка [`verify_local.py`](verify_local.py) поднимает **фейковый MAX-сервер** на `localhost`,
направляет на него настоящий SDK (через `bot.api_url`), симулирует входящие апдейты и проверяет
исходящие ответы:

```bash
python verify_local.py
```

- ✅ на текст бот отвечает тем же текстом в тот же чат;
- ✅ на `/start` приходит приветствие (отдельным хендлером, не эхом);
- ✅ авторизация — токен HTTP-заголовком `Authorization`;
- 🔍 на сообщение без текста ответа нет.

> Проверка подтверждает корректность **кода и интеграции с SDK**; она не заменяет проверку против
> реального MAX (для неё нужен токен), но это максимально близкий воспроизводимый аналог. Хендлеры
> импортируются из `bot.py` — харнесс гоняет настоящие обработчики бота.

## Источники

- Официальный SDK: <https://github.com/max-messenger/max-botapi-python> (PyPI `maxapi`)
- Документация Bot API: <https://dev.max.ru/docs-api>
- Получение токена: <https://business.max.ru>
