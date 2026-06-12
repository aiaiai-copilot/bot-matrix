import { VK, MessageContext } from 'vk-io';

export const GREETING = 'Привет! Я эхо-бот. Напиши мне что-нибудь — отвечу тем же.';

// Хендлеры вынесены из index.ts, чтобы verify-local.ts гонял ровно эту же логику
// против фейкового VK (улучшение против max/typescript, где код копировался).
export function registerHandlers(vk: VK): void {
  vk.updates.on('message_new', async (context: MessageContext) => {
    if (context.isOutbox) return;
    // Кнопка «Начать» шлёт payload {"command":"start"} — матчимся по payload, не по тексту.
    if (context.messagePayload?.command === 'start') {
      await context.send(GREETING);
      return;
    }
    if (!context.text) return; // вложение без текста (text === undefined) — молчим
    console.log(`← получено: ${context.text}  → отвечаю тем же`);
    await context.send(context.text);
  });
}
