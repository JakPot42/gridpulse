"""Deterministic grid stress score computation — no AI, no external calls."""
from dataclasses import dataclass
from config import STRESS_TIERS, REGIONS, FUEL_FIRM


@dataclass
class RegionSnapshot:
    region: str
    hour: str
    demand_mwh: float
    solar_mwh: float
    wind_mwh: float
    firm_mwh: float
    firm_capacity_mw: float
    temp_f: float | None
    wind_speed_mph: float | None
    cloud_cover_pct: float | None
    stress_score: float
    tier: str
    net_load_mwh: float
    renewable_pct: float


def score_to_tier(score: float) -> str:
    for tier, (lo, hi) in STRESS_TIERS.items():
        if lo <= score < hi:
            return tier
    return "CRITICAL"


def compute_stress(
    demand_mwh: float,
    solar_mwh: float,
    wind_mwh: float,
    firm_capacity_mw: float,
) -> tuple[float, float]:
    """
    Returns (score [0,100], net_load_mwh).

    score = clamp((net_load / firm_capacity - 0.6) / 0.4 * 100, 0, 100)
    score 0   -> firm capacity at 60% utilization (comfortable reserve)
    score 100 -> firm capacity at 100%+ utilization (crisis)
    """
    net_load = max(0.0, demand_mwh - solar_mwh - wind_mwh)
    if firm_capacity_mw <= 0:
        return 100.0, net_load
    ratio = net_load / firm_capacity_mw
    raw = (ratio - 0.6) / 0.4 * 100.0
    score = max(0.0, min(100.0, raw))
    return score, net_load


def build_snapshot(
    region: str,
    hour: str,
    demand_mwh: float,
    solar_mwh: float,
    wind_mwh: float,
    firm_mwh: float,
    temp_f: float | None = None,
    wind_speed_mph: float | None = None,
    cloud_cover_pct: float | None = None,
) -> RegionSnapshot:
    firm_capacity_mw = REGIONS[region]["firm_gw"] * 1000.0
    score, net_load = compute_stress(demand_mwh, solar_mwh, wind_mwh, firm_capacity_mw)
    tier = score_to_tier(score)
    renewable_pct = (solar_mwh + wind_mwh) / max(1.0, demand_mwh) * 100.0
    return RegionSnapshot(
        region=region,
        hour=hour,
        demand_mwh=demand_mwh,
        solar_mwh=solar_mwh,
        wind_mwh=wind_mwh,
        firm_mwh=firm_mwh,
        firm_capacity_mw=firm_capacity_mw,
        temp_f=temp_f,
        wind_speed_mph=wind_speed_mph,
        cloud_cover_pct=cloud_cover_pct,
        stress_score=score,
        tier=tier,
        net_load_mwh=net_load,
        renewable_pct=renewable_pct,
    )
