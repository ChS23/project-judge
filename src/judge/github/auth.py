import time

import httpx
import jwt

from judge.settings import settings

_token_cache: dict[int, tuple[str, float]] = {}


def _make_jwt() -> str:
    now = int(time.time())
    payload = {
        "iat": now - 60,
        "exp": now + 600,
        "iss": settings.github_app_id,
    }
    return jwt.encode(payload, settings.github_private_key, algorithm="RS256")


async def get_installation_token(installation_id: int) -> str:
    cached = _token_cache.get(installation_id)
    if cached and cached[1] > time.time():
        return cached[0]

    app_jwt = _make_jwt()
    url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            url,
            headers={
                "Authorization": f"Bearer {app_jwt}",
                "Accept": "application/vnd.github+json",
            },
        )
        resp.raise_for_status()

    data = resp.json()
    token = data["token"]
    expires_at = time.time() + 3300  # ~55 min
    _token_cache[installation_id] = (token, expires_at)
    return token
