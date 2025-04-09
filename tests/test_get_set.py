# tests/test_get_set.py
from pyproxy import Handler, wrap


def test_get_interception(sample):
    def get_value(obj):
        return "intercepted"

    proxy = wrap(
        sample,
        Handler(
            get={
                "value": get_value,
                "proxyonly": lambda _: "proxyonlyfield",
                "prop1": lambda _: "different_prop1",
            }
        ),
    )

    assert sample.value == 42
    assert sample.prop1 == "prop1"
    assert not hasattr(sample, "proxyonly")

    assert proxy.value == "intercepted"

    assert proxy.not_proxied == "noproxy"
    assert proxy.proxyonly == "proxyonlyfield"
    assert proxy.prop1 == "different_prop1"

    sample.prop1 = "prop2"
    assert sample.prop1 == "prop2"
    assert proxy.prop1 == "different_prop1"


def test_set_interception(sample):
    recorded = {}

    def set_value(obj, val):
        recorded["value"] = val
        obj.value = val

    def set_nofield(obj, val):
        obj.nofield = val

    def set_prop1(obj, val):
        obj.prop1 = val

    proxy = wrap(
        sample,
        Handler(set={"value": set_value, "foo": set_nofield, "prop1": set_prop1}),
    )

    proxy.value = 99
    assert sample.value == 99
    assert recorded["value"] == 99

    # Campo não interceptado deve funcionar normalmente
    proxy.not_proxied = "changed"
    assert sample.not_proxied == "changed"

    proxy.foo = "bar"
    assert proxy.nofield == "bar"

    assert proxy.prop1 == "prop1"
    proxy.prop1 = "otherval"
    assert proxy.prop1 == "otherval"
