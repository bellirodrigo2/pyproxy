import pytest
from pyproxy import Proxy, Handler

def test_call_interception(sample):
    def intercept_add(obj, a, b):
        return (a + b) * 10

    proxy = Proxy(
        sample,
        Handler(call={"add": intercept_add})
    )

    assert proxy.add(2, 3) == 50  # interceptado
    assert proxy.greet("Alice") == "Hello, Alice"  # não interceptado

def test_call_no_interception(sample):
    proxy = Proxy(sample, Handler())  # sem call handler

    assert proxy.add(1, 2) == 3
    assert proxy.greet("Bob") == "Hello, Bob"

def test_call_nonexistent_function(sample):
    def fake_func(obj, x):
        return f"Intercepted {x} via proxy only"

    proxy = Proxy(
        sample,
        Handler(call={"nonexistent": fake_func})
    )

    assert proxy.nonexistent("test") == "Intercepted test via proxy only"

def test_call_fallback_to_getattr(sample):
    def intercept_value(obj):
        return 999
    def intercept_call(obj, a, b):
        return 999

    proxy = Proxy(
        sample,
        Handler(
            get={"value": intercept_value},
            call={'add': intercept_call}
        )
    )

    assert proxy.add(1, 2) == 999
    assert proxy.value == 999  # interceptado via get
    assert proxy.not_proxied == "noproxy"  # não interceptado
