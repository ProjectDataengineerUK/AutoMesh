"""Fixture-to-workspace reconciliation."""

from __future__ import annotations


def reconcile(expected: dict[str, float], actual: dict[str, float], tolerance: float = 0.0) -> list[dict[str, object]]:
    results = []
    for metric, expected_value in expected.items():
        observed = actual.get(metric)
        delta = None if observed is None else observed - expected_value
        passed = observed is not None and abs(delta) <= tolerance
        results.append(
            {
                "metric": metric,
                "expected": expected_value,
                "actual": observed,
                "delta": delta,
                "status": "PASS" if passed else "FAIL",
            }
        )
    return results
