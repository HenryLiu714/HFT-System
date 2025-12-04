"""
Unified runner for the HFT C++ system test exchange.

This script:
- Runs the functional, fuzz, and latency-profile tests (without pytest)
- Runs a high-volume soak benchmark
- Runs a powers-of-two rate sweep (2**n messages/sec)
- Prints human-readable summaries
- Automatically plots latency histograms + CDFs for the sweep CSVs

Usage (from project root, with the C++ HFT system already running and
CLIENT_IN_PORT / EXCHANGE_IN_PORT set in the environment):

    python test-exchnage_2/run.py

You can tweak some parameters via CLI flags; run with -h for details:

    python test-exchnage_2/run.py -h
"""

from __future__ import annotations

import argparse
import sys
import csv
import random
import statistics
import time
from typing import Any, Dict, List, Tuple

import matplotlib.pyplot as plt

from client import UdpClient
from fix_utils import gen_new_order, parse_fix


# ---------------------------------------------------------------------------
# Helpers to invoke existing pytest-style tests without pytest
# ---------------------------------------------------------------------------


def run_functional_tests(client: UdpClient) -> bool:
    """Run the functional order-flow tests and report pass/fail."""
    import test_functional_order_flow as t_func

    print("\n=== Functional tests ===")
    all_ok = True

    try:
        t_func.test_order_acknowledgment(client)
        print("[PASS] test_order_acknowledgment")
    except AssertionError as exc:
        all_ok = False
        print(f"[FAIL] test_order_acknowledgment: {exc}")

    return all_ok


def run_fuzz_tests(client: UdpClient) -> bool:
    """Run the fuzz / robustness tests and report pass/fail."""
    import test_fuzz_parser_robustness as t_fuzz

    print("\n=== Fuzz / robustness tests ===")
    all_ok = True

    for name in [
        "test_half_message",
        "test_tag_injection_large_tag_number",
        "test_empty_value_field",
    ]:
        fn = getattr(t_fuzz, name)
        try:
            fn(client)
            print(f"[PASS] {name}")
        except AssertionError as exc:
            all_ok = False
            print(f"[FAIL] {name}: {exc}")

    return all_ok


def run_latency_smoke_test(client: UdpClient) -> bool:
    """
    Run the latency profiling smoke test.

    This reuses the pytest-style test function so that latency stats are
    printed in the same format to stdout.
    """
    import test_latency_profile as t_latency

    print("\n=== Latency profile (smoke) ===")
    try:
        t_latency.test_latency_profile_smoke(client)
        print("[PASS] test_latency_profile_smoke")
        return True
    except AssertionError as exc:
        print(f"[FAIL] test_latency_profile_smoke: {exc}")
        return False


# ---------------------------------------------------------------------------
# Soak benchmark (adapted from soak_benchmark.py so we can call it directly)
# ---------------------------------------------------------------------------


def run_soak(
    num_messages: int,
    output_path: str,
    symbol: str,
    base_price: float,
    rate: float | None,
) -> Dict[str, Any] | None:
    """
    High-volume UDP soak benchmark for the HFT system.

    Returns a stats dict (same keys as soak_benchmark.run_soak) or None if
    no responses were received.
    """
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

    if not latencies_ns:
        print(
            f"No responses received during soak run (output={output_path}). "
            "Check that the HFT system is running and ports are correct."
        )
        return None

    latencies_ns.sort()
    count = len(latencies_ns)
    p50 = _percentile(latencies_ns, 50)
    p99 = _percentile(latencies_ns, 99)
    jitter = statistics.pstdev(latencies_ns) if count > 1 else 0.0
    effective_rate = count / total_wall if total_wall > 0 else 0.0

    print(
        f"\nSoak benchmark ({output_path}):\n"
        f"  Responses collected: {count}\n"
        f"  min={latencies_ns[0]/1e3:.1f} µs, "
        f"p50={p50/1e3:.1f} µs, "
        f"p99={p99/1e3:.1f} µs, "
        f"max={latencies_ns[-1]/1e3:.1f} µs, "
        f"jitter(stddev)={jitter/1e3:.1f} µs\n"
        f"  Effective throughput ≈ {effective_rate:.1f} msg/s\n"
        f"  Results written to {output_path}"
    )

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


def _percentile(sorted_values: List[int], pct: float) -> float:
    """Simple percentile helper: pct in [0, 100]."""
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


# ---------------------------------------------------------------------------
# Firehose benchmark (send without per-message wait)
# ---------------------------------------------------------------------------


def _firehose_run_once(
    num_messages: int,
    symbol: str,
    base_price: float,
    rate: float,
    receive_window_s: float = 2.0,
) -> Dict[str, Any]:
    """
    Send many messages without waiting for each individual response.

    - Phase 1: send num_messages at the target rate using client.send()
    - Phase 2: for a fixed window, keep calling receive() to count replies

    This is meant to stress throughput / capacity, not measure exact RTTs.
    """
    import time

    client = UdpClient()
    start_wall = time.perf_counter()

    interval: float | None = None
    if rate > 0:
        interval = 1.0 / rate

    # Phase 1: firehose send
    for _ in range(num_messages):
        loop_start = time.perf_counter()

        price = round(base_price + random.uniform(-1.0, 1.0), 2)
        qty = random.randint(1, 500)
        msg = gen_new_order(symbol=symbol, price=price, qty=qty)
        client.send(msg)

        if interval is not None:
            elapsed = time.perf_counter() - loop_start
            remaining = interval - elapsed
            if remaining > 0:
                time.sleep(remaining)

    # Phase 2: receive for a fixed window
    responses = 0
    recv_start = time.perf_counter()
    while time.perf_counter() - recv_start < receive_window_s:
        resp = client.receive()
        if resp is not None:
            responses += 1

    total_wall = time.perf_counter() - start_wall
    client.close()

    effective_rate = responses / total_wall if total_wall > 0 else 0.0
    return {
        "requested_rate": rate,
        "effective_rate": effective_rate,
        "sent": num_messages,
        "responses": responses,
        "receive_window_s": receive_window_s,
        "total_wall_s": total_wall,
    }


def run_firehose_sweep(
    messages: int,
    symbol: str,
    base_price: float,
    min_exp: int,
    max_exp: int,
    exp_step: int,
) -> List[Dict[str, Any]]:
    """
    Sweep powers-of-two offered load using the firehose benchmark.

    For each 2**exp:
    - Blast 'messages' requests without per-message waiting
    - Measure how many responses came back in a fixed window
    - Record requested vs effective throughput
    """
    print(
        "\n=== Firehose throughput sweep (no per-message RTT wait) ===\n"
        f"Messages per rate point: {messages}, exponents: {min_exp}..{max_exp} "
        f"(step {exp_step})"
    )

    results: List[Dict[str, Any]] = []

    for exp in range(min_exp, max_exp + 1, max(1, exp_step)):
        # Use an integer rate to avoid float overflow at very large exponents.
        # For extremely large exponents this number is not physically meaningful
        # but it still serves as a label for the sweep.
        requested_rate = 2**exp
        print(f"\n--- Firehose rate 2**{exp} ---")

        stats = _firehose_run_once(
            num_messages=messages,
            symbol=symbol,
            base_price=base_price,
            rate=float(requested_rate),
        )
        stats["exp"] = exp
        results.append(stats)

        print(
            f"requested_rate≈2**{exp}, sent={stats['sent']}, "
            f"responses={stats['responses']}, "
            f"effective_rate≈{stats['effective_rate']:.1f} msg/s"
        )

    if results:
        print("\nFirehose sweep complete. Collected points:")
        for r in results:
            print(
                f"  2**{r['exp']}: requested≈2**{r['exp']}, "
                f"effective_rate≈{r['effective_rate']:.1f} msg/s, "
                f"responses={r['responses']}/{r['sent']}"
            )
    else:
        print("\nFirehose sweep produced no data.")

    # Plotting is handled by the caller (e.g. in main) so that we can combine
    # multiple graphs into a single figure at the end.
    return results

# ---------------------------------------------------------------------------
# Powers-of-two rate sweep and plotting
# ---------------------------------------------------------------------------


def run_power_of_two_sweep(
    messages: int,
    symbol: str,
    base_price: float,
    min_exp: int,
    max_exp: int,
    exp_step: int,
    p99_threshold: float,
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Sweep powers-of-two send rates and stop when p99 latency degrades.

    Returns (stats_list, csv_paths).
    """
    print(
        "\n=== Powers-of-two rate sweep ===\n"
        f"Messages per rate point: {messages}, exponents: {min_exp}..{max_exp} "
        f"(step {exp_step}), p99 threshold factor: {p99_threshold}"
    )

    results: List[Dict[str, Any]] = []
    csv_paths: List[str] = []
    prev_p99: float | None = None

    for exp in range(min_exp, max_exp + 1, max(1, exp_step)):
        requested_rate = float(2**exp)
        # Use exponent-based filenames to avoid extremely long paths when exp is large.
        output_path = f"soak_2pow{exp}.csv"
        print(f"\n--- Rate 2**{exp} = {requested_rate:.0f} msg/s ---")

        stats = run_soak(
            num_messages=messages,
            output_path=output_path,
            symbol=symbol,
            base_price=base_price,
            rate=requested_rate,
        )
        if not stats:
            print("No stats returned; stopping sweep.")
            break

        # Annotate stats with the exponent so legend labels can be 2^n instead
        # of the full numeric rate (which can be very large).
        stats["exp"] = exp
        results.append(stats)
        csv_paths.append(output_path)

        p99 = stats["p99"]
        eff_rate = stats["effective_rate"]
        print(f"Summary: effective_rate={eff_rate:.1f} msg/s, p99={p99/1e3:.1f} µs")

        if prev_p99 is not None and p99 > prev_p99 * p99_threshold:
            print(
                "p99 increased beyond threshold factor "
                f"{p99_threshold:.2f} "
                f"(prev {prev_p99/1e3:.1f} µs -> now {p99/1e3:.1f} µs). Stopping sweep."
            )
            break

        prev_p99 = p99

    if results:
        print("\nSweep complete. Collected points:")
        for r in results:
            print(
                f"  requested={r['requested_rate']:.0f} msg/s, "
                f"effective={r['effective_rate']:.1f} msg/s, "
                f"p50={r['p50']/1e3:.1f} µs, p99={r['p99']/1e3:.1f} µs, "
                f"max={r['max']/1e3:.1f} µs"
            )
    else:
        print("\nSweep produced no valid data.")

    return results, csv_paths


def plot_combined_latency_hist_and_cdf(
    csv_paths: List[str], sweep_results: List[Dict[str, Any]]
) -> None:
    """
    Plot a combined histogram and CDF overlay for all sweep CSVs.

    Left subplot: overlapping histograms (one per rate).
    Right subplot: overlapping CDF curves (one per rate).
    """
    series_latencies_us: List[Tuple[str, List[float]]] = []

    for stats, path in zip(sweep_results, csv_paths):
        latencies_ns: List[int] = []
        with open(path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    rtt_ns = int(row["rtt_ns"])
                except (KeyError, ValueError):
                    continue
                if rtt_ns > 0:
                    latencies_ns.append(rtt_ns)

        if not latencies_ns:
            print(f"No latency data found in {path}; skipping in combined plot.")
            continue

        latencies_us = [x / 1e3 for x in latencies_ns]
        latencies_us.sort()

        # Prefer labeling by exponent (2^n) for clarity when rates are huge.
        exp = stats.get("exp")
        if exp is not None:
            label = f"2^{exp}"
        else:
            rate = stats.get("requested_rate", 0.0) or 0.0
            label = f"{rate:.0f} msg/s"
        series_latencies_us.append((label, latencies_us))

    if not series_latencies_us:
        print("No latency data found in any sweep CSVs; skipping combined plot.")
        return

    plt.figure(figsize=(10, 4))

    # Histogram overlay
    plt.subplot(1, 2, 1)
    for label, latencies_us in series_latencies_us:
        plt.hist(latencies_us, bins=50, alpha=0.4, label=label)
    plt.xlabel("RTT (µs)")
    plt.ylabel("Count")
    plt.title("Latency histogram (all rates)")
    plt.legend()

    # CDF overlay
    plt.subplot(1, 2, 2)
    for label, latencies_us in series_latencies_us:
        n = len(latencies_us)
        xs = latencies_us
        ys = [i / (n - 1) for i in range(n)] if n > 1 else [1.0]
        plt.plot(xs, ys, label=label)
    plt.xlabel("RTT (µs)")
    plt.ylabel("CDF")
    plt.title("Latency CDF (all rates)")
    plt.legend()

    plt.tight_layout()
    plt.show()


def plot_summary_three_panel(
    csv_paths: List[str],
    sweep_results: List[Dict[str, Any]],
    firehose_results: List[Dict[str, Any]],
) -> None:
    """
    Draw a single figure with three panels:
    - Left: latency histogram overlay (RTT-based sweep)
    - Middle: latency CDF overlay (RTT-based sweep)
    - Right: firehose effective throughput vs exponent (2**n)
    """
    if not sweep_results or not csv_paths or not firehose_results:
        print("Not enough data to build three-panel summary figure.")
        return

    fig, (ax_hist, ax_cdf, ax_fire) = plt.subplots(1, 3, figsize=(15, 4))

    # Build latency series from CSVs (same logic as combined plot).
    series_latencies_us: List[Tuple[str, List[float]]] = []
    for stats, path in zip(sweep_results, csv_paths):
        latencies_ns: List[int] = []
        with open(path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    rtt_ns = int(row["rtt_ns"])
                except (KeyError, ValueError):
                    continue
                if rtt_ns > 0:
                    latencies_ns.append(rtt_ns)
        if not latencies_ns:
            continue

        latencies_us = [x / 1e3 for x in latencies_ns]
        latencies_us.sort()
        exp = stats.get("exp")
        label = f"2^{exp}" if exp is not None else f"{stats.get('requested_rate', 0.0):.0f} msg/s"
        series_latencies_us.append((label, latencies_us))

    if not series_latencies_us:
        print("No latency data found for summary figure.")
        return

    # Left: histogram overlay
    for label, latencies_us in series_latencies_us:
        ax_hist.hist(latencies_us, bins=50, alpha=0.4, label=label)
    ax_hist.set_xlabel("RTT (µs)")
    ax_hist.set_ylabel("Count")
    ax_hist.set_title("Latency histogram (all rates)")
    ax_hist.legend(fontsize="small")

    # Middle: CDF overlay
    for label, latencies_us in series_latencies_us:
        n = len(latencies_us)
        xs = latencies_us
        ys = [i / (n - 1) for i in range(n)] if n > 1 else [1.0]
        ax_cdf.plot(xs, ys, label=label)
    ax_cdf.set_xlabel("RTT (µs)")
    ax_cdf.set_ylabel("CDF")
    ax_cdf.set_title("Latency CDF (all rates)")
    ax_cdf.legend(fontsize="small")

    # Right: firehose throughput vs exponent
    try:
        exps = [r["exp"] for r in firehose_results]
        eff = [r["effective_rate"] for r in firehose_results]
        ax_fire.plot(exps, eff, marker="o")
        ax_fire.set_xlabel("Exponent n (rate ≈ 2**n msg/s)")
        ax_fire.set_ylabel("Effective throughput (msg/s)")
        ax_fire.set_title("Firehose: throughput vs 2**n")
        ax_fire.grid(True, linestyle="--", alpha=0.3)
    except Exception:
        ax_fire.text(0.5, 0.5, "Firehose plot failed", ha="center", va="center")

    fig.tight_layout()
    plt.show()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Unified functional/fuzz/latency/volume runner for the HFT test exchange."
    )
    parser.add_argument(
        "--symbol",
        type=str,
        default="AAPL",
        help="Symbol to use for generated orders (default: AAPL)",
    )
    parser.add_argument(
        "--base-price",
        type=float,
        default=150.0,
        help="Base price around which to jitter orders (default: 150.0)",
    )
    parser.add_argument(
        "--soak-messages",
        type=int,
        default=10000,
        help="Number of messages for the standalone soak benchmark (default: 10000)",
    )
    parser.add_argument(
        "--sweep-messages",
        type=int,
        default=5000,
        help="Messages per rate point in the powers-of-two sweep (default: 5000)",
    )
    parser.add_argument(
        "--sweep-min-exp",
        type=int,
        default=12,
        help="Minimum exponent for 2**exp in the rate sweep (default: 12)",
    )
    parser.add_argument(
        "--sweep-max-exp",
        type=int,
        default=30,
        help="Maximum exponent for 2**exp in the rate sweep (default: 50)",
    )
    parser.add_argument(
        "--sweep-exp-step",
        type=int,
        default=2,
        help="Step between exponents in the rate sweep, e.g. 2 -> 12,14,16... (default: 1)",
    )
    parser.add_argument(
        "--sweep-p99-threshold",
        type=float,
        default=3,
        help="Stop sweep when p99 grows by this factor vs previous step (default: 1.8)",
    )
    parser.add_argument(
        "--firehose-sweep",
        action="store_true",
        help="Also run a high-volume 'firehose' sweep that does not wait for each response.",
    )
    parser.add_argument(
        "--firehose-messages",
        type=int,
        default=20000,
        help="Messages per rate point in the firehose sweep (default: 20000)",
    )
    parser.add_argument(
        "--no-plots",
        action="store_true",
        help="If set, skip plotting latency histograms/CDFs for the sweep CSVs.",
    )

    args = parser.parse_args()

    # If run without any CLI flags (just `python test-exchnage_2/run.py`),
    # automatically use the "volume" preset that you'd otherwise specify via:
    #   --sweep-min-exp 12 --sweep-max-exp 30 --sweep-exp-step 2
    #   --firehose-sweep --firehose-messages 20000
    if len(sys.argv) == 1:
        args.sweep_min_exp = 12
        args.sweep_max_exp = 30
        args.sweep_exp_step = 2
        args.firehose_sweep = True
        args.firehose_messages = 20000

    print("Starting unified HFT system test-exchange run.")
    print("Assuming the C++ HFT system is already running and UDP ports are configured via env vars.\n")

    # 1) Functional + fuzz + latency tests using a shared client.
    client = UdpClient()
    try:
        ok_functional = run_functional_tests(client)
        ok_fuzz = run_fuzz_tests(client)
        ok_latency = run_latency_smoke_test(client)
    finally:
        client.close()

    print(
        "\n=== Summary: pytest-style tests ===\n"
        f"Functional tests: {'PASS' if ok_functional else 'FAIL'}\n"
        f"Fuzz tests:       {'PASS' if ok_fuzz else 'FAIL'}\n"
        f"Latency smoke:    {'PASS' if ok_latency else 'FAIL'}"
    )

    # 2) Standalone high-volume soak at "unlimited" rate (as fast as possible).
    soak_output = "soak_results.csv"
    run_soak(
        num_messages=args.soak_messages,
        output_path=soak_output,
        symbol=args.symbol,
        base_price=args.base_price,
        rate=None,
    )

    # 3) Powers-of-two rate sweep + latency/RTT plots.
    sweep_results, csv_paths = run_power_of_two_sweep(
        messages=args.sweep_messages,
        symbol=args.symbol,
        base_price=args.base_price,
        min_exp=args.sweep_min_exp,
        max_exp=args.sweep_max_exp,
        exp_step=args.sweep_exp_step,
        p99_threshold=args.sweep_p99_threshold,
    )

    firehose_results: List[Dict[str, Any]] | None = None

    # 4) Optional: additional firehose throughput sweep (no per-message RTT).
    if args.firehose_sweep:
        firehose_results = run_firehose_sweep(
            messages=args.firehose_messages,
            symbol=args.symbol,
            base_price=args.base_price,
            min_exp=args.sweep_min_exp,
            max_exp=args.sweep_max_exp,
            exp_step=args.sweep_exp_step,
        )

    # 5) Plots at the very end.
    if not args.no_plots and csv_paths:
        if firehose_results:
            print("Generating three-panel summary figure (latency + firehose)...")
            plot_summary_three_panel(csv_paths, sweep_results, firehose_results)

    print("\nUnified run complete.")


if __name__ == "__main__":
    main()


