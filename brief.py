"""Claude Haiku stress-driver narrative brief.

Live-mode Claude call delegates to the shared claude_brief.call_claude()
(Phase 6, Cluster 5 consistency pass) instead of constructing its own
anthropic.Anthropic client -- on_error="raise" preserves this repo's own
Step 0 fix (a dedicated `brief` command should fail loudly, not silently
succeed with the wrong content), now raising claude_brief.ClaudeCallError
instead of a locally-defined RuntimeError.
"""
from claude_brief import call_claude
from config import MODEL, DEMO_MODE
from stress_engine import RegionSnapshot
from scenarios import ScenarioResult


def generate_brief(
    snap: RegionSnapshot,
    scenario_result: ScenarioResult | None = None,
    *,
    demo_mode: bool = DEMO_MODE,
) -> str:
    if demo_mode:
        from seed_data import DEMO_BRIEFS
        return DEMO_BRIEFS.get(snap.region, DEMO_BRIEFS["_default"])
    return call_claude(
        [{"role": "user", "content": _build_prompt(snap, scenario_result)}],
        max_tokens=350,
        model=MODEL,
        on_error="raise",
    )


def _build_prompt(snap: RegionSnapshot, scenario_result: ScenarioResult | None) -> str:
    lines = [
        f"Write a 2-3 sentence plain-language brief explaining what is driving the current "
        f"grid stress level for {snap.region}. Focus on the physical cause: weather, demand "
        f"pattern, or generation mix. Be specific about numbers. Do not hedge with disclaimers.",
        "",
        f"Region: {snap.region}",
        f"Stress tier: {snap.tier} (score {snap.stress_score:.1f} / 100)",
        f"Demand: {snap.demand_mwh:,.0f} MWh",
        f"Solar: {snap.solar_mwh:,.0f} MWh",
        f"Wind: {snap.wind_mwh:,.0f} MWh",
        f"Firm (gas+nuclear+coal): {snap.firm_mwh:,.0f} MWh",
        f"Net load on firm capacity: {snap.net_load_mwh:,.0f} MWh",
        f"Firm capacity available: {snap.firm_capacity_mw:,.0f} MW",
        f"Renewable share of demand: {snap.renewable_pct:.1f}%",
    ]
    if snap.temp_f is not None:
        lines.append(f"Temperature: {snap.temp_f:.0f} F")
    if snap.wind_speed_mph is not None:
        lines.append(f"Observed wind speed: {snap.wind_speed_mph:.0f} mph")
    if snap.cloud_cover_pct is not None:
        lines.append(f"Cloud cover: {snap.cloud_cover_pct:.0f}%")
    if scenario_result:
        lines += [
            "",
            f"Scenario applied: {scenario_result.scenario}",
            f"Score change: {scenario_result.delta_score:+.1f} points",
            f"New tier: {scenario_result.modified.tier}",
        ]
        if scenario_result.delta_tier:
            lines.append("(Tier escalated -- mention this in the brief.)")
    return "\n".join(lines)
