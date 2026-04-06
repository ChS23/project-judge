import time

from judge.sheets.cache import TTLCache


def test_set_and_get():
    cache = TTLCache(ttl=60)
    cache.set("key", "value")
    assert cache.get("key") == "value"


def test_get_missing_key():
    cache = TTLCache(ttl=60)
    assert cache.get("missing") is None


def test_expired_entry():
    cache = TTLCache(ttl=1)
    cache.set("key", "value")
    # Подменяем время истечения
    cache._store["key"] = ("value", time.time() - 1)
    assert cache.get("key") is None
    assert "key" not in cache._store


def test_clear():
    cache = TTLCache(ttl=60)
    cache.set("a", 1)
    cache.set("b", 2)
    cache.clear()
    assert cache.get("a") is None
    assert cache.get("b") is None


def test_overwrite():
    cache = TTLCache(ttl=60)
    cache.set("key", "old")
    cache.set("key", "new")
    assert cache.get("key") == "new"
