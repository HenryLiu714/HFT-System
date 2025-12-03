"""
Market data replayer for the HFT system.

This script reads historical market data from a CSV file and replays it
as FIX Market Data Incremental Refresh (35=X) messages over UDP to the
HFT system. The goal is to drive the existing system with "real" or
recorded data instead of purely synthetic pings.

Usage (from project root, with CLIENT_IN_PORT set in the environment):

    python -m real_data_tests.replayer --csv path/to/data.csv

CSV expectations (customisable via CLI flags):
    - A header row is required.
    - Default column names:
        timestamp:  event time (float seconds or ISO-8601 string)
        symbol:     instrument symbol, e.g. AAPL
        bid:        best bid price
        bid_size:   best bid quantity
        ask:        best ask price
        ask_size:   best ask quantity

Time handling:
    - Timestamps are interpreted as *absolute* times, but only the
      deltas between consecutive rows are used.
    - The --speed flag scales these deltas:
        speed = 1.0  -> realtime
        speed = 2.0  -> 2x faster than realtime
        speed = 0.5  -> 0.5x (slower) than realtime
"""

from __future__ import annotations

import argparse
import csv
import os
import socket
import time
from datetime import datetime
from typing import Optional, Tuple


SOH = "\x01"


def _get_int_env(name: str) -> int:
    value = os.getenv(name)
    if value is None:
        raise RuntimeError(f"Environment variable {name} is required (got None)")
    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError(
            f"Environment variable {name} must be an int, got {value!r}"
        ) from exc


def _parse_timestamp(raw: str) -> float:
    """
    Parse a timestamp from CSV into seconds since epoch (float).

    Supports:
        - plain float/int seconds (e.g. 1700000000.123)
        - ISO-8601 strings understood by datetime.fromisoformat
    """
    raw = raw.strip()
    if not raw:
        raise ValueError("Empty timestamp value")

    # Try numeric seconds first
    try:
        return float(raw)
    except ValueError:
        pass

    # Fallback to ISO-8601 style datetime
    try:
        dt = datetime.fromisoformat(raw)
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"Unrecognised timestamp format: {raw!r}") from exc
    return dt.timestamp()


def build_md_incremental(
    symbol: str,
    bid: float,
    bid_size: float,
    ask: float,
    ask_size: float,
) -> str:
    """
    Build a minimal FIX Market Data Incremental Refresh (35=X) message.

    This is intentionally simple and aimed at exercising the parser and
    strategy logic, not at being a complete FIX implementation.
    """
    parts = [
        "8=FIX.4.4",
        "35=X",  # Market Data Incremental Refresh
        f"55={symbol}",
        # Non-standard but parser-friendly encoding:
        # 132 / 133: bid / ask, 134 / 135: bid_size / ask_size.
        # This avoids repeating tags, which the simple C++ FIXObject
        # does not support.
        f"132={bid}",       # best bid price
        f"133={ask}",       # best ask price
        f"134={bid_size}",  # best bid size
        f"135={ask_size}",  # best ask size
    ]
    return SOH.join(parts) + SOH


def replay_csv(
    csv_path: str,
    host: str,
    port: int,
    *,
    timestamp_col: str = "timestamp",
    symbol_col: str = "symbol",
    bid_col: str = "bid",
    bid_size_col: str = "bid_size",
    ask_col: str = "ask",
    ask_size_col: str = "ask_size",
    speed: float = 1.0,
    symbol_filter: Optional[str] = None,
) -> Tuple[int, float]:
    """
    Replay market data from a CSV file as FIX messages over UDP.

    Returns (rows_sent, wall_clock_seconds).
    """
    if speed <= 0:
        raise ValueError("speed must be positive")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    sent = 0
    start_wall = time.perf_counter()
    prev_ts: Optional[float] = None

    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                ts = _parse_timestamp(row[timestamp_col])
                symbol = row[symbol_col].strip()
                if symbol_filter and symbol != symbol_filter:
                    prev_ts = ts
                    continue

                bid = float(row[bid_col])
                bid_size = float(row[bid_size_col])
                ask = float(row[ask_col])
                ask_size = float(row[ask_size_col])
            except KeyError as exc:
                raise KeyError(f"Missing expected CSV column: {exc}") from exc
            except ValueError:
                # Skip rows with unparsable numeric fields
                prev_ts = ts if "ts" in locals() else prev_ts
                continue

            if prev_ts is not None:
                delta = (ts - prev_ts) / speed
                if delta > 0:
                    time.sleep(delta)
            prev_ts = ts

            msg = build_md_incremental(
                symbol=symbol,
                bid=bid,
                bid_size=bid_size,
                ask=ask,
                ask_size=ask_size,
            )
            sock.sendto(msg.encode("utf-8"), (host, port))
            sent += 1

    total_wall = time.perf_counter() - start_wall
    sock.close()
    return sent, total_wall


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Replay historical market data from CSV as FIX 35=X "
            "messages over UDP to the HFT system."
        )
    )
    parser.add_argument(
        "--csv",
        default="real_data_tests/dummy_market_data.csv",
        help=(
            "Path to CSV file containing historical market data. "
            "Defaults to real_data_tests/dummy_market_data.csv."
        ),
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Destination host for UDP (default: 127.0.0.1).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help=(
            "Destination UDP port. "
            "If omitted, uses CLIENT_IN_PORT from the environment."
        ),
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=1.0,
        help="Speed factor vs. realtime (default: 1.0).",
    )
    parser.add_argument(
        "--symbol-filter",
        type=str,
        default=None,
        help="If set, only replay rows for this symbol.",
    )
    parser.add_argument(
        "--timestamp-col",
        default="timestamp",
        help="Name of the timestamp column in the CSV (default: timestamp).",
    )
    parser.add_argument(
        "--symbol-col",
        default="symbol",
        help="Name of the symbol column in the CSV (default: symbol).",
    )
    parser.add_argument(
        "--bid-col",
        default="bid",
        help="Name of the best bid price column (default: bid).",
    )
    parser.add_argument(
        "--bid-size-col",
        default="bid_size",
        help="Name of the best bid size column (default: bid_size).",
    )
    parser.add_argument(
        "--ask-col",
        default="ask",
        help="Name of the best ask price column (default: ask).",
    )
    parser.add_argument(
        "--ask-size-col",
        default="ask_size",
        help="Name of the best ask size column (default: ask_size).",
    )

    args = parser.parse_args()

    if args.port is not None:
        dest_port = args.port
    else:
        try:
            dest_port = _get_int_env("CLIENT_IN_PORT")
        except RuntimeError:
            # Fallback to the C++ system's default port (see hft_system/include/config.h)
            dest_port = 9999

    print(
        f"Replaying {args.csv!r} to {args.host}:{dest_port} "
        f"with speed factor {args.speed:.2f}..."
    )
    sent, wall = replay_csv(
        csv_path=args.csv,
        host=args.host,
        port=dest_port,
        timestamp_col=args.timestamp_col,
        symbol_col=args.symbol_col,
        bid_col=args.bid_col,
        bid_size_col=args.bid_size_col,
        ask_col=args.ask_col,
        ask_size_col=args.ask_size_col,
        speed=args.speed,
        symbol_filter=args.symbol_filter,
    )
    rate = sent / wall if wall > 0 else 0.0
    print(f"Replay complete: sent {sent} messages in {wall:.3f}s (~{rate:.1f} msg/s)")


if __name__ == "__main__":
    main()


