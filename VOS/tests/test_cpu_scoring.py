"""
Regression tests for CPU performance scoring (modules/specs.py).

Guards against the class of bug where a genuinely capable real-world CPU is
wrongly scored below CPU_PERF_SCORE_MIN and shown as "Not Approved" on the
dashboard (originally reported: AMD Ryzen 5 2600 scored 64 -> Not Approved).

Scoring scale: Intel i5 6th-gen (i5-6500) == 100. A CPU is "Approved" when
its score >= CPU_PERF_SCORE_MIN. These tests assert the APPROVAL VERDICT for
a broad set of real CPU model strings (the exact score may drift; the verdict
must not).

Run:  python -m pytest tests/test_cpu_scoring.py -v
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules.specs import get_cpu_performance  # noqa: E402
from thresholds import CPU_PERF_SCORE_MIN  # noqa: E402


def verdict(model: str) -> str:
    score, _ = get_cpu_performance(model)
    return "Approved" if score >= CPU_PERF_SCORE_MIN else "Not Approved"


# Capable, real-world CPUs that MUST be Approved. A failure here is the exact
# bug this suite exists to prevent.
MUST_APPROVE = [
    # --- the originally reported regression ---
    "AMD Ryzen 5 2600 Six-Core Processor",
    # --- AMD Ryzen desktop (Zen / Zen+ / Zen2 / Zen3 / Zen4) ---
    "AMD Ryzen 3 1200 Quad-Core Processor",
    "AMD Ryzen 5 1600 Six-Core Processor",
    "AMD Ryzen 7 1700 Eight-Core Processor",
    "AMD Ryzen 3 2200G with Radeon Vega Graphics",
    "AMD Ryzen 5 2600X Six-Core Processor",
    "AMD Ryzen 7 2700 Eight-Core Processor",
    "AMD Ryzen 7 2700X Eight-Core Processor",
    "AMD Ryzen 3 3200G with Radeon Vega Graphics",
    "AMD Ryzen 5 3400G with Radeon Vega Graphics",
    "AMD Ryzen 5 3600 6-Core Processor",
    "AMD Ryzen 7 3700X 8-Core Processor",
    "AMD Ryzen 9 3900X 12-Core Processor",
    "AMD Ryzen 5 5500 6-Core Processor",
    "AMD Ryzen 5 5600 6-Core Processor",
    "AMD Ryzen 5 5600X 6-Core Processor",
    "AMD Ryzen 7 5800X 8-Core Processor",
    "AMD Ryzen 9 5900X 12-Core Processor",
    "AMD Ryzen 9 5950X 16-Core Processor",
    "AMD Ryzen 5 7600 6-Core Processor",
    "AMD Ryzen 7 7700X 8-Core Processor",
    "AMD Ryzen 9 7950X 16-Core Processor",
    # --- AMD Ryzen mobile / APU ---
    "AMD Ryzen 5 4500U with Radeon Graphics",
    "AMD Ryzen 5 4600G with Radeon Graphics",
    "AMD Ryzen 5 5500U with Radeon Graphics",
    "AMD Ryzen 7 5700U with Radeon Graphics",
    "AMD Ryzen 5 5625U with Radeon Graphics",
    "AMD Ryzen 7 6800H with Radeon Graphics",
    # --- Intel Core i-series ---
    "Intel Core i5-6500 @ 3.20GHz",
    "Intel Core i7-6700 @ 3.40GHz",
    "Intel Core i5-7500 @ 3.40GHz",
    "Intel Core i3-8100 @ 3.60GHz",
    "Intel Core i5-8400 @ 2.80GHz",
    "Intel Core i7-8700 @ 3.20GHz",
    "Intel Core i3-10100 @ 3.60GHz",
    "Intel Core i5-10400 @ 2.90GHz",
    "Intel Core i7-10700 @ 2.90GHz",
    "Intel Core i3-12100 @ 3.30GHz",
    "Intel Core i5-12400 @ 2.50GHz",
    "Intel Core i7-12700 @ 2.10GHz",
    "Intel Core i5-13400",
    "Intel Core i9-13900K",
    "12th Gen Intel Core i5-1235U",
    # --- modern capable budget (policy: approve) ---
    "Intel N100",
    "Intel Pentium Gold G6400 @ 4.00GHz",
    # --- Intel Xeon workstations ---
    "Intel Xeon E3-1240 v5 @ 3.50GHz",
    "Intel Xeon E5-2680 v4 @ 2.40GHz",
    "Intel Xeon E5-2620 v3 @ 2.40GHz",
    # --- Apple Silicon / Snapdragon ---
    "Apple M1",
    "Apple M2",
    "Snapdragon X Elite",
]

# Genuinely weak or (by policy) old silicon that MUST stay Not Approved.
# Guards the opposite failure: weak chips slipping through as Approved.
MUST_NOT_APPROVE = [
    "Intel Celeron G3900 @ 2.80GHz",
    "Intel Celeron N4020 @ 1.10GHz",
    "Intel Celeron J4125",
    "Intel Atom x5-Z8350",
    "Intel Pentium Silver N5000",
    "AMD A8-7600 Radeon R7",
    "AMD A10-9700 RADEON R7",
    "AMD A6-3650 APU",
    "AMD Phenom II X4 965",
    # policy: old/weak, intentionally rejected
    "Intel Core i3-6100 @ 3.70GHz",
    "Intel Pentium G4560 @ 3.50GHz",
    "AMD FX-6300 Six-Core Processor",
    "AMD FX-8350 Eight-Core Processor",
    "AMD Athlon 3000G with Radeon Vega Graphics",
]


@pytest.mark.parametrize("model", MUST_APPROVE)
def test_capable_cpu_is_approved(model):
    score, _ = get_cpu_performance(model)
    assert score >= CPU_PERF_SCORE_MIN, (
        f"{model!r} scored {score} (< {CPU_PERF_SCORE_MIN}) -> wrongly Not Approved"
    )


@pytest.mark.parametrize("model", MUST_NOT_APPROVE)
def test_weak_cpu_is_not_approved(model):
    score, _ = get_cpu_performance(model)
    assert score < CPU_PERF_SCORE_MIN, (
        f"{model!r} scored {score} (>= {CPU_PERF_SCORE_MIN}) -> wrongly Approved"
    )


def test_reported_regression_ryzen_5_2600():
    """The exact case that was reported as wrongly 'Not Approved'."""
    score, label = get_cpu_performance("AMD Ryzen 5 2600 Six-Core Processor")
    assert score >= CPU_PERF_SCORE_MIN, f"Ryzen 5 2600 regressed: score={score} label={label!r}"
