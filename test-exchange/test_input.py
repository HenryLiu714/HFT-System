"""
Defines sample FIX messages for testing an exchange simulator.

import via test_input.messages
"""

# ---------------------------------------------------------------------------
# 1️⃣  FIX Logon Message (35=A)
#     - Sent by the client to log into the exchange session.
#     - Exchange should respond with its own Logon (35=A).
# ---------------------------------------------------------------------------
fix_logon = (
    "8=FIX.4.2\x019=65\x0135=A\x0134=1\x0149=CLIENT1\x0156=EXCHANGE\x01"
    "52=20251001-18:30:00.000\x0198=0\x01108=30\x0110=128\x01"
)

# ---------------------------------------------------------------------------
# 2️⃣  Market Data Snapshot / Full Refresh (35=W)
#     - Sent by the exchange to provide a full order book snapshot.
#     - Includes bid/ask levels with price (270) and size (271).
# ---------------------------------------------------------------------------
fix_snapshot = (
    "8=FIX.4.4\x019=178\x0135=W\x0134=2\x0149=EXCHANGE\x0156=CLIENT1\x01"
    "52=20251001-22:15:43.123\x0162=MDReqID123\x0155=AAPL\x01268=2\x01"
    "269=0\x01270=172.35\x01271=100\x01"
    "269=1\x01270=172.40\x01271=200\x01"
    "10=128\x01"
)

# ---------------------------------------------------------------------------
# 3️⃣  Market Data Incremental Refresh (35=X)
#     - Sent by the exchange to update one or more levels from the book.
#     - In this example, a new bid appears at 172.36 for 150 shares.
# ---------------------------------------------------------------------------
fix_incremental = (
    "8=FIX.4.4\x019=120\x0135=X\x0134=3\x0149=EXCHANGE\x0156=CLIENT1\x01"
    "52=20251001-22:15:44.567\x0162=MDReqID123\x01268=1\x01"
    "279=0\x01269=0\x01270=172.36\x01271=150\x01"
    "10=055\x01"
)

# ---------------------------------------------------------------------------
# 4️⃣  New Order - Single (35=D)
#     - Sent by client to place a new buy or sell order.
#     - Here: Buy 100 shares of AAPL at $172.35.
# ---------------------------------------------------------------------------
fix_new_order = (
    "8=FIX.4.4\x019=112\x0135=D\x0134=4\x0149=CLIENT1\x0156=EXCHANGE\x01"
    "52=20251001-22:16:00.000\x0111=ORDER123\x0155=AAPL\x0154=1\x01"
    "38=100\x0144=172.35\x0140=2\x0110=072\x01"
)

# ---------------------------------------------------------------------------
# 5️⃣  Execution Report (35=8)
#     - Sent by exchange to confirm, fill, or reject an order.
#     - Here: ORDER123 is accepted (OrdStatus=0).
# ---------------------------------------------------------------------------
fix_execution_report = (
    "8=FIX.4.4\x019=140\x0135=8\x0134=5\x0149=EXCHANGE\x0156=CLIENT1\x01"
    "52=20251001-22:16:00.100\x0111=ORDER123\x0137=EXORD001\x0155=AAPL\x01"
    "54=1\x0138=100\x0139=0\x0150=0\x0132=0\x0131=0\x0110=200\x01"
)

messages = [fix_logon, fix_snapshot, fix_incremental, fix_new_order, fix_execution_report]