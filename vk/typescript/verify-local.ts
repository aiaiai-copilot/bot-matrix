// Локальная проверка VK echo-бота БЕЗ реального токена и БЕЗ обращения к проду VK.
// Поднимаем фейковый VK-сервер (node:http), направляем НАСТОЯЩИЙ vk-io на него (apiBaseUrl),
// симулируем Bots Long Poll и ловим исходящие messages.send (это и есть ответы бота).
// Хендлеры берём из src/handlers.ts (registerHandlers) — гоняем реальную логику бота.
import { createServer, type IncomingMessage } from 'node:http';
import type { AddressInfo } from 'node:net';
import { VK } from 'vk-io';
import { registerHandlers, GREETING } from './src/handlers.js';

const GROUP_ID = 42;
const ECHO_PEER = 2000000001;
const START_PEER = 2000000002;
const PROBE_PEER = 2000000003;
const ECHO_TEXT = 'Привет, VK!';
const TS = 1700000000;

// client_info обязателен — без него object трактуется как голое сообщение и структура ломается.
const CLIENT_INFO = {
  button_actions: ['text'],
  keyboard: true,
  inline_keyboard: true,
  carousel: false,
  lang_id: 0,
};

interface Sent {
  peerIds: string | null;
  text: string | null;
  accessToken: string | null;
  v: string | null;
}
const sent: Sent[] = [];
let batchDelivered = false;
let port = 0;

const sleep = (ms: number) => new Promise<void>((r) => setTimeout(r, ms));

function message(id: number, peerId: number, fromId: number, text: string | undefined, payload?: string) {
  // Для эхо-логики vk-io нужны: id, date, peer_id, from_id, out, conversation_message_id, attachments.
  // text/payload опциональны — их отсутствие = undefined в контексте (так моделируем probe без текста).
  const msg: Record<string, unknown> = {
    id,
    date: TS,
    peer_id: peerId,
    from_id: fromId,
    out: 0,
    conversation_message_id: id,
    attachments: [],
  };
  if (text !== undefined) msg.text = text;
  if (payload !== undefined) msg.payload = payload;
  return msg;
}

function update(id: number, peerId: number, fromId: number, text: string | undefined, payload?: string) {
  return {
    type: 'message_new',
    object: { client_info: CLIENT_INFO, message: message(id, peerId, fromId, text, payload) },
    group_id: GROUP_ID,
  };
}

function readBody(req: IncomingMessage): Promise<string> {
  return new Promise((resolve) => {
    let data = '';
    req.on('data', (c) => (data += c));
    req.on('end', () => resolve(data));
  });
}

const server = createServer(async (req, res) => {
  const url = new URL(req.url ?? '', 'http://127.0.0.1');
  const json = (obj: unknown) => {
    res.writeHead(200, { 'content-type': 'application/json' });
    res.end(JSON.stringify(obj));
  };

  // groups.getById — vk-io резолвит group_id (читает groups[0].id)
  if (url.pathname === '/method/groups.getById') {
    return json({ response: { groups: [{ id: GROUP_ID }] } });
  }
  // getLongPollServer — server используется ДОСЛОВНО как URL → замыкаем long poll на себя
  if (url.pathname === '/method/groups.getLongPollServer') {
    return json({ response: { key: 'k', server: `http://127.0.0.1:${port}/longpoll`, ts: '1' } });
  }
  // long-poll — у vk-io это GET с query (act=a_check, ...); мок игнорирует параметры
  if (url.pathname === '/longpoll') {
    if (!batchDelivered) {
      batchDelivered = true;
      console.log('[mock] → отдаю 3 апдейта: текст, «Начать»+payload, probe(без text)');
      return json({
        ts: '2',
        updates: [
          update(1, ECHO_PEER, 101, ECHO_TEXT),
          update(2, START_PEER, 102, 'Начать', '{"command":"start"}'),
          update(3, PROBE_PEER, 103, undefined), // нет text → context.text === undefined → молчим
        ],
      });
    }
    await sleep(300); // эмуляция long-poll: пусто с задержкой (быстрый stop без зависания)
    return json({ ts: '2', updates: [] });
  }
  // messages.send — у vk-io access_token и v в form-ТЕЛЕ (не в query, в отличие от Python-соседа)
  if (url.pathname === '/method/messages.send') {
    const params = new URLSearchParams(await readBody(req));
    sent.push({
      peerIds: params.get('peer_ids'),
      text: params.get('message'),
      accessToken: params.get('access_token'),
      v: params.get('v'),
    });
    console.log(`[mock] ← messages.send peer_ids=${params.get('peer_ids')} text=${JSON.stringify(params.get('message'))}`);
    return json({
      response: [{ peer_id: Number(params.get('peer_ids')), message_id: 555, conversation_message_id: 7 }],
    });
  }
  json({ response: 1 }); // прочие методы — безобидный дефолт
});

await new Promise<void>((resolve) => server.listen(0, '127.0.0.1', resolve));
port = (server.address() as AddressInfo).port;
console.log(`[mock] фейковый VK слушает http://127.0.0.1:${port}\n`);

// НАСТОЯЩИЙ vk-io, направленный на мок. agent: undefined — иначе https.globalAgent
// не умеет http:// (ловушка). pollingGroupId НЕ задаём — пусть резолвится через groups.getById.
const vk = new VK({
  token: 'test-token',
  apiBaseUrl: `http://127.0.0.1:${port}/method`,
  agent: undefined,
});
registerHandlers(vk);
await vk.updates.start();

for (let i = 0; i < 100 && sent.length < 2; i++) await sleep(100); // ждём 2 send ~10 с
await sleep(800); // шанс на возможный (нежелательный) ответ на probe

await vk.updates.stop();
server.closeAllConnections();
await new Promise<void>((resolve) => server.close(() => resolve()));

// --- проверки (зеркало vk/python) ---
const echo = sent.find((s) => s.peerIds === String(ECHO_PEER));
const start = sent.find((s) => s.peerIds === String(START_PEER));

const textOk = echo?.text === ECHO_TEXT;
const startOk = start?.text === GREETING;
const authOk = sent.length > 0 && sent.every((s) => s.accessToken === 'test-token' && s.v === '5.199');
const probeOk = sent.length === 2 && !sent.some((s) => s.peerIds === String(PROBE_PEER));

console.log('\n=== РЕЗУЛЬТАТ ===');
console.log(`✅ эхо текста:        ${JSON.stringify(echo?.text)}  (ожидали ${JSON.stringify(ECHO_TEXT)})  ${textOk ? '✅' : '❌'}`);
console.log(`✅ «Начать» payload:  ${JSON.stringify(start?.text)}  (приветствие, НЕ эхо «Начать»)  ${startOk ? '✅' : '❌'}`);
console.log(`✅ авторизация:       access_token + v=5.199 в form-теле  ${authOk ? '✅' : '❌'}`);
console.log(`🔍 probe:             messages.send всего ${sent.length}  (ожидали 2; без text ответа нет)  ${probeOk ? '✅' : '❌'}`);

const ok = textOk && startOk && authOk && probeOk;
console.log(ok
  ? '\n✅ PASS: echo round-trip через настоящий SDK; payload-приветствие отдельной веткой; сообщение без текста проигнорировано.'
  : '\n❌ FAIL: см. отметки выше.');
process.exit(ok ? 0 : 1);
