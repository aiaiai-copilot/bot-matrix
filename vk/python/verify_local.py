# Локальная проверка VK echo-бота БЕЗ реального токена и БЕЗ обращения к проду VK.
# Поднимаем фейковый VK-сервер (aiohttp), направляем НАСТОЯЩИЙ SDK на него (api.API_URL),
# симулируем Bots Long Poll и ловим исходящие messages.send (это и есть ответы бота).
# Хендлеры берём из bot.py напрямую (from bot import labeler) — гоняем реальные обработчики.
import asyncio
import shutil
import socket
import sys

from aiohttp import web

from vkbottle import API
from vkbottle.bot import Bot

from bot import GREETING, labeler  # реальные хендлеры on_start + echo, зарегистрированные на labeler

GROUP_ID = 42
ECHO_PEER = 2000000001
START_PEER = 2000000002
PROBE_PEER = 2000000003
ECHO_TEXT = "Привет, VK!"
TS = 1700000000

# client_info обязателен в каждом апдейте (иначе MessageMin не собирается).
CLIENT_INFO = {
    "button_actions": ["text"],
    "keyboard": True,
    "inline_keyboard": True,
    "carousel": False,
    "lang_id": 0,
}

posts = []            # пойманные messages.send: {peer_ids, text, access_token, v}
batch_delivered = False


def _message(msg_id, peer_id, from_id, text, payload=None):
    # Обязательные для vkbottle MessageMin поля + ловушка fwd_messages: [].
    msg = {
        "id": msg_id,
        "date": TS,
        "peer_id": peer_id,
        "from_id": from_id,
        "text": text,
        "conversation_message_id": msg_id,
        "out": 0,
        "version": 0,
        "fwd_messages": [],
        "attachments": [],
    }
    if payload is not None:
        msg["payload"] = payload
    return msg


def _update(msg_id, peer_id, from_id, text, payload=None):
    return {
        "type": "message_new",
        "object": {
            "client_info": CLIENT_INFO,
            "message": _message(msg_id, peer_id, from_id, text, payload),
        },
        "group_id": GROUP_ID,
    }


def make_app(base_url):
    async def handle_method(request):
        method = request.match_info["method"]
        if method == "groups.getById":
            return web.json_response({"response": {"groups": [{"id": GROUP_ID}]}})
        if method == "groups.getLongPollServer":
            # server используется дословно как URL → замыкаем long poll на себя
            return web.json_response({"response": {"key": "k", "server": f"{base_url}/longpoll", "ts": "1"}})
        if method == "messages.send":
            form = await request.post()                # параметры метода — form-data
            posts.append({
                "peer_ids": form.get("peer_ids"),
                "text": form.get("message"),
                "access_token": request.query.get("access_token"),  # авторизация — в query
                "v": request.query.get("v"),
            })
            print(f"[mock] ← messages.send peer_ids={form.get('peer_ids')} text={form.get('message')!r}")
            peer = int(form.get("peer_ids")) if form.get("peer_ids") else 0
            # при peer_ids SDK ждёт СПИСОК
            return web.json_response({"response": [{"peer_id": peer, "message_id": 555, "conversation_message_id": 7}]})
        return web.json_response({"response": 1})      # прочие методы — безобидный дефолт

    async def handle_longpoll(request):
        global batch_delivered
        if not batch_delivered:
            batch_delivered = True
            print("[mock] → отдаю 3 апдейта: текст, «Начать»+payload, probe(text='')")
            return web.json_response({"ts": "2", "updates": [
                _update(1, ECHO_PEER, 101, ECHO_TEXT),
                _update(2, START_PEER, 102, "Начать", payload='{"command": "start"}'),
                _update(3, PROBE_PEER, 103, ""),  # attachment-only: text="" → ответа быть не должно
            ]})
        await asyncio.sleep(0.3)  # эмуляция long-poll: пусто с задержкой (anti-busy-loop + быстрый stop)
        return web.json_response({"ts": "2", "updates": []})

    app = web.Application()
    app.router.add_post("/method/{method}", handle_method)
    app.router.add_post("/longpoll", handle_longpoll)
    return app


async def main() -> int:
    # пред-биндим сокет, чтобы знать порт до старта (как в max/python)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    base_url = f"http://127.0.0.1:{port}"

    runner = web.AppRunner(make_app(base_url))
    await runner.setup()
    site = web.SockSite(runner, sock)
    await site.start()
    print(f"[mock] фейковый VK слушает {base_url}\n")

    # НАСТОЯЩИЙ SDK, направленный на мок. API_URL — инстанс-атрибут перекрывает классовый;
    # ОБЯЗАТЕЛЕН хвост /method/ со слэшем (код делает конкатенацию API_URL + method).
    api = API("mock-token")
    api.API_URL = f"{base_url}/method/"
    bot = Bot(api=api, labeler=labeler)

    polling_task = asyncio.create_task(bot.run_polling())

    # ждём 2 ожидаемых messages.send (эхо + приветствие) максимум ~10 с
    for _ in range(100):
        if len(posts) >= 2:
            break
        await asyncio.sleep(0.1)
    await asyncio.sleep(1.0)  # шанс на возможный (нежелательный) ответ на probe

    bot.polling.stop()
    polling_task.cancel()
    try:
        await polling_task
    except asyncio.CancelledError:
        pass
    await runner.cleanup()
    shutil.rmtree(".vkbottle", ignore_errors=True)  # BotPolling пишет ./.vkbottle/bot-polling/{id}.json

    # --- проверки (зеркало max/python) ---
    echo_post = next((p for p in posts if p["peer_ids"] == str(ECHO_PEER)), None)
    start_post = next((p for p in posts if p["peer_ids"] == str(START_PEER)), None)

    text_ok = echo_post is not None and echo_post["text"] == ECHO_TEXT
    start_ok = start_post is not None and start_post["text"] == GREETING
    auth_ok = len(posts) > 0 and all(p["access_token"] == "mock-token" and p["v"] == "5.199" for p in posts)
    probe_ok = len(posts) == 2 and not any(p["peer_ids"] == str(PROBE_PEER) for p in posts)

    print("\n=== РЕЗУЛЬТАТ ===")
    print(f"✅ эхо текста:        {(echo_post['text'] if echo_post else None)!r}  (ожидали {ECHO_TEXT!r})  {'✅' if text_ok else '❌'}")
    print(f"✅ «Начать» payload:  {(start_post['text'] if start_post else None)!r}  (приветствие, НЕ эхо «Начать»)  {'✅' if start_ok else '❌'}")
    print(f"✅ авторизация:       access_token=mock-token и v=5.199 в query  {'✅' if auth_ok else '❌'}")
    print(f"🔍 probe:             messages.send всего {len(posts)}  (ожидали 2; на text='' ответа нет)  {'✅' if probe_ok else '❌'}")

    ok = text_ok and start_ok and auth_ok and probe_ok
    print("\n✅ PASS: echo round-trip через настоящий SDK; payload-приветствие отдельным хендлером; пустой текст проигнорирован."
          if ok else "\n❌ FAIL: см. отметки выше.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
