import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger("echo-bot")

# Все хендлеры регистрируются на диспетчере (аналог Composer/роутера).
dp = Dispatcher()


@dp.message(CommandStart())
async def on_start(message: Message) -> None:
    await message.answer("Привет! Я эхо-бот. Напиши мне что-нибудь — отвечу тем же.")


# Эхо: отвечаем тем же текстом. Фильтр F.text — только текстовые сообщения
# (на стикеры/фото и т.п. не реагируем, чтобы не слать пустой текст).
@dp.message(F.text)
async def echo(message: Message) -> None:
    logger.info("← получено: %s  → отвечаю тем же", message.text)
    await message.answer(message.text)


async def main() -> None:
    token = os.getenv("BOT_TOKEN")
    if not token:
        sys.exit(
            "BOT_TOKEN не задан. Скопируйте .env.example в .env и вставьте токен "
            "от @BotFather (https://t.me/BotFather)."
        )
    bot = Bot(token=token)
    logger.info("🤖 Telegram echo-бот запущен (long polling). Напишите ему в Telegram.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
