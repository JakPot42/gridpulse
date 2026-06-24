"""Tests for scenarios.py — what-if modifiers and joule export."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from stress_engine import build_snapshot, RegionSnapshot
from scenarios import apply_scenario, run_scenario, run_named_scenario, to_joule_format
from config import SCENARIO_DEFAULTS


def _make_snap(region="TEX", demand=68000.0, solar=2000.0, wind=5000.0, firm=40000.0) -> RegionSnapshot:
    return build_snapshot(region, "2026-06-23T14", demand, solar, wind, firm)


# ---------------------------------------------------------------------------
# apply_scenario
# ---------------------------------------------------------------------------

class TestApplyScenario:
    def test_wind_drop_reduces_wind_mwh(self):
        snap = _make_snap(wind=5000)
        mod = apply_scenario(snap, wind_pct=-20)
        assert mod.wind_mwh == pytest.approx(4000.0)

    def test_solar_drop_reduces_solar_mwh(self):
        snap = _make_snap(solar=2000)
        mod = apply_scenario(snap, solar_pct=-30)
        assert mod.solar_mwh == pytest.approx(1400.0)

    def test_demand_surge_increases_demand_mwh(self):
        snap = _make_snap(demand=68000)
        mod = apply_scenario(snap, demand_pct=15)
        assert mod.demand_mwh == pytest.approx(78200.0)

    def test_multiple_modifiers_applied_independently(self):
        snap = _make_snap(demand=68000, wind=5000, solar=2000)
        mod = apply_scenario(snap, demand_pct=10, wind_pct=-20, solar_pct=-30)
        assert mod.demand_mwh == pytest.approx(74800.0)
        assert mod.wind_mwh == pytest.approx(4000.0)
        assert mod.solar_mwh == pytest.approx(1400.0)

    def test_wind_drop_100pct_clamps_to_zero(self):
        snap = _make_snap(wind=5000)
        mod = apply_scenario(snap, wind_pct=-100)
        assert mod.wind_mwh == 0.0

    def test_demand_drop_100pct_clamps_to_zero(self):
        snap = _make_snap(demand=68000)
        mod = apply_scenario(snap, demand_pct=-100)
        assert mod.demand_mwh == 0.0

    def test_no_modifiers_score_unchanged(self):
        snap = _make_snap()
        mod = apply_scenario(snap)
        assert mod.stress_score == pytest.approx(snap.stress_score, abs=0.01)

    def test_wind_drop_increases_stress_score(self):
        snap = _make_snap(wind=5000)
        mod = apply_scenario(snap, wind_pct=-20)
        assert mod.stress_score >= snap.stress_score

    def test_demand_surge_increases_stress_score(self):
        snap = _make_snap()
        mod = apply_scenario(snap, demand_pct=15)
        assert mod.stress_score >= snap.stress_score

    def test_region_and_hour_preserved(self):
        snap = _make_snap(region="NE")
        mod = apply_scenario(snap, wind_pct=-20)
        assert mod.region == "NE"
        assert mod.hour == snap.hour


# ---------------------------------------------------------------------------
# run_scenario
# ---------------------------------------------------------------------------

class TestRunScenario:
    def test_returns_scenario_result(self):
        from scenarios import ScenarioResult
        snap = _make_snap()
        result = run_scenario(snap, "test", wind_pct=-20)
        assert isinstance(result, ScenarioResult)

    def test_delta_score_is_difference(self):
        snap = _make_snap()
        result = run_scenario(snap, "test", wind_pct=-20)
        assert result.delta_score == pytest.approx(
            result.modified.stress_score - snap.stress_score, abs=0.01
        )

    def test_delta_tier_true_when_tier_escalates(self):
        # TEX: demand=55000, no renewables → net_load=55000, ratio=55000/71000=0.775
        # score = (0.775-0.6)/0.4*100 = 43.7 → ELEVATED
        # demand_pct=+10 → new demand=60500 → score=63 → HIGH (escalation)
        snap = build_snapshot("TEX", "2026-06-23T14", demand_mwh=55000, solar_mwh=0, wind_mwh=0, firm_mwh=0)
        assert snap.tier == "ELEVATED"
        result = run_scenario(snap, "escalate", demand_pct=10)
        assert result.modified.tier == "HIGH"
        assert result.delta_tier is True

    def test_delta_tier_false_when_tier_unchanged(self):
        snap = _make_snap(demand=50000)  # LOW stress
        result = run_scenario(snap, "tiny", wind_pct=-1)
        if result.modified.tier == snap.tier:
            assert result.delta_tier is False

    def test_scenario_name_stored(self):
        snap = _make_snap()
        result = run_scenario(snap, "my_scenario", wind_pct=-20)
        assert result.scenario == "my_scenario"

    def test_base_snapshot_preserved(self):
        snap = _make_snap()
        result = run_scenario(snap, "test", wind_pct=-20)
        assert result.base is snap


# ---------------------------------------------------------------------------
# run_named_scenario
# ---------------------------------------------------------------------------

class TestRunNamedScenario:
    @pytest.mark.parametrize("name", list(SCENARIO_DEFAULTS.keys()))
    def test_all_named_scenarios_run(self, name):
        snap = _make_snap()
        result = run_named_scenario(snap, name)
        assert result.scenario == name

    def test_wind_drop_uses_default_wind_pct(self):
        snap = _make_snap(wind=5000)
        result = run_named_scenario(snap, "wind_drop")
        expected_wind = 5000 * (1 + SCENARIO_DEFAULTS["wind_drop"]["wind_pct"] / 100)
        assert result.modified.wind_mwh == pytest.approx(expected_wind)

    def test_invalid_name_raises_value_error(self):
        snap = _make_snap()
        with pytest.raises(ValueError, match="Unknown scenario"):
            run_named_scenario(snap, "nuke_it_from_orbit")


# ---------------------------------------------------------------------------
# to_joule_format
# ---------------------------------------------------------------------------

class TestToJouleFormat:
    def test_returns_dict_with_region_keys(self):
        snaps = [_make_snap(region="CAL"), _make_snap(region="TEX")]
        result = to_joule_format(snaps)
        assert set(result.keys()) == {"CAL", "TEX"}

    def test_each_region_has_required_keys(self):
        snap = _make_snap(region="NE")
        result = to_joule_format([snap])
        required = {"stress_score", "tier", "net_load_mwh", "firm_capacity_mw",
                    "demand_mwh", "renewable_pct", "hour"}
        assert required.issubset(set(result["NE"].keys()))

    def test_stress_score_rounded(self):
        snap = _make_snap()
        result = to_joule_format([snap])
        score = result["TEX"]["stress_score"]
        # Should be rounded to 1 decimal place
        assert score == round(score, 1)

    def test_tier_matches_snapshot(self):
        snap = _make_snap()
        result = to_joule_format([snap])
        assert result["TEX"]["tier"] == snap.tier

    def test_empty_list_returns_empty_dict(self):
        assert to_joule_format([]) == {}

    def test_hour_preserved(self):
        snap = _make_snap()
        result = to_joule_format([snap])
        assert result["TEX"]["hour"] == "2026-06-23T14"
