"""
Functional tests: assert semantics of the round-trip FIX flow.

These tests intentionally talk to the live HFT system over UDP and assume
that:
- A New Order (35=D) eventually results in either:
  - Execution Report (35=8), or
  - Reject (35=3)
"""

from fix_utils import gen_new_order, parse_fix


def test_order_acknowledgment(client):
    # 1. Send Order
    order_msg = gen_new_order(symbol="AAPL", price=150.0)
    response, rtt = client.send_and_receive(order_msg)

    assert response is not None, "No response from HFT system within timeout"

    # 2. Parse and assert basic semantics
    parsed = parse_fix(response)

    msg_type = parsed.get("35")
    assert msg_type in {"8", "3"}, f"Expected Execution Report (8) or Reject (3), got {msg_type!r}"

    # Example extra assertion for ExecType when we received an Execution Report.
    if msg_type == "8":
        exec_type = parsed.get("150")
        assert exec_type is not None, "Execution Report missing ExecType (150)"


