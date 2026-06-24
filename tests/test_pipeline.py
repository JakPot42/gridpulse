"""Tests for pipeline.py — data merge and snapshot assembly."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from pipeline import build_snapshots, current_snapshot, _merge
from stress_engine import RegionSnapshot
from config import REGIONS


REGION_KEYS = list(REGIONS.keys())


class TestBuildSnapshots:
    def test_returns_dict(self):
        result = build_snapshots(hours=3)
        assert isinstance(result, dict)

    def test_all_regions_present_by_default(self):
        result = build_snapshots(hours=3)
        for region in REGION_KEYS:
            assert region in result

    def test_single_region_requested(self):
        result = build_snapshots(regions=["CAL"], hours=3)
        assert set(result.keys()) == {"CAL"}

    def test_snapshots_are_region_snapshot_objects(self):
        result = build_snapshots(regions=["TEX"], hours=3)
        for snap in result["TEX"]:
            assert isinstance(snap, RegionSnapshot)

    @pytest.mark.parametrize("region", REGION_KEYS)
    def test_stress_score_in_range(self, region):
        result = build_snapshots(regions=[region], hours=3)
        for snap in result[region]:
            assert 0.0 <= snap.stress_score <= 100.0

    @pytest.mark.parametrize("region", REGION_KEYS)
    def test_tier_is_valid(self, region):
        valid_tiers = {"LOW", "ELEVATED", "HIGH", "CRITICAL"}
        result = build_snapshots(regions=[region], hours=3)
        for snap in result[region]:
            assert snap.tier in valid_tiers

    def test_hours_controls_number_of_snapshots(self):
        result = build_snapshots(regions=["CAL"], hours=3)
        assert len(result["CAL"]) <= 3

    def test_snapshots_sorted_chronologically(self):
        result = build_snapshots(regions=["MIDA"], hours=6)
        snaps = result["MIDA"]
        for i in range(len(snaps) - 1):
            assert snaps[i].hour <= snaps[i + 1].hour

    def test_weather_fields_populated(self):
        result = build_snapshots(regions=["CAL"], hours=3)
        for snap in result["CAL"]:
            assert snap.temp_f is not None
            assert snap.wind_speed_mph is not None
            assert snap.cloud_cover_pct is not None


class TestMerge:
    def _demand(self, region="CAL", hours=3):
        return [
            {"period": f"2026-06-23T{14+i:02d}", "respondent": region, "type": "D", "value": 45000.0 + i * 1000}
            for i in range(hours)
        ]

    def _generation(self, region="CAL", hours=3):
        rows = []
        for i in range(hours):
            period = f"2026-06-23T{14+i:02d}"
            rows += [
                {"period": period, "respondent": region, "fueltype": "SUN", "value": 10000.0},
                {"period": period, "respondent": region, "fueltype": "WND", "value": 3000.0},
                {"period": period, "respondent": region, "fueltype": "NG", "value": 22000.0},
                {"period": period, "respondent": region, "fueltype": "NUC", "value": 9800.0},
                {"period": period, "respondent": region, "fueltype": "COL", "value": 200.0},
            ]
        return rows

    def _weather(self, hours=3):
        return [
            {"startTime": f"2026-06-23T{14+i:02d}:00:00", "temp_f": 96.0, "wind_mph": 8.0, "cloud_pct": 5.0}
            for i in range(hours)
        ]

    def test_returns_list_of_snapshots(self):
        result = _merge("CAL", self._demand(), self._generation(), self._weather())
        assert isinstance(result, list)
        assert len(result) > 0
        assert isinstance(result[0], RegionSnapshot)

    def test_solar_extracted_from_generation(self):
        result = _merge("CAL", self._demand(), self._generation(), self._weather())
        assert result[0].solar_mwh == 10000.0

    def test_wind_extracted_from_generation(self):
        result = _merge("CAL", self._demand(), self._generation(), self._weather())
        assert result[0].wind_mwh == 3000.0

    def test_firm_summed_from_ng_nuc_col_oil(self):
        result = _merge("CAL", self._demand(), self._generation(), self._weather())
        # NG=22000 + NUC=9800 + COL=200 = 32000
        assert result[0].firm_mwh == pytest.approx(32000.0)

    def test_weather_fields_mapped(self):
        result = _merge("CAL", self._demand(), self._generation(), self._weather())
        assert result[0].temp_f == 96.0
        assert result[0].wind_speed_mph == 8.0
        assert result[0].cloud_cover_pct == 5.0

    def test_no_overlap_returns_empty(self):
        demand = [{"period": "2026-06-23T14", "respondent": "CAL", "type": "D", "value": 45000}]
        gen = [{"period": "2026-06-23T15", "respondent": "CAL", "fueltype": "NG", "value": 30000}]
        result = _merge("CAL", demand, gen, [])
        assert result == []


class TestCurrentSnapshot:
    def test_returns_first_snapshot(self):
        snaps = build_snapshots(regions=["TEX"], hours=6)["TEX"]
        cs = current_snapshot(snaps)
        assert cs is snaps[0]

    def test_empty_list_returns_none(self):
        assert current_snapshot([]) is None

    def test_single_element_list(self):
        snap = build_snapshots(regions=["NY"], hours=1)["NY"]
        result = current_snapshot(snap)
        assert result is not None
