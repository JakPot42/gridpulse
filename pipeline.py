"""Orchestrates EIA + NOAA data into RegionSnapshot objects."""
from config import REGIONS, FUEL_FIRM
from eia_client import fetch_demand, fetch_generation_mix
from noaa_client import fetch_hourly_forecast
from stress_engine import RegionSnapshot, build_snapshot


def build_snapshots(
    regions: list[str] | None = None,
    hours: int = 6,
) -> dict[str, list[RegionSnapshot]]:
    """
    Returns {region: [snapshots sorted chronologically]}.
    In DEMO_MODE all data comes from seed_data; otherwise calls EIA and NOAA APIs.
    """
    if regions is None:
        regions = list(REGIONS.keys())
    result: dict[str, list[RegionSnapshot]] = {}
    for region in regions:
        demand_data = fetch_demand(region, hours)
        gen_data = fetch_generation_mix(region, hours)
        lat = REGIONS[region]["lat"]
        lon = REGIONS[region]["lon"]
        weather_data = fetch_hourly_forecast(lat, lon, hours)
        result[region] = _merge(region, demand_data, gen_data, weather_data)
    return result


def _merge(
    region: str,
    demand_data: list[dict],
    gen_data: list[dict],
    weather_data: list[dict],
) -> list[RegionSnapshot]:
    demand_by_hour: dict[str, float] = {
        d["period"]: float(d["value"]) for d in demand_data
    }
    gen_by_hour: dict[str, dict[str, float]] = {}
    for g in gen_data:
        h = g["period"]
        gen_by_hour.setdefault(h, {})[g["fueltype"]] = float(g["value"])

    hours = sorted(set(demand_by_hour) & set(gen_by_hour))
    snaps: list[RegionSnapshot] = []
    for i, hour in enumerate(hours):
        demand = demand_by_hour[hour]
        gen = gen_by_hour[hour]
        solar = gen.get("SUN", 0.0)
        wind = gen.get("WND", 0.0)
        firm = sum(gen.get(f, 0.0) for f in FUEL_FIRM)
        weather = weather_data[i] if i < len(weather_data) else {}
        snap = build_snapshot(
            region=region,
            hour=hour,
            demand_mwh=demand,
            solar_mwh=solar,
            wind_mwh=wind,
            firm_mwh=firm,
            temp_f=weather.get("temp_f"),
            wind_speed_mph=weather.get("wind_mph"),
            cloud_cover_pct=weather.get("cloud_pct"),
        )
        snaps.append(snap)
    return snaps


def current_snapshot(snapshots: list[RegionSnapshot]) -> RegionSnapshot | None:
    """Return the first (oldest) snapshot from a region's list, representing current state."""
    return snapshots[0] if snapshots else None
