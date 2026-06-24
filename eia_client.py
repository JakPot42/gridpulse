"""EIA API v2 client — electricity demand and generation mix by region."""
import requests
from config import EIA_API_KEY, EIA_BASE, DEMO_MODE, FUEL_ALL


def _get(endpoint: str, params: dict) -> dict:
    params = dict(params)
    params["api_key"] = EIA_API_KEY
    resp = requests.get(f"{EIA_BASE}{endpoint}", params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def fetch_demand(region: str, hours: int = 24) -> list[dict]:
    """
    Returns list of {period, respondent, type, value} dicts for hourly demand.
    value is in MWh. period format: 'YYYY-MM-DDTHH'.
    """
    if DEMO_MODE:
        from seed_data import DEMO_DEMAND
        return DEMO_DEMAND.get(region, [])[:hours]
    data = _get("/electricity/rto/region-data/data/", {
        "frequency": "hourly",
        "data[0]": "value",
        "facets[respondent][]": region,
        "facets[type][]": "D",
        "sort[0][column]": "period",
        "sort[0][direction]": "asc",
        "length": hours,
    })
    return data.get("response", {}).get("data", [])


def fetch_generation_mix(region: str, hours: int = 24) -> list[dict]:
    """
    Returns list of {period, respondent, fueltype, value} dicts.
    One row per fuel type per hour. value is in MWh.
    """
    if DEMO_MODE:
        from seed_data import DEMO_GENERATION
        all_rows = DEMO_GENERATION.get(region, [])
        # Return rows covering up to `hours` distinct periods
        seen_periods: set[str] = set()
        result = []
        for row in all_rows:
            seen_periods.add(row["period"])
            if len(seen_periods) > hours:
                break
            result.append(row)
        return result
    n_fuel = len(FUEL_ALL)
    data = _get("/electricity/rto/fuel-type-data/data/", {
        "frequency": "hourly",
        "data[0]": "value",
        "facets[respondent][]": region,
        "sort[0][column]": "period",
        "sort[0][direction]": "asc",
        "length": hours * n_fuel,
    })
    return data.get("response", {}).get("data", [])
