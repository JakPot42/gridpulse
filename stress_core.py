"""
stress_core.py — the canonical stress-tier scale shared by the grid and
water stress-index engines (Phase 6, Cluster 5).

Both GridPulse's stress_engine.py and Water Security Stress Monitor's
stress_engine.py independently defined the identical STRESS_TIERS dict
(LOW [0,25) / ELEVATED [25,50) / HIGH [50,75) / CRITICAL [75,100.1)) and a
byte-identical score_to_tier() function -- Water Monitor was explicitly
built as "the GridPulse pattern applied to water," and the tier scale is
exactly where that shared lineage shows in the real code. Canonicalized
here once; each tool's own domain formula (grid: net-load/firm-capacity
ratio; water: 0.5*supply_stress + 0.5*USDM-weighted-drought-index) stays
in its own engine, unchanged -- only the shared tier scale moved.

Deliberately NOT a shared "region" concept: GridPulse's "CAL" (an EIA
electricity balancing region) and Water Monitor's "CAL" (a water/drought
region) share a key but not a referent -- see each tool's own config.py
for its own REGIONS roster.
"""
from __future__ import annotations

STRESS_TIERS: dict[str, tuple[float, float]] = {
    "LOW":      (0.0,  25.0),
    "ELEVATED": (25.0, 50.0),
    "HIGH":     (50.0, 75.0),
    "CRITICAL": (75.0, 100.1),  # upper bound open
}


def score_to_tier(score: float) -> str:
    """Map a 0-100 stress score to its tier label."""
    for tier, (lo, hi) in STRESS_TIERS.items():
        if lo <= score < hi:
            return tier
    return "CRITICAL"
