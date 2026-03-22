import json

import structlog
from gidgethub.sansio import Event

from judge.settings import settings
from judge.tasks.broker import broker
from judge.webhook.router import router

logger = structlog.get_logger()

_broker_started = False


async def _ensure_broker():
    global _broker_started
    if not _broker_started:
        await broker.startup()
        _broker_started = True


async def app(scope, receive, send):
    if scope["type"] == "lifespan":
        message = await receive()
        if message["type"] == "lifespan.startup":
            await _ensure_broker()
            await send({"type": "lifespan.startup.complete"})
        elif message["type"] == "lifespan.shutdown":
            await broker.shutdown()
            await send({"type": "lifespan.shutdown.complete"})
        return

    if scope["type"] != "http":
        return

    await _ensure_broker()

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
            await logger.awarning("webhook_signature_invalid")
            await _respond(send, 401, {"error": "invalid signature"})
            return

        try:
            await logger.ainfo(
                "webhook_received",
                gh_event=event.event,
                delivery=event.delivery_id,
            )
            await router.dispatch(event)
        except Exception:
            await logger.aexception("webhook_dispatch_error")
            await _respond(send, 500, {"error": "internal error"})
            return

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
