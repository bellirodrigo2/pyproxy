import pytest

class Sample:
    def __init__(self, value: int = 42):
        self.value = value
        self.not_proxied = 'noproxy'

    def add(self, a, b):
        return a + b

    def greet(self, name):
        return f"Hello, {name}"

@pytest.fixture
def sample():
    return Sample()
