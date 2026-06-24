"""GridPulse CLI — regional grid stress index from EIA demand + NOAA weather."""
import sys
import os
import json
import click
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import DEMO_MODE, REGIONS, SCENARIO_DEFAULTS
from pipeline import build_snapshots, current_snapshot
from scenarios import run_scenario, run_named_scenario, to_joule_format
from brief import generate_brief
from dashboard import (
    console,
    print_banner,
    print_dashboard,
    print_region_timeline,
    print_scenario,
    print_brief,
    print_joule_export,
    print_json,
)

_REGION_CHOICES = sorted(REGIONS.keys())
_SCENARIO_CHOICES = sorted(SCENARIO_DEFAULTS.keys())


@click.group()
@click.option(
    "--hours", default=6, show_default=True, type=int,
    help="Hours of data to fetch (1-24).",
)
@click.pass_context
def cli(ctx: click.Context, hours: int) -> None:
    """
    GridPulse: fuses EIA electricity demand data with NOAA weather forecasts
    into a regional grid stress index.

    \b
    Data sources:
      EIA API v2  -- electricity demand and generation mix
      NOAA API    -- hourly weather forecasts (no API key required)

    Set DEMO_MODE=False and EIA_API_KEY to fetch live data.
    """
    ctx.ensure_object(dict)
    ctx.obj["hours"] = hours


@cli.command()
@click.option(
    "--region", "-r",
    type=click.Choice(_REGION_CHOICES, case_sensitive=False),
    multiple=True,
    help="Region(s) to include. Default: all regions.",
)
@click.pass_context
def dashboard(ctx: click.Context, region: tuple[str, ...]) -> None:
    """Show all-region stress overview for the current hour."""
    print_banner()
    regions = list(region) if region else None
    snapshots = build_snapshots(regions=regions, hours=ctx.obj["hours"])
    print_dashboard(snapshots)
    if DEMO_MODE:
        console.print("[dim]DEMO_MODE=True -- set EIA_API_KEY and DEMO_MODE=False for live data.[/dim]")


@cli.command()
@click.argument("region", type=click.Choice(_REGION_CHOICES, case_sensitive=False))
@click.pass_context
def region(ctx: click.Context, region: str) -> None:
    """Show hourly stress timeline for a single REGION (CAL, TEX, MIDA, MIDW, NE, NY)."""
    print_banner()
    snapshots = build_snapshots(regions=[region], hours=ctx.obj["hours"])
    snaps = snapshots.get(region, [])
    if not snaps:
        console.print(f"[red]No data returned for {region}.[/red]")
        raise SystemExit(1)
    print_region_timeline(region, snaps)
    if DEMO_MODE:
        console.print("[dim]DEMO_MODE=True -- set EIA_API_KEY and DEMO_MODE=False for live data.[/dim]")


@cli.command()
@click.argument("target_region", metavar="REGION",
                type=click.Choice(_REGION_CHOICES, case_sensitive=False))
@click.pass_context
def brief(ctx: click.Context, target_region: str) -> None:
    """Generate a Claude stress-driver brief for REGION."""
    print_banner()
    snapshots = build_snapshots(regions=[target_region], hours=ctx.obj["hours"])
    snap = current_snapshot(snapshots.get(target_region, []))
    if snap is None:
        console.print(f"[red]No data for {target_region}.[/red]")
        raise SystemExit(1)
    console.print(f"[dim]Generating brief for {target_region} (stress={snap.stress_score:.1f}, tier={snap.tier})...[/dim]")
    text = generate_brief(snap)
    print_brief(target_region, text)


@cli.command()
@click.argument("target_region", metavar="REGION",
                type=click.Choice(_REGION_CHOICES, case_sensitive=False))
@click.option(
    "--scenario", "-s",
    type=click.Choice(_SCENARIO_CHOICES),
    default=None,
    help="Named scenario preset (wind_drop, solar_drop, demand_surge, polar_vortex).",
)
@click.option("--wind-pct", type=float, default=None,
              help="Wind generation change in pct (e.g. -20 for 20%% drop).")
@click.option("--solar-pct", type=float, default=None,
              help="Solar generation change in pct.")
@click.option("--demand-pct", type=float, default=None,
              help="Demand change in pct (e.g. +15 for 15%% surge).")
@click.pass_context
def scenario(
    ctx: click.Context,
    target_region: str,
    scenario: str | None,
    wind_pct: float | None,
    solar_pct: float | None,
    demand_pct: float | None,
) -> None:
    """
    What-if scenario analysis for REGION.

    \b
    Examples:
      scenario TEX --scenario wind_drop
      scenario CAL --wind-pct -20 --demand-pct 15
      scenario NE --scenario polar_vortex
    """
    print_banner()
    snapshots = build_snapshots(regions=[target_region], hours=ctx.obj["hours"])
    snap = current_snapshot(snapshots.get(target_region, []))
    if snap is None:
        console.print(f"[red]No data for {target_region}.[/red]")
        raise SystemExit(1)

    has_custom = any(v is not None for v in [wind_pct, solar_pct, demand_pct])

    if not has_custom and scenario is None:
        scenario = "wind_drop"

    if has_custom:
        name = scenario or "custom"
        result = run_scenario(
            snap, name,
            wind_pct=wind_pct or 0.0,
            solar_pct=solar_pct or 0.0,
            demand_pct=demand_pct or 0.0,
        )
    else:
        result = run_named_scenario(snap, scenario)

    print_scenario(result)

    if DEMO_MODE:
        console.print("[dim]DEMO_MODE=True -- set EIA_API_KEY and DEMO_MODE=False for live data.[/dim]")


@cli.command()
@click.option("--format", "fmt", type=click.Choice(["table", "json"]), default="table",
              show_default=True, help="Output format.")
@click.pass_context
def export(ctx: click.Context, fmt: str) -> None:
    """
    Export current-hour stress index in P20 joule format.

    Compatible with the joule DoD installation SMR suitability screener (P20).
    HIGH/CRITICAL regions signal higher SMR resilience value.
    """
    snapshots = build_snapshots(hours=ctx.obj["hours"])
    current_snaps = [
        s for region_snaps in snapshots.values()
        for s in [current_snapshot(region_snaps)]
        if s is not None
    ]
    joule_data = to_joule_format(current_snaps)
    if fmt == "json":
        print_json(joule_data)
    else:
        print_banner()
        print_joule_export(joule_data)


@cli.command()
@click.pass_context
def demo(ctx: click.Context) -> None:
    """
    Run all GridPulse commands against seeded demo data.
    No API keys required.
    """
    print_banner()
    console.rule("[bold]Demo 1: All-Region Dashboard[/bold]")
    snapshots = build_snapshots(hours=6)
    print_dashboard(snapshots)

    console.rule("[bold]Demo 2: Texas Hourly Timeline[/bold]")
    print_region_timeline("TEX", snapshots["TEX"])

    console.rule("[bold]Demo 3: Texas Stress Brief[/bold]")
    tex_snap = current_snapshot(snapshots["TEX"])
    if tex_snap:
        text = generate_brief(tex_snap, demo_mode=True)
        print_brief("TEX", text)

    console.rule("[bold]Demo 4: Wind Drop Scenario (Texas)[/bold]")
    if tex_snap:
        from scenarios import run_named_scenario
        result = run_named_scenario(tex_snap, "wind_drop")
        print_scenario(result)

    console.rule("[bold]Demo 5: Polar Vortex Scenario (New England)[/bold]")
    ne_snap = current_snapshot(snapshots["NE"])
    if ne_snap:
        result = run_named_scenario(ne_snap, "polar_vortex")
        print_scenario(result)
        ne_brief = generate_brief(ne_snap, demo_mode=True)
        print_brief("NE", ne_brief)

    console.rule("[bold]Demo 6: Joule Export (P20 Integration)[/bold]")
    current_snaps = [
        s for region_snaps in snapshots.values()
        for s in [current_snapshot(region_snaps)]
        if s is not None
    ]
    joule_data = to_joule_format(current_snaps)
    print_joule_export(joule_data)

    console.print("[dim]All demo output uses seeded data. Set DEMO_MODE=False for live EIA/NOAA data.[/dim]")


if __name__ == "__main__":
    cli()
