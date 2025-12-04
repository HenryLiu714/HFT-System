"""
Sweep powers-of-two send rates and watch where latency starts to increase.

This script calls run_soak() programmatically for rates = 2^k and stops
once p99 latency grows beyond a configurable threshold compared to the
previous step.

Run from the project root (with the HFT system already running):

    python -m test-exchnage_2.rate_sweep

You can tweak the range and threshold with CLI flags.
"""

from __future__ import annotations

import argparse
from typing import List, Dict, Any

from .soak_benchmark import run_soak


def main() -> None:
    parser = argparse.ArgumentParser(description="Sweep powers-of-two send rates and measure latency.")
    parser.add_argument(
        "--min-exp",
        type=int,
        default=12,
        help="Minimum exponent for 2**exp (default: 7 -> 128 msg/s)",
    )
    parser.add_argument(
        "--max-exp",
        type=int,
        default=100,
        help="Maximum exponent for 2**exp (default: 30). Very large exponents "
             "will effectively behave like 'unlimited' rate.",
    )
    parser.add_argument(
        "--messages",
        type=int,
        default=5000,
        help="Messages per rate point (default: 5000)",
    )
    parser.add_argument(
        "--symbol",
        type=str,
        default="AAPL",
        help="Symbol for generated orders (default: AAPL)",
    )
    parser.add_argument(
        "--base-price",
        type=float,
        default=150.0,
        help="Base price around which to jitter orders (default: 150.0)",
    )
    parser.add_argument(
        "--p99-threshold",
        type=float,
        default=1.8,
        help="Stop when p99 grows by this factor vs previous step (default: 1.2 = +20%%)",
    )

    args = parser.parse_args()

    results: List[Dict[str, Any]] = []
    prev_p99: float | None = None

    for exp in range(args.min_exp, args.max_exp + 1):
        requested_rate = float(2 ** exp)
        print(f"\n=== Testing rate 2**{exp} = {requested_rate:.0f} msg/s ===")

        stats = run_soak(
            num_messages=args.messages,
            output_path=f"soak_{int(requested_rate)}.csv",
            symbol=args.symbol,
            base_price=args.base_price,
            rate=requested_rate,
        )

        if not stats:
            print("No stats returned, stopping sweep.")
            break

        results.append(stats)

        p99 = stats["p99"]
        eff_rate = stats["effective_rate"]
        print(f"Summary: effective_rate={eff_rate:.1f} msg/s, p99={p99/1e3:.1f} µs")

        if prev_p99 is not None and p99 > prev_p99 * args.p99_threshold:
            print(
                f"p99 increased beyond threshold factor {args.p99_threshold:.2f} "
                f"(prev {prev_p99/1e3:.1f} µs -> now {p99/1e3:.1f} µs). Stopping."
            )
            break

        prev_p99 = p99

    print("\nSweep complete. Collected points:")
    for r in results:
        print(
            f"requested={r['requested_rate']:.0f} msg/s, "
            f"effective={r['effective_rate']:.1f} msg/s, "
            f"p50={r['p50']/1e3:.1f} µs, p99={r['p99']/1e3:.1f} µs, "
            f"max={r['max']/1e3:.1f} µs"
        )


if __name__ == "__main__":
    main()


