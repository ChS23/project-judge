import hashlib
import hmac
import json
from unittest.mock import patch

from judge.webhook.app import app


def _sign(body: bytes, secret: str) -> str:
    sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={sig}"


class FakeReceive:
    def __init__(self, body: bytes):
        self.body = body
        self.called = False

    async def __call__(self):
        if not self.called:
            self.called = True
            return {"body": self.body, "more_body": False}
        return {"body": b"", "more_body": False}


class FakeSend:
    def __init__(self):
        self.responses = []

    async def __call__(self, message):
        self.responses.append(message)

    @property
    def status(self):
        for r in self.responses:
            if r.get("type") == "http.response.start":
                return r["status"]
        return None

    @property
    def body(self):
        for r in self.responses:
            if r.get("type") == "http.response.body":
                return json.loads(r["body"])
        return None


@patch("judge.webhook.app._check_health", return_value={"status": "ok", "checks": {}})
async def test_health(_mock_health):
    scope = {"type": "http", "method": "GET", "path": "/health", "headers": []}
    send = FakeSend()
    await app(scope, None, send)
    assert send.status == 200
    assert send.body["status"] == "ok"


async def test_404():
    scope = {"type": "http", "method": "GET", "path": "/unknown", "headers": []}
    send = FakeSend()
    await app(scope, None, send)
    assert send.status == 404


async def test_webhook_invalid_signature():
    body = b'{"action": "opened"}'
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/webhook",
        "headers": [
            (b"x-github-event", b"pull_request"),
            (b"x-hub-signature-256", b"sha256=invalid"),
            (b"x-github-delivery", b"test-123"),
            (b"content-type", b"application/json"),
        ],
    }
    send = FakeSend()
    receive = FakeReceive(body)
    await app(scope, receive, send)
    assert send.status == 401
