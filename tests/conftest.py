import os

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FIXTURES = os.path.join(HERE, "fixtures")
DATA = os.path.join(ROOT, "data")


@pytest.fixture
def fixtures():
    return FIXTURES
