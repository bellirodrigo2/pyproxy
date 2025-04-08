# tests/test_get_set.py
from pyproxy import Handler, Proxy


def test_get_interception(sample):
    def get_value(obj):
        return "intercepted"

    proxy = Proxy(
        sample,
        Handler(get={"value": get_value, "proxyonly": lambda _: "proxyonlyfield"}),
    )

    assert proxy.value == "intercepted"
    # Campo não interceptado deve retornar o valor normal
    assert proxy.not_proxied == "noproxy"
    assert proxy.proxyonly == "proxyonlyfield"


def test_set_interception(sample):
    recorded = {}

    def set_value(obj, val):
        recorded["value"] = val
        obj.value = val

    def set_nofield(obj, val):
        obj.nofield = val

    proxy = Proxy(sample, Handler(set={"value": set_value, "foo": set_nofield}))

    proxy.value = 99
    assert sample.value == 99
    assert recorded["value"] == 99

    # Campo não interceptado deve funcionar normalmente
    proxy.not_proxied = "changed"
    assert sample.not_proxied == "changed"

    proxy.foo = "bar"
    assert proxy.nofield == "bar"
