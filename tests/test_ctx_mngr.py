from pyproxy import Handler, wrap
from tests.conftest import Sample


def test_proxy_as_context_manager_direct(sample):
    proxy = wrap(sample, Handler())

    with proxy as s:
        assert isinstance(s, Sample)
        assert s.entered is True
        assert s is sample  # retorna o próprio target
        assert sample.exited is False

    assert sample.exited is True


def test_proxy_with_context_handler(sample):
    log = []

    def custom_context(obj):
        class DummyCtx:
            def __enter__(self_):
                log.append("entered")
                return "custom-object"

            def __exit__(self_, exc_type, exc_val, exc_tb):
                log.append("exited")

        return DummyCtx()

    handler = Handler(context=custom_context)
    proxy = wrap(sample, handler)

    with proxy as s:
        assert s == "custom-object"
        assert log == ["entered"]

    assert log == ["entered", "exited"]


def test_context_manager_error_without_handler_or_dunder(sample, monkeypatch):
    monkeypatch.delattr(Sample, "__enter__", raising=True)
    monkeypatch.delattr(Sample, "__exit__", raising=True)

    proxy = wrap(sample, Handler())

    import pytest

    with pytest.raises(TypeError, match="context manager protocol"):
        with proxy:
            pass
