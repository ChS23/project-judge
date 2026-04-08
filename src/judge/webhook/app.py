import json

import structlog
from gidgethub.sansio import Event

from judge.settings import settings
from judge.tasks.broker import broker
from judge.webhook.router import router

logger = structlog.get_logger()

_broker_started = False


async def _check_health() -> dict:
    """Deep health check: Redis, LLM availability."""
    checks = {}

    # Redis
    try:
        import redis.asyncio as aioredis

        r = aioredis.from_url(settings.redis_url)
        pong = r.ping()
        if hasattr(pong, "__await__"):
            await pong
        checks["redis"] = "ok"
        close = r.aclose()
        if hasattr(close, "__await__"):
            await close
    except Exception as e:
        checks["redis"] = f"error: {e}"

    # LLM (lightweight check — just verify API key works)
    if settings.zai_api_key and settings.zai_api_key != "test":
        try:
            import httpx

            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.post(
                    f"{settings.zai_base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {settings.zai_api_key}"},
                    json={
                        "model": settings.zai_model,
                        "messages": [{"role": "user", "content": "ping"}],
                        "max_tokens": 1,
                    },
                )
                checks["llm"] = (
                    "ok" if resp.status_code < 500 else f"error: {resp.status_code}"
                )
        except Exception as e:
            checks["llm"] = f"error: {e}"
    else:
        checks["llm"] = "not configured"

    all_ok = all(v == "ok" for v in checks.values() if v != "not configured")
    return {"status": "ok" if all_ok else "degraded", "checks": checks}


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
        health = await _check_health()
        status = 200 if health["status"] == "ok" else 503
        await _respond(send, status, health)
        return

    if method == "POST" and path == "/webhook":
        body = await _read_body(receive)
        headers = {k.decode(): v.decode() for k, v in scope["headers"]}

        try:
            secret = settings.github_webhook_secret
            event = Event.from_http(headers, body, secret=secret)
        except json.JSONDecodeError:
            await logger.awarning("webhook_malformed_body")
            await _respond(send, 400, {"error": "malformed JSON body"})
            return
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


async def _read_body(receive, max_size: int = 1_048_576) -> bytes:
    body = b""
    while True:
        message = await receive()
        body += message.get("body", b"")
        if len(body) > max_size:
            msg = "Request body too large"
            raise ValueError(msg)
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
