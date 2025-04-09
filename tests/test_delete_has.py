import pytest

from pyproxy import Handler, wrap


class Dummy:
    pass


@pytest.mark.parametrize(
    "key,expected",
    [
        (123, True),  # int
        ((1, 2), True),  # tuple
        (Dummy(), True),  # objeto
    ],
)
def test_has_interception_non_str_keys(sample, key, expected):
    called = []

    def intercept_has(obj, val):
        called.append("true")
        return True

    proxy = wrap(sample, Handler(contain=intercept_has))

    assert key in proxy
    assert called == ["true"]


def test_has_fallback_to_iterable(sample):

    proxy = wrap(sample, Handler())

    assert "a" in sample
    assert "a" in proxy

    assert "z" not in sample
    assert "z" not in proxy


def test_delete_interception(sample):
    deleted = []

    errr = "errrrr"

    def intercept_delete(_):
        deleted.append("toremove")
        raise ValueError(errr)

    def delete_add(obj):
        obj.add = None

    sample.to_remove = 123

    proxy = wrap(
        sample, Handler(delete={"toremove": intercept_delete, "add": delete_add})
    )
    with pytest.raises(ValueError, match=errr):
        del proxy.toremove

    assert deleted == ["toremove"]
    assert not hasattr(sample, "toremove")

    assert proxy.add(1, 2) == 3
    del proxy.add

    with pytest.raises(TypeError):
        proxy.add(1, 2)
