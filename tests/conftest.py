import pytest


class Sample:
    def __init__(self, value: int = 42):
        self.value = value
        self.not_proxied = "noproxy"
        self.entered = False
        self.exited = False

    def add(self, a, b):
        return a + b

    def greet(self, name):
        return f"Hello, {name}"

    def __enter__(self):
        self.entered = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.exited = True


@pytest.fixture
def sample():
    return Sample()
