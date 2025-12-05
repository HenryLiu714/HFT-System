"""
High-volume soak benchmark for the C++ HFT system.

This script:
- Sends many FIX New Order messages over UDP using the same ports as the tests
- Records per-message send/receive timestamps and round-trip latency
- Writes results to a CSV file for later analysis / plotting

You can optionally control the **send rate** in messages per second in order
to test how latency behaves under increasing offered load.

Run from the project root (with the HFT system already running):

    pytest is NOT required here; this is a standalone script.

Examples:

    # Simple run with 10k messages at \"as fast as possible\" rate
    python -m test-exchnage_2.soak_benchmark --messages 10000 --output soak_results.csv

    # Run 5k messages at ~512 msgs/sec
    python -m test-exchnage_2.soak_benchmark --messages 5000 --rate 512 --output soak_512.csv
"""

from __future__ import annotations

import argparse
import csv
import statistics
import random
from typing import List

# Support both package-style (`python -m test-exchnage_2.soak_benchmark`)
# and direct script execution (`python test-exchnage_2/soak_benchmark.py`)
try:  # pragma: no cover - import fallback logic
    from .client import UdpClient  # type: ignore[import]
    from .fix_utils import gen_new_order, parse_fix  # type: ignore[import]
except ImportError:
    from client import UdpClient  # type: ignore[import]
    from fix_utils import gen_new_order, parse_fix  # type: ignore[import]


def run_soak(
    num_messages: int,
    output_path: str,
    symbol: str,
    base_price: float,
    rate: float | None,
) -> dict | None:
    import time

    client = UdpClient()
    latencies_ns: List[int] = []
    start_wall = time.perf_counter()

    with open(output_path, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["seq", "send_ns", "recv_ns", "rtt_ns", "msg_type"])

        interval: float | None = None
        if rate and rate > 0:
            interval = 1.0 / rate

        for i in range(num_messages):
            loop_start = time.perf_counter()

            # Add a bit of randomness around the base price to simulate market movement.
            price = round(base_price + random.uniform(-1.0, 1.0), 2)
            qty = random.randint(1, 500)

            msg = gen_new_order(symbol=symbol, price=price, qty=qty)

            response, send_ns, recv_ns = client.send_and_receive_times(msg)
            rtt_ns = recv_ns - send_ns
            msg_type = ""
            if response is not None:
                parsed = parse_fix(response)
                msg_type = parsed.get("35", "")
                latencies_ns.append(rtt_ns)

            writer.writerow([i, send_ns, recv_ns, rtt_ns, msg_type])

            # Throttle to approximate the requested send rate, if provided.
            if interval is not None:
                elapsed = time.perf_counter() - loop_start
                remaining = interval - elapsed
                if remaining > 0:
                    time.sleep(remaining)

    client.close()
    total_wall = time.perf_counter() - start_wall

    if latencies_ns:
        latencies_ns.sort()
        count = len(latencies_ns)
        p50 = _percentile(latencies_ns, 50)
        p99 = _percentile(latencies_ns, 99)
        jitter = statistics.pstdev(latencies_ns) if count > 1 else 0.0
        effective_rate = count / total_wall if total_wall > 0 else 0.0

        print(
            f"Collected {count} responses.\n"
            f"min={latencies_ns[0]/1e3:.1f} µs, "
            f"p50={p50/1e3:.1f} µs, "
            f"p99={p99/1e3:.1f} µs, "
            f"max={latencies_ns[-1]/1e3:.1f} µs, "
            f"jitter(stddev)={jitter/1e3:.1f} µs\n"
            f"Effective throughput ≈ {effective_rate:.1f} msg/s"
        )
        print(f"Results written to {output_path}")

        return {
            "requested_rate": rate,
            "effective_rate": effective_rate,
            "count": count,
            "min": latencies_ns[0],
            "p50": p50,
            "p99": p99,
            "max": latencies_ns[-1],
            "jitter": jitter,
            "total_wall_s": total_wall,
            "output_path": output_path,
        }

    print("No responses received; check that the HFT system is running and ports are correct.")
    return None


def _percentile(sorted_values: List[int], pct: float) -> float:
    """
    Simple percentile helper: pct in [0, 100].
    """
    if not sorted_values:
        return 0.0
    k = (len(sorted_values) - 1) * pct / 100.0
    f = int(k)
    c = min(f + 1, len(sorted_values) - 1)
    if f == c:
        return float(sorted_values[f])
    d0 = sorted_values[f] * (c - k)
    d1 = sorted_values[c] * (k - f)
    return d0 + d1


def main() -> None:
    parser = argparse.ArgumentParser(description="High-volume UDP soak benchmark for the HFT system.")
    parser.add_argument(
        "--messages",
        type=int,
        default=10000,
        help="Number of messages to send (default: 10000)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="soak_results.csv",
        help="Output CSV file path (default: soak_results.csv)",
    )
    parser.add_argument(
        "--symbol",
        type=str,
        default="AAPL",
        help="Symbol to use for generated New Order messages (default: AAPL)",
    )
    parser.add_argument(
        "--base-price",
        type=float,
        default=150.0,
        help="Base price around which to jitter orders (default: 150.0)",
    )
    parser.add_argument(
        "--rate",
        type=float,
        default=None,
        help="Target send rate in messages per second (default: unlimited/as fast as possible)",
    )

    args = parser.parse_args()
    run_soak(args.messages, args.output, args.symbol, args.base_price, args.rate)


if __name__ == "__main__":
    main()


