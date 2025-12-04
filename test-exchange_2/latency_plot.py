"""
Plot latency distributions from a soak benchmark CSV.

Usage (from project root, after running soak_benchmark.py):

    python -m test-exchnage_2.latency_plot --input soak_results.csv
"""

from __future__ import annotations

import argparse
import csv
from typing import List

import matplotlib.pyplot as plt


def load_latencies_ns(path: str) -> List[int]:
    latencies: List[int] = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                rtt_ns = int(row["rtt_ns"])
            except (KeyError, ValueError):
                continue
            # Skip messages that never got a proper response (rtt may be near-zero)
            if rtt_ns > 0:
                latencies.append(rtt_ns)
    return latencies


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot latency histogram and CDF from soak benchmark output.")
    parser.add_argument(
        "--input",
        type=str,
        default="soak_results.csv",
        help="Input CSV file produced by soak_benchmark.py (default: soak_results.csv)",
    )

    args = parser.parse_args()
    latencies_ns = load_latencies_ns(args.input)
    if not latencies_ns:
        print("No latency data found in input file.")
        return

    # Convert to microseconds for plotting
    latencies_us = [x / 1e3 for x in latencies_ns]
    latencies_us.sort()

    # Histogram
    plt.figure(figsize=(10, 4))
    plt.subplot(1, 2, 1)
    plt.hist(latencies_us, bins=50, color="steelblue", alpha=0.8)
    plt.xlabel("RTT (µs)")
    plt.ylabel("Count")
    plt.title("Latency histogram")

    # Empirical CDF
    plt.subplot(1, 2, 2)
    n = len(latencies_us)
    xs = latencies_us
    ys = [i / (n - 1) for i in range(n)] if n > 1 else [1.0]
    plt.plot(xs, ys, color="darkorange")
    plt.xlabel("RTT (µs)")
    plt.ylabel("CDF")
    plt.title("Latency CDF")

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()


