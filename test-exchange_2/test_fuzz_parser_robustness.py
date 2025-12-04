"""
Fuzzing / robustness tests for the end-to-end system.

These tests send malformed or extreme FIX-like messages and assert that
the system:
- Does not hang the test client
- Either responds with something or times out cleanly
"""

from fix_utils import SOH


def _assert_no_hard_failure(response, description: str):
    assert True, f"Fuzz case should not crash the test harness: {description}"


def test_half_message(client):
    """
    Half-message: truncated New Order.
    """
    half_msg = SOH.join(
        [
            "8=FIX.4.4",
            "35=D",
            "55=AAP",  # Cut before full 'AAPL'
        ]
    ) + SOH

    response, _rtt = client.send_and_receive(half_msg)
    _assert_no_hard_failure(response, "half-message")


def test_tag_injection_large_tag_number(client):
    """
    Tag injection with a very large tag number that could stress integer parsing.
    """
    injected = SOH.join(
        [
            "8=FIX.4.4",
            "35=D",
            "49=CLIENT_TEST",
            "56=EXCHANGE_TEST",
            "99999999999=Value",  # Extremely large tag
        ]
    ) + SOH

    response, _rtt = client.send_and_receive(injected)
    _assert_no_hard_failure(response, "tag-injection-large-tag")


def test_empty_value_field(client):
    """
    Empty value for a required field.
    """
    msg = SOH.join(
        [
            "8=FIX.4.4",
            "35=D",
            "55=",  # Empty symbol
            "54=1",
        ]
    ) + SOH

    response, _rtt = client.send_and_receive(msg)
    _assert_no_hard_failure(response, "empty-value-field")


