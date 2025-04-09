import pytest

from pyproxy import Handler, Proxy


def test_default_str_repr(sample):
    proxy = Proxy(sample, Handler())
    assert str(proxy) == str(sample)
    assert repr(proxy) == repr(sample)


def test_custom_str_handler(sample):
    handler = Handler(str=lambda o: f"[custom str {o.value}]")
    proxy = Proxy(sample, handler)
    assert str(proxy) == "[custom str 42]"


def test_custom_repr_handler(sample):
    handler = Handler(repr=lambda o: f"[custom repr {o.value}]")
    proxy = Proxy(sample, handler)
    assert repr(proxy) == "[custom repr 42]"


def test_custom_str_and_repr(sample):
    handler = Handler(str=lambda o: "override str", repr=lambda o: "override repr")
    proxy = Proxy(sample, handler)
    assert str(proxy) == "override str"
    assert repr(proxy) == "override repr"
