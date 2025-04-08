import pytest

from pyproxy import Handler, Proxy


class Dummy:
    def __init__(self, value: int):
        self.value = value

    def __str__(self):
        return f"<Dummy value={self.value}>"

    def __repr__(self):
        return f"Dummy({self.value})"


@pytest.fixture
def dummy():
    return Dummy(99)


def test_default_str_repr(dummy):
    proxy = Proxy(dummy, Handler())
    assert str(proxy) == str(dummy)
    assert repr(proxy) == repr(dummy)


def test_custom_str_handler(dummy):
    handler = Handler(str=lambda o: f"[custom str {o.value}]")
    proxy = Proxy(dummy, handler)
    assert str(proxy) == "[custom str 99]"


def test_custom_repr_handler(dummy):
    handler = Handler(repr=lambda o: f"[custom repr {o.value}]")
    proxy = Proxy(dummy, handler)
    assert repr(proxy) == "[custom repr 99]"


def test_custom_str_and_repr(dummy):
    handler = Handler(str=lambda o: "override str", repr=lambda o: "override repr")
    proxy = Proxy(dummy, handler)
    assert str(proxy) == "override str"
    assert repr(proxy) == "override repr"
