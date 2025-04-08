import pytest

from pyproxy import Handler, Proxy


@pytest.fixture
def data_dict():
    return {"a": 1, "b": 2}


def test_default_getitem(data_dict):
    proxy = Proxy(data_dict, Handler())
    assert proxy["a"] == 1
    assert proxy["b"] == 2


def test_custom_getitem(data_dict):
    def upper_key(obj, key):
        return obj[key.upper()]

    wrapped = {"A": 10, "B": 20}
    proxy = Proxy(wrapped, Handler(getitem=upper_key))
    assert proxy["a"] == 10
    assert proxy["b"] == 20


def test_getitem_missing_key_raises():
    proxy = Proxy({}, Handler())
    with pytest.raises(KeyError):
        _ = proxy["missing"]


def test_default_setitem(data_dict):
    proxy = Proxy(data_dict, Handler())
    proxy["c"] = 3
    assert proxy["c"] == 3
    assert data_dict["c"] == 3  # verifica se o target também foi atualizado


def test_custom_setitem():
    calls = []

    def custom_set(obj, key, value):
        calls.append((key, value))
        obj[key.lower()] = value

    wrapped = {}
    proxy = Proxy(wrapped, Handler(setitem=custom_set))
    proxy["X"] = 42

    assert wrapped["x"] == 42
    assert calls == [("X", 42)]
