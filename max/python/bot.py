import asyncio
import logging
import os
import sys

from maxapi import Bot, Dispatcher, F
from maxapi.types import MessageCreated, CommandStart
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger("echo-bot")

# Все хендлеры регистрируются на диспетчере (аналог aiogram Dispatcher).
# Порядок регистрации важен: /start раньше echo, чтобы команду не «съело» эхо.
dp = Dispatcher()


@dp.message_created(CommandStart())
async def on_start(event: MessageCreated) -> None:
    await event.message.answer("Привет! Я эхо-бот. Напиши мне что-нибудь — отвечу тем же.")


# Эхо: отвечаем тем же текстом. Фильтр F.message.body.text — только сообщения с текстом
# (на вложения без текста не реагируем, чтобы не слать пустой ответ).
@dp.message_created(F.message.body.text)
async def echo(event: MessageCreated) -> None:
    text = event.message.body.text
    logger.info("← получено: %s  → отвечаю тем же", text)
    await event.message.answer(text)


async def main() -> None:
    token = os.getenv("BOT_TOKEN")
    if not token:
        sys.exit(
            "BOT_TOKEN не задан. Скопируйте .env.example в .env и вставьте токен бота MAX "
            "(см. README — токен выдаётся через business.max.ru)."
        )
    bot = Bot(token)
    logger.info("🤖 MAX echo-бот запущен (long polling). Напишите ему в MAX.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
