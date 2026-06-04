// Локальная проверка echo-бота БЕЗ реального токена и БЕЗ обращения к проду MAX.
// Поднимаем фейковый MAX-сервер, направляем настоящий SDK на него (clientOptions.baseUrl),
// симулируем входящее message_created и ловим исходящий POST /messages (это и есть эхо).
// Обработчик ниже — дословная копия логики из src/index.ts.
import http from 'node:http';
import maxBotApi from '@maxhub/max-bot-api';

const { Bot } = maxBotApi;

const INCOMING_TEXT = 'Привет, MAX!';
const CHAT_ID = 777;
const MARKER = 100;

const NONTEXT_CHAT_ID = 888;
let updateDelivered = false;
const posts = [];
let resolveFirstPost;
const firstPost = new Promise((resolve) => { resolveFirstPost = resolve; });

const server = http.createServer((req, res) => {
  const url = new URL(req.url, 'http://localhost');
  const json = (obj) => { res.writeHead(200, { 'content-type': 'application/json' }); res.end(JSON.stringify(obj)); };

  // bot.start() сначала дёргает GET /me
  if (req.method === 'GET' && url.pathname === '/me') {
    return json({ user_id: 1, name: 'Echo Bot', username: 'my_echo_bot', is_bot: true });
  }

  // long polling: GET /updates
  if (req.method === 'GET' && url.pathname === '/updates') {
    if (!updateDelivered) {
      updateDelivered = true;
      console.log(`[mock] → отдаю 2 апдейта: текст "${INCOMING_TEXT}" (chat ${CHAT_ID}) и ПУСТОЙ текст (chat ${NONTEXT_CHAT_ID}, probe)`);
      const ts = 1700000000000;
      const msg = (chatId, text) => ({
        update_type: 'message_created',
        timestamp: ts,
        message: {
          sender: { user_id: 42, name: 'Tester', username: 'tester' },
          recipient: { chat_id: chatId, chat_type: 'dialog' },
          timestamp: ts,
          body: { mid: `mid-${chatId}`, seq: 1, text, attachments: [] },
        },
      });
      return json({
        marker: MARKER,
        updates: [
          msg(CHAT_ID, INCOMING_TEXT),
          msg(NONTEXT_CHAT_ID, ''), // probe: пустой текст → ответа быть не должно
        ],
      });
    }
    // последующие опросы — эмуляция long-poll: пусто с задержкой, чтобы не было busy-loop
    return setTimeout(() => json({ marker: MARKER, updates: [] }), 500);
  }

  // эхо-ответ бота: POST /messages?chat_id=...
  if (req.method === 'POST' && url.pathname === '/messages') {
    let raw = '';
    req.on('data', (c) => { raw += c; });
    req.on('end', () => {
      const chatId = url.searchParams.get('chat_id');
      const body = raw ? JSON.parse(raw) : {};
      console.log(`[mock] ← поймал POST /messages chat_id=${chatId} body=${JSON.stringify(body)} (Authorization: ${req.headers.authorization})`);
      json({ message: { recipient: { chat_id: Number(chatId) }, body: { mid: 'srv-1', seq: 2, text: body.text } } });
      posts.push({ chatId, body, auth: req.headers.authorization });
      if (posts.length === 1) resolveFirstPost();
    });
    return;
  }

  res.writeHead(404); res.end();
});

await new Promise((r) => server.listen(0, '127.0.0.1', r));
const { port } = server.address();
const baseUrl = `http://127.0.0.1:${port}`;
console.log(`[mock] фейковый MAX слушает ${baseUrl}\n`);

// --- НАСТОЯЩИЙ SDK + та же логика, что в src/index.ts ---
const bot = new Bot('test-token', { clientOptions: { baseUrl } });
bot.on('message_created', (ctx) => {
  const text = ctx.message.body.text;
  if (!text) return;
  console.log(`[bot] ← получено: ${text}  → отвечаю тем же`);
  return ctx.reply(text);
});
bot.catch((err) => console.error('[bot] ошибка:', err));
bot.start();

const timeout = new Promise((_, rej) => setTimeout(() => rej(new Error('таймаут: эхо не получено за 8с')), 8000));

try {
  await Promise.race([firstPost, timeout]);
  // даём время на возможный (нежелательный) ответ на пустое сообщение
  await new Promise((r) => setTimeout(r, 1500));

  const echo = posts[0];
  const textOk = echo?.body?.text === INCOMING_TEXT;
  const chatOk = Number(echo?.chatId) === CHAT_ID;
  const authOk = echo?.auth === 'test-token'; // сырой токен в заголовке Authorization, без Bearer
  const probeOk = posts.length === 1;         // на пустой текст ответа НЕ было

  console.log('\n=== РЕЗУЛЬТАТ ===');
  console.log(`✅ happy path — text:    ${JSON.stringify(echo?.body?.text)}  (ожидали ${JSON.stringify(INCOMING_TEXT)})  ${textOk ? '✅' : '❌'}`);
  console.log(`✅ happy path — chat_id: ${echo?.chatId}  (ожидали ${CHAT_ID})  ${chatOk ? '✅' : '❌'}`);
  console.log(`✅ авторизация — Authorization: ${echo?.auth}  (сырой токен, без Bearer)  ${authOk ? '✅' : '❌'}`);
  console.log(`🔍 probe — ответов всего: ${posts.length}  (ожидали 1; на пустой текст ответа быть не должно)  ${probeOk ? '✅' : '❌'}`);

  const ok = textOk && chatOk && authOk && probeOk;
  console.log(ok
    ? '\n✅ PASS: echo round-trip через настоящий SDK; пустой текст корректно проигнорирован.'
    : '\n❌ FAIL: см. отметки выше.');
  bot.stop();
  server.close();
  process.exit(ok ? 0 : 1);
} catch (err) {
  console.error(`\n❌ FAIL: ${err.message}`);
  bot.stop();
  server.close();
  process.exit(1);
}
