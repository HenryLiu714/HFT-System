"""
Alternate FIX test messages tuned for the C++ HFT system.

Imported via: from test_input_2 import messages

All messages use MsgType values that the C++ Handler responds to:
- 0: Heartbeat
- 1: Test Request
- A: Logon
- D: New Order - Single
"""

# 1) FIX Logon (35=A) – client logs in to the exchange
fix_logon = (
    "8=FIX.4.2\x019=65\x0135=A\x0134=1\x0149=CLIENT1\x0156=EXCHANGE\x01"
    "52=20251001-18:30:00.000\x0198=0\x01108=30\x0110=128\x01"
)

# 2) Heartbeat (35=0) – simple keep-alive
fix_heartbeat = (
    "8=FIX.4.2\x019=50\x0135=0\x0134=2\x0149=CLIENT1\x0156=EXCHANGE\x01"
    "52=20251001-18:31:00.000\x0110=099\x01"
)

# 3) Test Request (35=1) – expects heartbeat with matching 112
fix_test_request = (
    "8=FIX.4.2\x019=60\x0135=1\x0134=3\x0149=CLIENT1\x0156=EXCHANGE\x01"
    "52=20251001-18:31:30.000\x01112=TEST_REQ_1\x0110=100\x01"
)

# 4) New Order - Single (35=D) – buy 100 AAPL
fix_new_order_1 = (
    "8=FIX.4.4\x019=112\x0135=D\x0134=4\x0149=CLIENT1\x0156=EXCHANGE\x01"
    "52=20251001-18:32:00.000\x0111=ORDER123\x0155=AAPL\x0154=1\x01"
    "38=100\x0144=172.35\x0140=2\x0110=072\x01"
)

# 5) New Order - Single (35=D) – sell 50 AAPL
fix_new_order_2 = (
    "8=FIX.4.4\x019=110\x0135=D\x0134=5\x0149=CLIENT1\x0156=EXCHANGE\x01"
    "52=20251001-18:32:05.000\x0111=ORDER124\x0155=AAPL\x0154=2\x01"
    "38=50\x0144=172.40\x0140=2\x0110=073\x01"
)

# Message list used by benchmarking.py (once you change the import)
messages = [
    fix_logon,
    fix_heartbeat,
    fix_test_request,
    fix_new_order_1,
    fix_new_order_2,
]


