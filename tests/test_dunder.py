import pytest

from pyproxy import Handler, Proxy


@pytest.fixture
def list_data():
    return [1, 2, 3]


def test_default_len(list_data):
    proxy = Proxy(list_data, Handler())
    assert len(proxy) == 3


def test_custom_len():
    def fake_len(obj):
        return 42

    proxy = Proxy([1, 2, 3], Handler(len=fake_len))
    assert len(proxy) == 42


def test_default_eq():
    proxy = Proxy([1, 2], Handler())
    assert proxy == [1, 2]
    assert not (proxy == [2, 1])


def test_custom_eq():
    def always_equal(obj, other):
        return True

    proxy = Proxy([99], Handler(eq=always_equal))
    assert proxy == "anything"


def test_default_ne():
    proxy = Proxy([1, 2], Handler())
    assert proxy != [2, 1]
    assert not (proxy != [1, 2])


def test_custom_ne():
    def always_not_equal(obj, other):
        return True

    proxy = Proxy([1, 2], Handler(ne=always_not_equal))
    assert proxy != [1, 2]


def test_default_bool():
    proxy1 = Proxy([], Handler())
    proxy2 = Proxy([1], Handler())

    assert not bool(proxy1)
    assert bool(proxy2)


def test_custom_bool():
    proxy = Proxy([], Handler(bool=lambda obj: True))
    assert bool(proxy)
