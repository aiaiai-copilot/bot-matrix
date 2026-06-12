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
