import pytest
from pyproxy import Proxy, Handler

class Dummy:
    pass

@pytest.mark.parametrize("key,expected", [
    (123, True),                   # int
    ((1, 2), True),                # tuple
    (Dummy(), True),              # objeto
])
def test_has_interception_non_str_keys(sample, key, expected):
    called = []

    def intercept_has(obj):
        called.append('true')
        return True

    proxy = Proxy(
        sample,
        Handler(
            has={key: intercept_has}
        )
    )

    assert key in proxy
    assert called == ['true']

def test_has_fallback_to_iterable():
    class Container:
        def __init__(self):
            self._values = {"a", "b", "c"}
        def __iter__(self):
            return iter(self._values)

    container = Container()

    proxy = Proxy(container, Handler())

    assert "a" in proxy
    assert "z" not in proxy

def test_has_fallback_to_hasattr():
    class Obj:
        def __init__(self):
            self.existing = True

    obj = Obj()

    proxy = Proxy(obj, Handler())

    assert "existing" in proxy
    assert "missing" not in proxy


def test_delete_interception(sample):
    deleted = []

    errr = 'errrrr'
    
    def intercept_delete(_):
        deleted.append('toremove')
        raise ValueError(errr)

    sample.to_remove = 123

    proxy = Proxy(
        sample,
        Handler(
            delete={"toremove": intercept_delete}
        )
    )
    with pytest.raises(ValueError, match=errr):
        del proxy.toremove

    assert deleted == ["toremove"]
    assert not hasattr(sample, "toremove")
