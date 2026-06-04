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
