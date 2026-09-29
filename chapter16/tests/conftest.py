import pytest
from chapter16.fixtures import load_fixtures

@pytest.fixture
def lab():
    return load_fixtures()
