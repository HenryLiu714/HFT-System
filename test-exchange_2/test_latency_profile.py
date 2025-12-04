"""
Latency profiling tests.

These do not assert on specific timing thresholds (which are environment
dependent) but compute useful statistics: min, max, percentiles, and jitter.
"""

from statistics import mean, pstdev

from fix_utils import gen_new_order


def _percentile(sorted_values, pct: float) -> float:
    """
    Simple percentile helper: pct in [0, 100].
    """
    if not sorted_values:
        return 0.0
    k = (len(sorted_values) - 1) * pct / 100.0
    f = int(k)
    c = min(f + 1, len(sorted_values) - 1)
    if f == c:
        return sorted_values[f]
    d0 = sorted_values[f] * (c - k)
    d1 = sorted_values[c] * (k - f)
    return d0 + d1


def test_latency_profile_smoke(client):
    """
    Send a series of New Orders and collect round-trip latencies.

    The goal is to ensure:
    - We get responses for most messages
    - We can compute basic latency statistics without errors
    """
    latencies = []
    responses = 0
    attempts = 100

    for _ in range(attempts):
        msg = gen_new_order(symbol="AAPL", price=150.0)
        response, rtt = client.send_and_receive(msg)
        if response is not None:
            responses += 1
            latencies.append(rtt)

    # Basic sanity: we should get at least some responses
    assert responses > 0, "Did not receive any responses during latency profiling"

    latencies.sort()
    p50 = _percentile(latencies, 50)
    p99 = _percentile(latencies, 99)
    jitter = pstdev(latencies) if len(latencies) > 1 else 0.0

    # Expose metrics via pytest's reporting (stdout)
    print(
        f"\nLatency stats over {len(latencies)} responses: "
        f"min={latencies[0]*1e6:.1f}µs, "
        f"p50={p50*1e6:.1f}µs, "
        f"p99={p99*1e6:.1f}µs, "
        f"max={latencies[-1]*1e6:.1f}µs, "
        f"jitter(stddev)={jitter*1e6:.1f}µs"
    )


