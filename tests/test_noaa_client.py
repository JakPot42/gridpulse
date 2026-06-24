"""Tests for noaa_client.py — parsing and demo mode."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from noaa_client import _parse_wind_speed, _parse_cloud_cover, fetch_hourly_forecast
from config import REGIONS


class TestParseWindSpeed:
    @pytest.mark.parametrize("s,expected", [
        ("10 mph",    10.0),
        ("0 mph",      0.0),
        ("15 mph",    15.0),
        ("5 to 10 mph", 7.5),
        ("15 to 20 mph", 17.5),
        ("3 to 7 mph",  5.0),
        ("",           0.0),
        ("0 to 0 mph", 0.0),
    ])
    def test_parse(self, s, expected):
        assert _parse_wind_speed(s) == pytest.approx(expected)


class TestParseCloudCover:
    @pytest.mark.parametrize("forecast,expected", [
        ("Sunny",           5.0),
        ("Clear",           5.0),
        ("Mostly Sunny",   20.0),
        ("Mostly Clear",   20.0),
        ("Partly Cloudy",  50.0),
        ("Partly Sunny",   50.0),
        ("Mostly Cloudy",  80.0),
        ("Cloudy",         95.0),
        ("Overcast",       95.0),
        ("",               50.0),  # unknown defaults to 50
    ])
    def test_parse(self, forecast, expected):
        assert _parse_cloud_cover(forecast) == pytest.approx(expected)


class TestFetchHourlyForecastDemoMode:
    def test_returns_list(self):
        lat = REGIONS["CAL"]["lat"]
        lon = REGIONS["CAL"]["lon"]
        result = fetch_hourly_forecast(lat, lon, 6)
        assert isinstance(result, list)

    def test_respects_hours_limit(self):
        lat = REGIONS["CAL"]["lat"]
        lon = REGIONS["CAL"]["lon"]
        result = fetch_hourly_forecast(lat, lon, 3)
        assert len(result) <= 3

    def test_entries_have_required_fields(self):
        lat = REGIONS["TEX"]["lat"]
        lon = REGIONS["TEX"]["lon"]
        result = fetch_hourly_forecast(lat, lon, 6)
        for entry in result:
            assert "temp_f" in entry
            assert "wind_mph" in entry
            assert "cloud_pct" in entry
            assert "startTime" in entry

    def test_all_regions_return_data(self):
        for region, cfg in REGIONS.items():
            result = fetch_hourly_forecast(cfg["lat"], cfg["lon"], 3)
            assert len(result) > 0, f"No weather data for {region}"

    def test_unknown_lat_lon_returns_empty(self):
        result = fetch_hourly_forecast(0.0, 0.0, 6)
        assert result == []
