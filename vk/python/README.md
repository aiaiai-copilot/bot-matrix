# VK × Python — echo-бот (стартер)

Минимальный запускаемый бот сообщества **VK** на **Python**, использующий
[`vkbottle`](https://github.com/vkbottle/vkbottle) — де-факто стандарт экосистемы
(async + декораторы; первопартийного SDK у VK нет). Бот отвечает тем же текстом,
что ему прислали (echo), а на кнопку «Начать» шлёт приветствие.

## Требования

- **Python ≥ 3.10**
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
cd vk/python

# виртуальное окружение
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# зависимости
pip install -r requirements.txt

# конфигурация
cp .env.example .env               # затем впишите BOT_TOKEN=... в .env

# запуск (Bots Long Poll)
python bot.py
```

Напишите сообществу в VK — бот ответит тем же текстом. Кнопка **«Начать»**
(показывается до первой переписки) пришлёт приветствие.

## Как это устроено

```python
labeler = BotLabeler()

@labeler.message(payload={"command": "start"})
async def on_start(message: Message):
    await message.answer("Привет! ...")

@labeler.message()
async def echo(message: Message):
    if not message.text:
        return
    await message.answer(message.text)

Bot(token, labeler=labeler).run()
```

- Хендлеры вешаются на `labeler` (а не на `Bot`) — это позволяет `verify_local.py`
  пересобрать бота с фейковым API и теми же обработчиками.
- В VK нет `/start`; конвенция платформы — кнопка **«Начать»**, которая шлёт сообщение
  с `payload = {"command":"start"}`. Приветствие матчится **по payload** (точное совпадение),
  не по тексту: если написать слово «Начать» руками (без payload) — это обычный текст, сработает эхо.
- `message.answer(...)` отвечает в тот же диалог; текст входящего — `message.text`
  (у сообщения без текста — пустая строка, на него не отвечаем).

### Нюанс VK-API (Python SDK)

`vkbottle` работает с доменом **`api.vk.ru`** (VK требует его с 30.09.2025), версией API **5.199**
и передаёт токен **query-параметром** `access_token`. У соседней TypeScript-ячейки (`vk-io`) токен
уходит в form-теле запроса — **оба варианта валидны** для VK API.

## Проверка без токена (`python verify_local.py`)

[`verify_local.py`](verify_local.py) поднимает **фейковый VK-сервер** на `localhost`,
направляет на него настоящий SDK (через `api.API_URL`), симулирует Bots Long Poll и
проверяет исходящие `messages.send`:

```bash
python verify_local.py
```

- ✅ на текст бот отвечает тем же текстом в тот же диалог;
- ✅ на «Начать» (payload `{"command":"start"}`) приходит приветствие — отдельным хендлером, не эхом;
- ✅ авторизация — `access_token` и `v=5.199` в query-параметрах `messages.send`;
- 🔍 на сообщение без текста ответа нет.

> Проверка подтверждает корректность **кода и интеграции с SDK** и не требует токена.
> Хендлеры импортируются из `bot.py` — харнесс гоняет настоящие обработчики бота.

## Источники

- SDK `vkbottle`: <https://github.com/vkbottle/vkbottle> (PyPI `vkbottle`)
- Документация VK Bot API: <https://dev.vk.com/ru/api/bots/getting-started>
- Bots Long Poll: <https://dev.vk.com/ru/api/bots-long-poll/getting-started>
