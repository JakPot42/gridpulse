"""
Pre-seeded demo data — 6 EIA regions x 6 hours (2026-06-23 14:00-19:00 UTC).
All DEMO_MODE API clients return from these dicts; no real HTTP calls made.

Stress scores at hour 14 (base hour):
  CAL:  3.8  LOW      -- solar-heavy afternoon
  TEX: 64.8  HIGH     -- heat-driven demand, low wind
  MIDA: 35.5 ELEVATED -- moderate load, little renewable
  MIDW: 35.9 ELEVATED -- wind helping but demand high
  NE:  54.5  HIGH     -- small capacity region under load
  NY:  32.2  ELEVATED -- dense urban demand
"""

# ---------------------------------------------------------------------------
# EIA demand data  (matches /electricity/rto/region-data/data/ format)
# period format: "YYYY-MM-DDTHH"
# ---------------------------------------------------------------------------

def _demand_hours(region: str, base_values: list[float]) -> list[dict]:
    hours = [f"2026-06-23T{14 + i:02d}" for i in range(len(base_values))]
    return [
        {"period": h, "respondent": region, "type": "D", "value": v}
        for h, v in zip(hours, base_values)
    ]


DEMO_DEMAND: dict[str, list[dict]] = {
    "CAL":  _demand_hours("CAL",  [45000, 47000, 48500, 46000, 43000, 40000]),
    "TEX":  _demand_hours("TEX",  [68000, 70000, 71500, 69000, 66000, 62000]),
    "MIDA": _demand_hours("MIDA", [51000, 52500, 53000, 51000, 49000, 47000]),
    "MIDW": _demand_hours("MIDW", [68000, 69500, 70000, 68500, 66000, 63000]),
    "NE":   _demand_hours("NE",   [25000, 25800, 26200, 25500, 24500, 23500]),
    "NY":   _demand_hours("NY",   [30000, 31000, 31500, 30500, 29500, 28000]),
}

# ---------------------------------------------------------------------------
# EIA generation mix data  (matches /electricity/rto/fuel-type-data/data/ format)
# one entry per (period, fueltype)
# ---------------------------------------------------------------------------

# (solar_mwh, wind_mwh, ng_mwh, nuc_mwh, col_mwh) per hour per region
_GEN_BASE: dict[str, list[tuple]] = {
    # CAL: solar-heavy, winds moderate, very little coal
    "CAL": [
        (10000, 3000, 22000, 9800, 200),
        (10500, 2800, 23500, 9800, 200),
        (10000, 2600, 25500, 9800, 200),
        ( 8500, 2700, 24500, 9800, 200),
        ( 5500, 2800, 22500, 9800, 200),
        ( 2000, 3000, 19000, 9800, 200),
    ],
    # TEX: hot summer day, low wind, lots of gas
    "TEX": [
        ( 2000, 5000, 45000, 6000, 10000),
        ( 2200, 4500, 47000, 6000, 10000),
        ( 2000, 4200, 49000, 6000, 10000),
        ( 1800, 4000, 47000, 6000, 10000),
        ( 1000, 3800, 45000, 6000, 10000),
        (  300, 4000, 42000, 6000, 10000),
    ],
    # MIDA: mixed, modest solar/wind
    "MIDA": [
        ( 1500, 2000, 33000, 10000, 4500),
        ( 1700, 2000, 34500, 10000, 4500),
        ( 1600, 1800, 35000, 10000, 4500),
        ( 1200, 1900, 33500, 10000, 4500),
        (  700, 2100, 32000, 10000, 4500),
        (  200, 2200, 30000, 10000, 4500),
    ],
    # MIDW: good wind, coal still dominant
    "MIDW": [
        ( 1000, 9000, 25000, 12000, 21000),
        ( 1100, 8800, 26000, 12000, 21000),
        ( 1000, 8500, 27000, 12000, 21000),
        (  900, 8700, 26000, 12000, 21000),
        (  500, 9000, 24500, 12000, 21000),
        (  100, 9200, 23000, 12000, 21000),
    ],
    # NE: nuclear-heavy, small region, tight margins
    "NE": [
        (  300, 1800, 9000, 11500, 2500),
        (  400, 1750, 9500, 11500, 2500),
        (  350, 1700, 9800, 11500, 2500),
        (  250, 1750, 9500, 11500, 2500),
        (  100, 1800, 9000, 11500, 2500),
        (   50, 1850, 8500, 11500, 2500),
    ],
    # NY: nuclear + gas, dense demand
    "NY": [
        (  800, 1500, 14000,  9000, 4700),
        (  900, 1450, 14800,  9000, 4700),
        (  850, 1400, 15200,  9000, 4700),
        (  700, 1450, 14800,  9000, 4700),
        (  400, 1500, 14200,  9000, 4700),
        (  100, 1550, 13200,  9000, 4700),
    ],
}


def _gen_hours(region: str) -> list[dict]:
    rows = []
    for i, (solar, wind, ng, nuc, col) in enumerate(_GEN_BASE[region]):
        period = f"2026-06-23T{14 + i:02d}"
        for fueltype, value in [
            ("SUN", solar), ("WND", wind),
            ("NG", ng), ("NUC", nuc), ("COL", col),
        ]:
            rows.append({"period": period, "respondent": region, "fueltype": fueltype, "value": value})
    return rows


DEMO_GENERATION: dict[str, list[dict]] = {r: _gen_hours(r) for r in _GEN_BASE}

# ---------------------------------------------------------------------------
# NOAA weather data  (pre-parsed, matches noaa_client._parse_period output)
# keyed by "lat,lon" matching REGIONS config exactly
# ---------------------------------------------------------------------------

def _weather_hours(start_temps: list[float], winds: list[float], clouds: list[float]) -> list[dict]:
    return [
        {
            "startTime": f"2026-06-23T{14 + i:02d}:00:00",
            "temp_f": t,
            "wind_mph": w,
            "cloud_pct": c,
            "short_forecast": _cloud_label(c),
        }
        for i, (t, w, c) in enumerate(zip(start_temps, winds, clouds))
    ]


def _cloud_label(pct: float) -> str:
    if pct < 15:
        return "Sunny"
    if pct < 35:
        return "Mostly Sunny"
    if pct < 65:
        return "Partly Cloudy"
    if pct < 85:
        return "Mostly Cloudy"
    return "Cloudy"


DEMO_WEATHER: dict[str, list[dict]] = {
    "36.75,-119.78": _weather_hours(    # CAL
        start_temps=[96, 97, 98, 97, 94, 90],
        winds=[8, 7, 6, 7, 9, 10],
        clouds=[5, 5, 5, 5, 10, 15],
    ),
    "30.27,-97.74": _weather_hours(     # TEX
        start_temps=[101, 103, 104, 103, 100, 97],
        winds=[6, 5, 5, 6, 7, 8],
        clouds=[5, 5, 5, 5, 10, 10],
    ),
    "38.89,-77.03": _weather_hours(     # MIDA
        start_temps=[88, 90, 91, 89, 86, 83],
        winds=[10, 9, 8, 9, 11, 12],
        clouds=[30, 30, 35, 35, 40, 40],
    ),
    "41.85,-87.65": _weather_hours(     # MIDW
        start_temps=[85, 87, 88, 86, 84, 80],
        winds=[16, 15, 14, 15, 17, 18],
        clouds=[20, 20, 25, 20, 20, 15],
    ),
    "42.36,-71.06": _weather_hours(     # NE
        start_temps=[82, 84, 85, 84, 81, 78],
        winds=[9, 8, 8, 9, 10, 11],
        clouds=[40, 40, 45, 45, 50, 50],
    ),
    "40.71,-74.01": _weather_hours(     # NY
        start_temps=[90, 92, 93, 92, 89, 86],
        winds=[7, 7, 6, 7, 8, 9],
        clouds=[20, 20, 25, 25, 30, 30],
    ),
}

# ---------------------------------------------------------------------------
# Pre-baked stress briefs for demo mode
# ---------------------------------------------------------------------------

DEMO_BRIEFS: dict[str, str] = {
    "CAL": (
        "California's grid is in LOW stress this afternoon despite near-100F temperatures. "
        "Strong solar output (10,000 MWh) is offsetting a significant share of peak demand, "
        "keeping net load well within the firm capacity margin. "
        "Stress will tick up modestly as solar output falls toward sunset."
    ),
    "TEX": (
        "Texas is in HIGH stress driven by a combination of extreme heat (104F) and low wind "
        "generation. With demand near 68,000 MWh and wind contributing only 5,000 MWh, "
        "gas generation is carrying 66% of load. Reserve margins are thin. "
        "A further 10% demand increase would push the grid into CRITICAL territory."
    ),
    "MIDA": (
        "Mid-Atlantic is in ELEVATED stress as high humidity and temperatures in the upper 80s "
        "drive air conditioning demand. Renewable contributions are modest -- solar and wind "
        "together cover less than 7% of load -- keeping firm generation under sustained pressure. "
        "No immediate relief expected until overnight demand softens."
    ),
    "MIDW": (
        "Midwest is in ELEVATED stress. Strong Great Lakes wind (9,000 MWh) is helping, but "
        "total demand of 68,000 MWh is still drawing heavily on coal and gas baseload. "
        "A shift in wind to the west overnight could reduce renewable supply and push stress higher."
    ),
    "NE": (
        "New England is in HIGH stress due to limited generation capacity relative to demand. "
        "Nuclear provides the backbone (11,500 MWh), but at 25,000 MWh demand the region is "
        "operating near the upper bound of its firm capacity. "
        "A summer demand surge or unexpected nuclear outage would trigger CRITICAL conditions."
    ),
    "NY": (
        "New York is in ELEVATED stress with urban demand at 30,000 MWh. "
        "Nuclear and gas are carrying the load in roughly equal measure; "
        "solar and wind contribute under 8%. "
        "Grid conditions are stable but headroom is limited through evening peak hours."
    ),
    "_default": (
        "Grid stress data is available in demo mode. "
        "Set DEMO_MODE=False and provide EIA_API_KEY to generate live stress briefs "
        "from real hourly demand and generation data."
    ),
}
