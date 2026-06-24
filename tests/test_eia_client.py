"""Tests for eia_client.py — demo mode data format."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from eia_client import fetch_demand, fetch_generation_mix
from config import REGIONS


REGION_KEYS = list(REGIONS.keys())


class TestFetchDemandDemoMode:
    @pytest.mark.parametrize("region", REGION_KEYS)
    def test_returns_nonempty_list(self, region):
        result = fetch_demand(region, 6)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_respects_hours_limit(self):
        result = fetch_demand("CAL", 3)
        assert len(result) <= 3

    @pytest.mark.parametrize("region", REGION_KEYS)
    def test_entries_have_period_and_value(self, region):
        result = fetch_demand(region, 6)
        for row in result:
            assert "period" in row
            assert "value" in row

    @pytest.mark.parametrize("region", REGION_KEYS)
    def test_value_is_positive(self, region):
        for row in fetch_demand(region, 6):
            assert row["value"] > 0

    def test_period_format_is_eia_style(self):
        result = fetch_demand("MIDA", 6)
        for row in result:
            assert len(row["period"]) == 13  # "YYYY-MM-DDTHH"
            assert "T" in row["period"]

    def test_unknown_region_returns_empty(self):
        result = fetch_demand("UNKNOWN", 6)
        assert result == []


class TestFetchGenerationMixDemoMode:
    @pytest.mark.parametrize("region", REGION_KEYS)
    def test_returns_nonempty_list(self, region):
        result = fetch_generation_mix(region, 6)
        assert isinstance(result, list)
        assert len(result) > 0

    @pytest.mark.parametrize("region", REGION_KEYS)
    def test_entries_have_fueltype_field(self, region):
        for row in fetch_generation_mix(region, 6):
            assert "fueltype" in row

    def test_includes_sun_fueltype(self):
        result = fetch_generation_mix("CAL", 6)
        fuels = {r["fueltype"] for r in result}
        assert "SUN" in fuels

    def test_includes_wnd_fueltype(self):
        result = fetch_generation_mix("MIDW", 6)
        fuels = {r["fueltype"] for r in result}
        assert "WND" in fuels

    def test_hours_limit_restricts_distinct_periods(self):
        result = fetch_generation_mix("TEX", 2)
        periods = {r["period"] for r in result}
        assert len(periods) <= 2

    def test_unknown_region_returns_empty(self):
        result = fetch_generation_mix("UNKNOWN", 6)
        assert result == []
