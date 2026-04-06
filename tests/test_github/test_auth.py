import time
from unittest.mock import AsyncMock, MagicMock, patch

from judge.github.auth import _token_cache, get_installation_token


@patch("judge.github.auth._make_jwt", return_value="fake-jwt")
@patch("judge.github.auth.httpx.AsyncClient")
async def test_get_installation_token(mock_client_cls, _mock_jwt):
    _token_cache.clear()

    mock_resp = MagicMock()
    mock_resp.json.return_value = {"token": "ghs_test123"}

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_resp
    mock_client_cls.return_value.__aenter__.return_value = mock_client

    token = await get_installation_token(12345)
    assert token == "ghs_test123"
    _token_cache.clear()


@patch("judge.github.auth._make_jwt", return_value="fake-jwt")
@patch("judge.github.auth.httpx.AsyncClient")
async def test_token_cached(mock_client_cls, _mock_jwt):
    _token_cache.clear()

    mock_resp = MagicMock()
    mock_resp.json.return_value = {"token": "ghs_cached"}

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_resp
    mock_client_cls.return_value.__aenter__.return_value = mock_client

    token1 = await get_installation_token(99)
    token2 = await get_installation_token(99)
    assert token1 == token2 == "ghs_cached"
    assert mock_client.post.call_count == 1
    _token_cache.clear()


@patch("judge.github.auth._make_jwt", return_value="fake-jwt")
@patch("judge.github.auth.httpx.AsyncClient")
async def test_token_expired(mock_client_cls, _mock_jwt):
    _token_cache.clear()
    _token_cache[77] = ("ghs_old", time.time() - 1)

    mock_resp = MagicMock()
    mock_resp.json.return_value = {"token": "ghs_new"}

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_resp
    mock_client_cls.return_value.__aenter__.return_value = mock_client

    token = await get_installation_token(77)
    assert token == "ghs_new"
    assert mock_client.post.call_count == 1
    _token_cache.clear()
