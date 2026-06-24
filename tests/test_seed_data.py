"""Tests for seed_data.py — structure and correctness of demo data."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from config import REGIONS
from seed_data import DEMO_DEMAND, DEMO_GENERATION, DEMO_WEATHER, DEMO_BRIEFS


REGION_KEYS = list(REGIONS.keys())


class TestDemoDemand:
    def test_all_regions_present(self):
        for region in REGION_KEYS:
            assert region in DEMO_DEMAND, f"Missing region: {region}"

    @pytest.mark.parametrize("region", REGION_KEYS)
    def test_region_has_data(self, region):
        assert len(DEMO_DEMAND[region]) > 0

    @pytest.mark.parametrize("region", REGION_KEYS)
    def test_demand_value_positive(self, region):
        for row in DEMO_DEMAND[region]:
            assert row["value"] > 0

    @pytest.mark.parametrize("region", REGION_KEYS)
    def test_period_format(self, region):
        for row in DEMO_DEMAND[region]:
            assert "T" in row["period"]  # "YYYY-MM-DDTHH"
            assert len(row["period"]) == 13  # 2026-06-23T14

    @pytest.mark.parametrize("region", REGION_KEYS)
    def test_respondent_matches_region(self, region):
        for row in DEMO_DEMAND[region]:
            assert row["respondent"] == region

    def test_all_regions_have_same_period_count(self):
        counts = {r: len(v) for r, v in DEMO_DEMAND.items()}
        assert len(set(counts.values())) == 1, f"Period counts differ: {counts}"


class TestDemoGeneration:
    def test_all_regions_present(self):
        for region in REGION_KEYS:
            assert region in DEMO_GENERATION

    @pytest.mark.parametrize("region", REGION_KEYS)
    def test_has_sun_entries(self, region):
        fuels = {row["fueltype"] for row in DEMO_GENERATION[region]}
        assert "SUN" in fuels

    @pytest.mark.parametrize("region", REGION_KEYS)
    def test_has_wind_entries(self, region):
        fuels = {row["fueltype"] for row in DEMO_GENERATION[region]}
        assert "WND" in fuels

    @pytest.mark.parametrize("region", REGION_KEYS)
    def test_has_ng_entries(self, region):
        fuels = {row["fueltype"] for row in DEMO_GENERATION[region]}
        assert "NG" in fuels

    @pytest.mark.parametrize("region", REGION_KEYS)
    def test_values_non_negative(self, region):
        for row in DEMO_GENERATION[region]:
            assert row["value"] >= 0

    @pytest.mark.parametrize("region", REGION_KEYS)
    def test_periods_match_demand_periods(self, region):
        gen_periods = {row["period"] for row in DEMO_GENERATION[region]}
        demand_periods = {row["period"] for row in DEMO_DEMAND[region]}
        assert gen_periods == demand_periods


class TestDemoWeather:
    def _lat_lon_keys(self):
        return {f"{r['lat']},{r['lon']}" for r in REGIONS.values()}

    def test_all_region_lat_lon_keys_present(self):
        for region_cfg in REGIONS.values():
            key = f"{region_cfg['lat']},{region_cfg['lon']}"
            assert key in DEMO_WEATHER, f"Missing weather key: {key}"

    def test_weather_entries_have_required_fields(self):
        for key, entries in DEMO_WEATHER.items():
            for entry in entries:
                assert "startTime" in entry
                assert "temp_f" in entry
                assert "wind_mph" in entry
                assert "cloud_pct" in entry

    def test_temperature_plausible(self):
        for entries in DEMO_WEATHER.values():
            for entry in entries:
                assert 0 <= entry["temp_f"] <= 130, f"Implausible temp: {entry['temp_f']}"

    def test_cloud_pct_in_range(self):
        for entries in DEMO_WEATHER.values():
            for entry in entries:
                assert 0.0 <= entry["cloud_pct"] <= 100.0

    def test_wind_mph_non_negative(self):
        for entries in DEMO_WEATHER.values():
            for entry in entries:
                assert entry["wind_mph"] >= 0.0


class TestDemoBriefs:
    def test_all_regions_have_brief(self):
        for region in REGION_KEYS:
            assert region in DEMO_BRIEFS, f"Missing brief for {region}"

    def test_default_brief_present(self):
        assert "_default" in DEMO_BRIEFS

    @pytest.mark.parametrize("region", REGION_KEYS)
    def test_brief_is_nonempty_string(self, region):
        assert isinstance(DEMO_BRIEFS[region], str)
        assert len(DEMO_BRIEFS[region]) > 50
