import pytest


class Sample:
    def __init__(self, value: int = 42):
        self.value = value
        self.not_proxied = "noproxy"
        self.entered = False
        self.exited = False
        self._prop1 = "prop1"
        self.existing = True
        self.seq = {"a", "b", "c"}
        self.called = False

    @property
    def prop1(self):
        return self._prop1

    @prop1.setter
    def prop1(self, v: str):
        self._prop1 = v

    def add(self, a, b):
        return a + b

    def greet(self, name):
        return f"Hello, {name}"

    def __iter__(self):
        return iter(self.seq)

    def __enter__(self):
        self.entered = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.exited = True

    def __str__(self):
        return f"<Dummy value={self.value}>"

    def __repr__(self):
        return f"Dummy({self.value})"


@pytest.fixture
def sample():
    return Sample()
