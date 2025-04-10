import pytest

from pyproxy import Handler, is_proxy, unwrap, wrap
from pyproxy.proxy import Proxy


def test_is_proxy_true(sample):
    proxy = wrap(sample, Handler(), spoof_class=False)
    assert is_proxy(proxy) is True


def test_is_proxy_false(sample):
    assert is_proxy(sample) is False


def test_unwrap_proxy(sample):
    proxy = wrap(sample, Handler())
    assert unwrap(proxy) is sample


def test_unwrap_non_proxy(sample):
    assert unwrap(sample) is sample


def test_spoof_class_identity(sample):
    proxy = wrap(sample, Handler(), spoof_class=True)
    assert proxy.__class__ is sample.__class__  # spoofed
    assert type(proxy) is Proxy  # real type


def test_real_class_identity_without_spoof(sample):
    proxy = wrap(sample, Handler(), spoof_class=False)
    assert proxy.__class__ is Proxy  # not spoofed
