import pytest

# Import the local client helper that lives alongside this file.
# We avoid relative imports here because pytest loads conftest.py
# as a top-level module (no package context).
from client import UdpClient


@pytest.fixture(scope="module")
def client() -> UdpClient:
    """
    Pytest fixture providing a UDP test client that talks to the running HFT system.

    Assumes the HFT system is already running and listening on CLIENT_IN_PORT /
    EXCHANGE_IN_PORT as defined in the environment.
    """
    c = UdpClient()
    try:
        yield c
    finally:
        c.close()


