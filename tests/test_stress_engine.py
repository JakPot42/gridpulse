"""Tests for stress_engine.py — deterministic score computation."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from stress_engine import compute_stress, score_to_tier, build_snapshot


# ---------------------------------------------------------------------------
# compute_stress
# ---------------------------------------------------------------------------

class TestComputeStress:
    def test_zero_renewables_net_load_equals_demand(self):
        score, net = compute_stress(60000, 0, 0, 78000)
        assert net == 60000.0

    def test_renewables_reduce_net_load(self):
        _, net = compute_stress(60000, 5000, 3000, 78000)
        assert net == 52000.0

    def test_renewables_exceed_demand_clamps_net_load_to_zero(self):
        _, net = compute_stress(5000, 3000, 3000, 78000)
        assert net == 0.0

    def test_below_60pct_firm_utilization_clamps_score_to_zero(self):
        # demand < 0.6 * firm → raw score negative → clamped to 0
        score, _ = compute_stress(30000, 0, 0, 100000)
        assert score == 0.0

    def test_at_60pct_firm_utilization_score_is_zero(self):
        # ratio = 60000/100000 = 0.6 → raw = 0
        score, _ = compute_stress(60000, 0, 0, 100000)
        assert score == pytest.approx(0.0, abs=0.01)

    def test_at_80pct_firm_utilization_score_is_50(self):
        # (0.8 - 0.6) / 0.4 * 100 = 50
        score, _ = compute_stress(80000, 0, 0, 100000)
        assert score == pytest.approx(50.0, abs=0.01)

    def test_at_90pct_firm_utilization_score_is_75(self):
        # (0.9 - 0.6) / 0.4 * 100 = 75
        score, _ = compute_stress(90000, 0, 0, 100000)
        assert score == pytest.approx(75.0, abs=0.01)

    def test_at_100pct_firm_utilization_score_is_100(self):
        # (1.0 - 0.6) / 0.4 * 100 = 100
        score, _ = compute_stress(100000, 0, 0, 100000)
        assert score == pytest.approx(100.0, abs=0.01)

    def test_above_100pct_clamps_to_100(self):
        score, _ = compute_stress(120000, 0, 0, 100000)
        assert score == 100.0

    def test_zero_firm_capacity_returns_100(self):
        score, _ = compute_stress(50000, 0, 0, 0)
        assert score == 100.0

    def test_score_always_between_0_and_100(self):
        for demand in [0, 10000, 50000, 100000, 200000]:
            score, _ = compute_stress(demand, 0, 0, 100000)
            assert 0.0 <= score <= 100.0

    def test_solar_and_wind_reduce_score(self):
        score_no_renew, _ = compute_stress(80000, 0, 0, 100000)
        score_with_renew, _ = compute_stress(80000, 5000, 5000, 100000)
        assert score_with_renew < score_no_renew


# ---------------------------------------------------------------------------
# score_to_tier
# ---------------------------------------------------------------------------

class TestScoreToTier:
    @pytest.mark.parametrize("score,expected", [
        (0.0,  "LOW"),
        (12.5, "LOW"),
        (24.9, "LOW"),
        (25.0, "ELEVATED"),
        (37.5, "ELEVATED"),
        (49.9, "ELEVATED"),
        (50.0, "HIGH"),
        (62.5, "HIGH"),
        (74.9, "HIGH"),
        (75.0, "CRITICAL"),
        (87.5, "CRITICAL"),
        (100.0,"CRITICAL"),
    ])
    def test_tier_boundaries(self, score, expected):
        assert score_to_tier(score) == expected


# ---------------------------------------------------------------------------
# build_snapshot
# ---------------------------------------------------------------------------

class TestBuildSnapshot:
    def _basic(self, **overrides):
        kwargs = dict(
            region="CAL",
            hour="2026-06-23T14",
            demand_mwh=45000,
            solar_mwh=10000,
            wind_mwh=3000,
            firm_mwh=32000,
        )
        kwargs.update(overrides)
        return build_snapshot(**kwargs)

    def test_region_field_set(self):
        snap = self._basic()
        assert snap.region == "CAL"

    def test_hour_field_set(self):
        snap = self._basic()
        assert snap.hour == "2026-06-23T14"

    def test_firm_capacity_mw_from_regions_config(self):
        snap = self._basic(region="CAL")
        assert snap.firm_capacity_mw == 52000.0  # 52.0 GW * 1000

    def test_tex_firm_capacity(self):
        snap = build_snapshot("TEX", "2026-06-23T14", 68000, 2000, 5000, 40000)
        assert snap.firm_capacity_mw == 71000.0

    def test_stress_score_computed(self):
        snap = self._basic()
        # net_load = 45000-10000-3000 = 32000; ratio=32000/52000=0.6154; score=3.85
        assert snap.stress_score == pytest.approx(3.85, abs=0.1)

    def test_tier_derived_from_score(self):
        snap = self._basic()
        assert snap.tier == score_to_tier(snap.stress_score)

    def test_net_load_mwh_field(self):
        snap = self._basic()
        assert snap.net_load_mwh == pytest.approx(32000.0)

    def test_renewable_pct_calculation(self):
        snap = self._basic()
        # (10000+3000)/45000*100 = 28.89
        assert snap.renewable_pct == pytest.approx(28.89, abs=0.1)

    def test_optional_weather_fields_preserved(self):
        snap = build_snapshot(
            "NE", "2026-06-23T14", 25000, 300, 1800, 20000,
            temp_f=82.0, wind_speed_mph=9.0, cloud_cover_pct=40.0,
        )
        assert snap.temp_f == 82.0
        assert snap.wind_speed_mph == 9.0
        assert snap.cloud_cover_pct == 40.0

    def test_weather_fields_default_to_none(self):
        snap = self._basic()
        assert snap.temp_f is None
        assert snap.wind_speed_mph is None
        assert snap.cloud_cover_pct is None

    def test_score_between_0_and_100(self):
        snap = self._basic()
        assert 0.0 <= snap.stress_score <= 100.0
