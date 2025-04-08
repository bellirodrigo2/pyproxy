import pytest

from pyproxy import Handler, Proxy, is_proxy, unwrap


class Dummy:
    pass


@pytest.fixture
def dummy():
    return Dummy()


def test_is_proxy_true(dummy):
    proxy = Proxy.wrap(dummy, Handler(), spoof_class=False)
    assert is_proxy(proxy) is True


def test_is_proxy_false(dummy):
    assert is_proxy(dummy) is False


def test_unwrap_proxy(dummy):
    proxy = Proxy.wrap(dummy, Handler())
    assert unwrap(proxy) is dummy


def test_unwrap_non_proxy(dummy):
    assert unwrap(dummy) is dummy


def test_spoof_class_identity(dummy):
    proxy = Proxy.wrap(dummy, Handler(), spoof_class=True)
    assert proxy.__class__ is dummy.__class__  # spoofed
    assert type(proxy) is Proxy  # real type


def test_real_class_identity_without_spoof(dummy):
    proxy = Proxy.wrap(dummy, Handler(), spoof_class=False)
    assert proxy.__class__ is Proxy  # not spoofed
