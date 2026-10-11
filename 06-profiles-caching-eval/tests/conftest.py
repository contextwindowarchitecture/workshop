from __future__ import annotations

import pytest

import impl


@pytest.fixture
def which():
    return impl.name()
