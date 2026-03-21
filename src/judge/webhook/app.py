import json

from gidgethub.sansio import Event

from judge.settings import settings
from judge.webhook.router import router


async def app(scope, receive, send):
    if scope["type"] != "http":
        return

    path = scope["path"]
    method = scope["method"]

    if method == "GET" and path == "/health":
        await _respond(send, 200, {"status": "ok"})
        return

    if method == "POST" and path == "/webhook":
        body = await _read_body(receive)
        headers = {k.decode(): v.decode() for k, v in scope["headers"]}

        try:
            secret = settings.github_webhook_secret
            event = Event.from_http(headers, body, secret=secret)
        except Exception:
            await _respond(send, 401, {"error": "invalid signature"})
            return

        await router.dispatch(event)
        await _respond(send, 202, {"status": "accepted"})
        return

    await _respond(send, 404, {"error": "not found"})


async def _read_body(receive) -> bytes:
    body = b""
    while True:
        message = await receive()
        body += message.get("body", b"")
        if not message.get("more_body", False):
            return body


async def _respond(send, status: int, data: dict) -> None:
    payload = json.dumps(data).encode()
    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": [(b"content-type", b"application/json")],
        }
    )
    await send({"type": "http.response.body", "body": payload})
