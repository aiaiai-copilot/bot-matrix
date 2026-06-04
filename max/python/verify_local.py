# Локальная проверка echo-бота БЕЗ реального токена и БЕЗ обращения к проду MAX.
# Поднимаем фейковый MAX-сервер (aiohttp), направляем настоящий SDK на него (bot.api_url),
# симулируем GET /updates и ловим исходящие POST /messages (это и есть эхо).
# Хендлеры берём из bot.py напрямую (from bot import dp) — гоняем реальные обработчики бота.
import asyncio
import socket
import sys

from aiohttp import web

from maxapi import Bot
from bot import dp  # реальные хендлеры on_start + echo, зарегистрированные на dp

# --- фикстуры входящих апдейтов ---
ECHO_TEXT = "Привет, MAX!"
GREETING = "Привет! Я эхо-бот. Напиши мне что-нибудь — отвечу тем же."
ECHO_CHAT_ID = 777
START_CHAT_ID = 779
PROBE_CHAT_ID = 888
TS = 1700000000000

posts = []            # пойманные POST /messages: {chat_id, text, authorization}
batch_delivered = False


def _user(uid, name, is_bot=False, username=None):
    return {
        "user_id": uid,
        "first_name": name,
        "username": username,
        "is_bot": is_bot,
        "last_activity_time": TS,
    }


def _message_update(chat_id, text):
    return {
        "update_type": "message_created",
        "timestamp": TS,
        "message": {
            "sender": _user(42, "Tester", username="tester"),
            "recipient": {"chat_id": chat_id, "chat_type": "dialog"},
            "timestamp": TS,
            "body": {"mid": f"mid-{chat_id}", "seq": 1, "text": text, "attachments": []},
        },
    }


# --- эндпоинты фейкового MAX ---
async def handle_me(request):
    return web.json_response(_user(1, "Echo Bot", is_bot=True, username="echo_bot"))


async def handle_updates(request):
    global batch_delivered
    if not batch_delivered:
        batch_delivered = True
        print("[mock] → отдаю 3 апдейта: текст, /start, probe(text=null)")
        return web.json_response({
            "marker": 100,
            "updates": [
                _message_update(ECHO_CHAT_ID, ECHO_TEXT),
                _message_update(START_CHAT_ID, "/start"),
                _message_update(PROBE_CHAT_ID, None),  # probe: нет текста → ответа быть не должно
            ],
        })
    # эмуляция long-poll: пусто с небольшой задержкой, чтобы не было busy-loop
    await asyncio.sleep(0.3)
    return web.json_response({"marker": 100, "updates": []})


async def handle_chat(request):
    # enrich_event дозапрашивает чат для каждого message-апдейта (auto_requests=True)
    chat_id = int(request.match_info["chat_id"])
    return web.json_response({
        "chat_id": chat_id,
        "type": "dialog",
        "status": "active",
        "last_event_time": TS,
        "participants_count": 2,
        "is_public": False,
    })


async def handle_messages(request):
    chat_id = request.query.get("chat_id")
    # Авторизация в maxapi 0.9.18 — через HTTP-заголовок Authorization (а не query access_token).
    authorization = request.headers.get("Authorization")
    body = await request.json()
    print(f"[mock] ← POST /messages chat_id={chat_id} text={body.get('text')!r} Authorization={authorization}")
    posts.append({"chat_id": chat_id, "text": body.get("text"), "authorization": authorization})
    resp_msg = {
        "sender": _user(1, "Echo Bot", is_bot=True),
        "recipient": {"chat_id": int(chat_id) if chat_id else None, "chat_type": "dialog"},
        "timestamp": TS,
        "body": {"mid": "srv-1", "seq": 2, "text": body.get("text"), "attachments": []},
    }
    return web.json_response({"message": resp_msg})


async def _shutdown(polling_task, runner, bot):
    dp.polling = False
    polling_task.cancel()
    try:
        await polling_task
    except asyncio.CancelledError:
        pass
    if bot.session:
        await bot.session.close()
    await runner.cleanup()


async def main() -> int:
    app = web.Application()
    app.router.add_get("/me", handle_me)
    app.router.add_get("/updates", handle_updates)
    app.router.add_get("/chats/{chat_id}", handle_chat)
    app.router.add_post("/messages", handle_messages)

    # пред-биндим сокет, чтобы узнать порт без приватных атрибутов aiohttp
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.SockSite(runner, sock)
    await site.start()

    base_url = f"http://127.0.0.1:{port}"
    print(f"[mock] фейковый MAX слушает {base_url}\n")

    # настоящий SDK, направленный на мок
    bot = Bot("test-token")
    bot.api_url = base_url                   # перенаправляем на фейковый сервер (instance-атрибут, который читает ClientSession)
    bot.auto_check_subscriptions = False     # не дёргать GET /subscriptions перед поллингом
    # auto_requests НЕ трогаем (дефолт True) — иначе SDK не проставит message.bot и answer() упадёт

    polling_task = asyncio.create_task(dp.start_polling(bot))

    # ждём 2 ожидаемых POST'а (эхо + приветствие) максимум ~10с
    for _ in range(100):
        if len(posts) >= 2:
            break
        await asyncio.sleep(0.1)
    # пауза: дать шанс на возможный (нежелательный) ответ на probe
    await asyncio.sleep(1.0)

    await _shutdown(polling_task, runner, bot)

    # --- проверки ---
    echo_post = next((p for p in posts if p["chat_id"] == str(ECHO_CHAT_ID)), None)
    start_post = next((p for p in posts if p["chat_id"] == str(START_CHAT_ID)), None)

    text_ok = echo_post is not None and echo_post["text"] == ECHO_TEXT
    start_ok = start_post is not None and start_post["text"] == GREETING
    auth_ok = len(posts) > 0 and all(p["authorization"] == "test-token" for p in posts)
    probe_ok = len(posts) == 2 and not any(p["chat_id"] == str(PROBE_CHAT_ID) for p in posts)

    print("\n=== РЕЗУЛЬТАТ ===")
    print(f"✅ happy path — эхо текста:   {(echo_post['text'] if echo_post else None)!r}  (ожидали {ECHO_TEXT!r})  {'✅' if text_ok else '❌'}")
    print(f"✅ /start — приветствие:      {(start_post['text'] if start_post else None)!r}  (НЕ эхо '/start')  {'✅' if start_ok else '❌'}")
    print(f"✅ авторизация — заголовок Authorization на POST /messages  {'✅' if auth_ok else '❌'}")
    print(f"🔍 probe — POST'ов всего: {len(posts)}  (ожидали 2; на text=null ответа быть не должно)  {'✅' if probe_ok else '❌'}")

    ok = text_ok and start_ok and auth_ok and probe_ok
    print("\n✅ PASS: echo round-trip через настоящий SDK; /start отдельным хендлером; пустой текст проигнорирован."
          if ok else "\n❌ FAIL: см. отметки выше.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
