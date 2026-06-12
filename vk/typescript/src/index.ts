import 'dotenv/config';
import { VK } from 'vk-io';
import { registerHandlers } from './handlers.js';

const token = process.env.BOT_TOKEN;
if (!token) {
  console.error(
    'BOT_TOKEN не задан. Скопируйте .env.example в .env и вставьте токен сообщества VK ' +
    '(см. README — «Управление → Работа с API → Ключи доступа»).',
  );
  process.exit(1);
}

const vk = new VK({ token });
registerHandlers(vk);

console.log('🤖 VK echo-бот запущен (Bots Long Poll). Напишите сообществу в VK.');
vk.updates.start().catch((error) => {
  console.error('Не удалось запустить long polling:', error);
  process.exit(1);
});
