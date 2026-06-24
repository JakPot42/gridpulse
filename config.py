"""GridPulse configuration — regions, thresholds, API endpoints."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
EIA_API_KEY: str = os.getenv("EIA_API_KEY", "")
DEMO_MODE: bool = os.getenv("DEMO_MODE", "True").lower() not in ("false", "0", "no")
MODEL: str = os.getenv("GRIDPULSE_MODEL", "claude-haiku-4-5-20251001")
DB_PATH: str = os.getenv("GRIDPULSE_DB", str(Path(__file__).parent / "gridpulse.db"))

EIA_BASE = "https://api.eia.gov/v2"
NOAA_BASE = "https://api.weather.gov"
USER_AGENT = "GridPulse/1.0 (portfolio; contact jak.potvin@gmail.com)"

# firm_gw: estimated firm (dispatchable) generation capacity in GW per region
REGIONS: dict[str, dict] = {
    "CAL":  {"name": "California",   "lat": 36.75, "lon": -119.78, "firm_gw": 52.0},
    "TEX":  {"name": "Texas",        "lat": 30.27, "lon":  -97.74, "firm_gw": 71.0},
    "MIDA": {"name": "Mid-Atlantic", "lat": 38.89, "lon":  -77.03, "firm_gw": 64.0},
    "MIDW": {"name": "Midwest",      "lat": 41.85, "lon":  -87.65, "firm_gw": 78.0},
    "NE":   {"name": "New England",  "lat": 42.36, "lon":  -71.06, "firm_gw": 28.0},
    "NY":   {"name": "New York",     "lat": 40.71, "lon":  -74.01, "firm_gw": 38.0},
}

STRESS_TIERS: dict[str, tuple[float, float]] = {
    "LOW":      (0.0,  25.0),
    "ELEVATED": (25.0, 50.0),
    "HIGH":     (50.0, 75.0),
    "CRITICAL": (75.0, 100.1),  # upper bound open
}

FUEL_RENEWABLE_VARIABLE: set[str] = {"SUN", "WND"}
FUEL_FIRM: set[str] = {"NG", "NUC", "COL", "OIL"}
FUEL_HYDRO: set[str] = {"WAT"}
FUEL_ALL: set[str] = {"COL", "NG", "NUC", "OIL", "OTH", "SUN", "UNK", "WAT", "WND"}

SCENARIO_DEFAULTS: dict[str, dict] = {
    "wind_drop":    {"wind_pct": -20.0, "solar_pct": 0.0,  "demand_pct": 0.0},
    "solar_drop":   {"wind_pct": 0.0,   "solar_pct": -30.0, "demand_pct": 0.0},
    "demand_surge": {"wind_pct": 0.0,   "solar_pct": 0.0,  "demand_pct": +15.0},
    "polar_vortex": {"wind_pct": -10.0, "solar_pct": 0.0,  "demand_pct": +25.0},
}
