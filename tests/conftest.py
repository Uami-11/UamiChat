import json
import os

import pytest

import client.ui as ui

TEST_DB_URL = os.environ.get(
    "TEST_DB_URL",
    "postgresql://uami@localhost:5433/uamichat_test",
)

os.environ["DB_URL"] = TEST_DB_URL


class FakeWebsocket:
    """Records every message sent to it so tests can assert on it."""

    def __init__(self):
        self.sent = []

    async def send(self, raw: str):
        self.sent.append(json.loads(raw))

    async def recv(self):
        raise AssertionError("tests should not receive on FakeWebsocket")


@pytest.fixture
def fake_ws():
    return FakeWebsocket()


@pytest.fixture
def console():
    """Swap ui.console for a recording console and return it."""
    from rich.console import Console

    original = ui.console
    ui.console = Console(record=True)
    yield ui.console
    ui.console = original
