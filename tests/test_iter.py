# tests/test_iterator.py

import pytest

from pyproxy import Handler, Proxy


@pytest.fixture
def iterable_sample():
    class IterableSample:
        def __init__(self):
            self.data = [1, 2, 3]

        def __iter__(self):
            return iter(self.data)

    return IterableSample()


def test_default_iterator_behavior(iterable_sample):
    proxy = Proxy(target=iterable_sample, handler=Handler())
    result = list(proxy)
    assert result == [1, 2, 3]


def test_iterator_handler_override(iterable_sample):
    # handler que inverte os dados
    def reverse_iter(obj):
        return reversed(obj.data)

    handler = Handler(iterator=reverse_iter)
    proxy = Proxy(target=iterable_sample, handler=handler)
    result = list(proxy)
    assert result == [3, 2, 1]


def test_iterator_handler_custom_sequence():
    class Dummy:
        def __init__(self):
            self.x = 10

    dummy = Dummy()

    def custom_iter(obj):
        return iter(["a", "b", "c"])

    proxy = Proxy(target=dummy, handler=Handler(iterator=custom_iter))
    assert list(proxy) == ["a", "b", "c"]


def test_next_on_proxy(iterable_sample):
    proxy = Proxy(target=iterable_sample, handler=Handler())
    assert next(proxy) == 1
    assert next(proxy) == 2
    assert next(proxy) == 3
    with pytest.raises(StopIteration):
        next(proxy)


def test_next_on_proxy_with_iterator_handler():
    class Dummy:
        def __init__(self):
            self.called = False

    dummy = Dummy()

    def custom_iter(obj):
        obj.called = True
        return iter(["x", "y"])

    proxy = Proxy(target=dummy, handler=Handler(iterator=custom_iter))
    assert next(proxy) == "x"
    assert next(proxy) == "y"
    with pytest.raises(StopIteration):
        next(proxy)
    assert dummy.called
