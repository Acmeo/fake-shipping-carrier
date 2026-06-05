"""Shared fixtures for fake-shipping-carrier tests."""

from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from fake_shipping_carrier.app import app
from fake_shipping_carrier.store import Store


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    app.state.store = Store()
    with TestClient(app) as c:
        yield c
