"""
Lightweight FIX utilities for tests.

These helpers avoid bringing in simplefix and are only intended for
parsing/constructing messages in assertions, not for production use.
"""

from typing import Dict

SOH = "\x01"


def parse_fix(raw: str) -> Dict[str, str]:
    """
    Parse a FIX string into a simple tag -> value dictionary.

    - Ignores empty segments
    - Keeps the last occurrence of a tag (e.g. in repeating groups)
    """
    fields: Dict[str, str] = {}
    if not raw:
        return fields

    parts = raw.split(SOH)
    for part in parts:
        if not part:
            continue
        if "=" not in part:
            # Malformed field; store under a synthetic key for debugging
            fields.setdefault("_malformed", "")
            fields["_malformed"] += part + "|"
            continue
        tag, value = part.split("=", 1)
        fields[tag] = value
    return fields


def gen_new_order(symbol: str = "AAPL", price: float = 150.0, qty: int = 100) -> str:
    """
    Generate a simple New Order Single (35=D) suitable for end-to-end tests.

    This is intentionally minimal and does not compute a real checksum.
    The production exchange / C++ parser should still handle it as a basic
    New Order message for functional testing purposes.
    """
    # Note: we do not set tags 8/9/10 for simplicity here; many parsers
    # (including yours) only care about the tag=value pairs, not checksums.
    parts = [
        "8=FIX.4.4",
        "35=D",
        "49=CLIENT_TEST",
        "56=EXCHANGE_TEST",
        "55=" + symbol,
        "54=1",  # Buy
        f"38={qty}",
        f"44={price}",
        "40=2",  # Limit
    ]
    return SOH.join(parts) + SOH


