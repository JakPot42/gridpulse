"""What-if scenario modifiers — deterministic pct adjustments to demand/solar/wind."""
from dataclasses import dataclass
from stress_engine import RegionSnapshot, build_snapshot
from config import SCENARIO_DEFAULTS


@dataclass
class ScenarioResult:
    scenario: str
    base: RegionSnapshot
    modified: RegionSnapshot
    delta_score: float
    delta_tier: bool


def apply_scenario(
    snap: RegionSnapshot,
    *,
    demand_pct: float = 0.0,
    wind_pct: float = 0.0,
    solar_pct: float = 0.0,
) -> RegionSnapshot:
    """
    Apply percentage adjustments (e.g. wind_pct=-20 means 20% wind drop).
    All modifiers are additive in pct space: value * (1 + pct/100).
    """
    new_demand = max(0.0, snap.demand_mwh * (1.0 + demand_pct / 100.0))
    new_solar = max(0.0, snap.solar_mwh * (1.0 + solar_pct / 100.0))
    new_wind = max(0.0, snap.wind_mwh * (1.0 + wind_pct / 100.0))
    return build_snapshot(
        region=snap.region,
        hour=snap.hour,
        demand_mwh=new_demand,
        solar_mwh=new_solar,
        wind_mwh=new_wind,
        firm_mwh=snap.firm_mwh,
        temp_f=snap.temp_f,
        wind_speed_mph=snap.wind_speed_mph,
        cloud_cover_pct=snap.cloud_cover_pct,
    )


def run_scenario(
    snap: RegionSnapshot,
    name: str,
    *,
    demand_pct: float = 0.0,
    wind_pct: float = 0.0,
    solar_pct: float = 0.0,
) -> ScenarioResult:
    modified = apply_scenario(snap, demand_pct=demand_pct, wind_pct=wind_pct, solar_pct=solar_pct)
    return ScenarioResult(
        scenario=name,
        base=snap,
        modified=modified,
        delta_score=modified.stress_score - snap.stress_score,
        delta_tier=(modified.tier != snap.tier),
    )


def run_named_scenario(snap: RegionSnapshot, scenario_name: str) -> ScenarioResult:
    """Run a scenario from SCENARIO_DEFAULTS by name."""
    if scenario_name not in SCENARIO_DEFAULTS:
        raise ValueError(f"Unknown scenario '{scenario_name}'. Valid: {sorted(SCENARIO_DEFAULTS)}")
    params = SCENARIO_DEFAULTS[scenario_name]
    return run_scenario(snap, scenario_name, **params)


def to_joule_format(snapshots: list[RegionSnapshot]) -> dict:
    """
    Export stress index for P20 joule SMR suitability screener.

    Joule uses grid stress as one factor when scoring DoD installation suitability
    for small modular reactor deployment: a region in HIGH/CRITICAL stress has
    higher SMR value as a resilience asset because it cannot absorb additional
    demand loss from grid disruption.
    """
    return {
        snap.region: {
            "stress_score": round(snap.stress_score, 1),
            "tier": snap.tier,
            "net_load_mwh": round(snap.net_load_mwh, 0),
            "firm_capacity_mw": snap.firm_capacity_mw,
            "demand_mwh": round(snap.demand_mwh, 0),
            "renewable_pct": round(snap.renewable_pct, 1),
            "hour": snap.hour,
        }
        for snap in snapshots
    }
