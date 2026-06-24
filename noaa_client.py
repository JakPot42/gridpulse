"""NOAA weather.gov API client — no API key required."""
import requests
from config import NOAA_BASE, USER_AGENT, DEMO_MODE

_HEADERS = {"User-Agent": USER_AGENT, "Accept": "application/geo+json"}


def _get(url: str) -> dict:
    resp = requests.get(url, headers=_HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.json()


def get_hourly_forecast_url(lat: float, lon: float) -> str:
    data = _get(f"{NOAA_BASE}/points/{lat},{lon}")
    return data["properties"]["forecastHourly"]


def fetch_hourly_forecast(lat: float, lon: float, hours: int = 24) -> list[dict]:
    """
    Returns list of parsed hourly weather dicts:
      {startTime, temp_f, wind_mph, cloud_pct, short_forecast}
    """
    if DEMO_MODE:
        from seed_data import DEMO_WEATHER
        key = f"{lat},{lon}"
        return DEMO_WEATHER.get(key, [])[:hours]
    url = get_hourly_forecast_url(lat, lon)
    data = _get(url)
    periods = data["properties"]["periods"][:hours]
    return [_parse_period(p) for p in periods]


def _parse_period(period: dict) -> dict:
    wind_mph = _parse_wind_speed(period.get("windSpeed", "0 mph"))
    cloud_pct = _parse_cloud_cover(period.get("shortForecast", ""))
    return {
        "startTime": period["startTime"],
        "temp_f": float(period["temperature"]),
        "wind_mph": wind_mph,
        "cloud_pct": cloud_pct,
        "short_forecast": period.get("shortForecast", ""),
    }


def _parse_wind_speed(s: str) -> float:
    """Parse '10 mph' or '5 to 10 mph' into a single float average."""
    clean = s.lower().replace("mph", "").strip()
    nums: list[float] = []
    for part in clean.split("to"):
        try:
            nums.append(float(part.strip()))
        except ValueError:
            pass
    return sum(nums) / len(nums) if nums else 0.0


def _parse_cloud_cover(forecast: str) -> float:
    """Map NOAA shortForecast string to cloud cover percentage."""
    f = forecast.lower()
    if "partly" in f:
        return 50.0
    if "mostly" in f and ("sunny" in f or "clear" in f):
        return 20.0
    if "mostly cloudy" in f:
        return 80.0
    if any(w in f for w in ("cloudy", "overcast")):
        return 95.0
    if any(w in f for w in ("sunny", "clear")):
        return 5.0
    return 50.0
