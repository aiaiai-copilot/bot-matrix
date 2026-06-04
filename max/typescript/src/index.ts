import 'dotenv/config';
import { Bot } from '@maxhub/max-bot-api';

// Токен бота MAX (см. .env.example — получается у @MasterBot: https://max.ru/masterbot).
const token = process.env.BOT_TOKEN;
if (!token) {
  console.error(
    'BOT_TOKEN не задан. Скопируйте .env.example в .env и вставьте токен от @MasterBot (https://max.ru/masterbot).',
  );
  process.exit(1);
}

const bot = new Bot(token);

// Эхо: отвечаем тем же текстом, что прислал пользователь.
// message_created — событие нового сообщения; текст лежит в ctx.message.body.text.
bot.on('message_created', (ctx) => {
  const text = ctx.message.body.text;
  if (!text) return;
  console.log(`← получено: ${text}  → отвечаю тем же`);
  return ctx.reply(text);
});

// Логируем ошибки, чтобы бот не падал молча.
bot.catch((err) => console.error('Ошибка бота:', err));

// Запускаем long polling (под капотом — GET /updates к https://platform-api.max.ru).
bot.start();
console.log('🤖 MAX echo-бот запущен (long polling). Напишите ему в MAX.');
