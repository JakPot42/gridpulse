"""Rich terminal dashboard — ASCII-safe for Windows cp1252 console."""
import json
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from stress_engine import RegionSnapshot
from scenarios import ScenarioResult
from config import REGIONS

console = Console()

TIER_COLORS = {
    "LOW":      "green",
    "ELEVATED": "yellow",
    "HIGH":     "red",
    "CRITICAL": "bold red",
}

_BANNER = """
[bold cyan]GridPulse[/bold cyan]  [dim]v1.0[/dim]
[dim]Regional grid stress index -- EIA demand + NOAA weather[/dim]
"""


def _bar(score: float, width: int = 20) -> str:
    filled = max(0, min(width, int(score / 100.0 * width)))
    return "#" * filled + "." * (width - filled)


def print_banner() -> None:
    console.print(_BANNER)


def print_dashboard(snapshots: dict[str, list[RegionSnapshot]]) -> None:
    """Print all-region stress overview for the current hour."""
    console.print()
    console.rule("[bold]Regional Grid Stress -- Current Hour[/bold]")
    console.print()
    console.print(f"  {'Region':<6}  {'Name':<14}  {'Score':>6}  {'Tier':<10}  Bar")
    console.print("  " + "-" * 60)
    for region, snaps in snapshots.items():
        if not snaps:
            continue
        snap = snaps[0]
        color = TIER_COLORS.get(snap.tier, "white")
        bar = _bar(snap.stress_score)
        console.print(
            f"  [bold]{region:<6}[/bold]  {REGIONS[region]['name']:<14}  "
            f"[{color}]{snap.stress_score:>6.1f}[/{color}]  "
            f"[{color}]{snap.tier:<10}[/{color}]  [{color}]{bar}[/{color}]"
        )
    console.print()


def print_region_timeline(region: str, snaps: list[RegionSnapshot]) -> None:
    """Print hourly timeline for a single region."""
    name = REGIONS[region]["name"]
    console.rule(f"[bold]{region} ({name}) -- Hourly Timeline[/bold]")
    console.print()
    console.print(
        f"  {'Hour':<6}  {'Score':>6}  {'Tier':<10}  {'Bar':<20}  "
        f"{'Demand':>8}  {'Solar':>6}  {'Wind':>6}"
    )
    console.print("  " + "-" * 78)
    for snap in snaps:
        color = TIER_COLORS.get(snap.tier, "white")
        bar = _bar(snap.stress_score)
        hour_label = snap.hour[11:13] + ":00" if len(snap.hour) >= 13 else snap.hour
        console.print(
            f"  {hour_label:<6}  "
            f"[{color}]{snap.stress_score:>6.1f}[/{color}]  "
            f"[{color}]{snap.tier:<10}[/{color}]  [{color}]{bar:<20}[/{color}]  "
            f"{snap.demand_mwh:>8,.0f}  {snap.solar_mwh:>6,.0f}  {snap.wind_mwh:>6,.0f}"
        )
    console.print()


def print_scenario(result: ScenarioResult) -> None:
    """Print base vs modified comparison for a what-if scenario."""
    snap = result.base
    mod = result.modified
    base_color = TIER_COLORS.get(snap.tier, "white")
    mod_color = TIER_COLORS.get(mod.tier, "white")

    console.rule(f"[bold]Scenario: {result.scenario}[/bold]")
    console.print()
    console.print(f"  Region : {snap.region} ({REGIONS[snap.region]['name']})")
    console.print(f"  Hour   : {snap.hour}")
    console.print()
    console.print(
        f"  Base    {_bar(snap.stress_score, 15)}  "
        f"[{base_color}]{snap.stress_score:>5.1f}  {snap.tier}[/{base_color}]"
    )
    console.print(
        f"  After   {_bar(mod.stress_score, 15)}  "
        f"[{mod_color}]{mod.stress_score:>5.1f}  {mod.tier}[/{mod_color}]"
    )
    console.print(f"  Delta   {result.delta_score:+.1f} points")
    if result.delta_tier:
        console.print(f"  [bold yellow]Tier escalation: {snap.tier} -> {mod.tier}[/bold yellow]")
    console.print()


def print_brief(region: str, text: str) -> None:
    console.print(Panel(
        text,
        title=f"[bold]GridPulse Brief -- {region}[/bold]",
        border_style="cyan",
    ))
    console.print()


def print_joule_export(joule_data: dict) -> None:
    """Print and return P20 joule-format export table."""
    console.rule("[bold]Joule Export -- P20 SMR Suitability Integration[/bold]")
    console.print("[dim]HIGH/CRITICAL stress signals higher SMR resilience value for DoD installations.[/dim]")
    console.print()

    t = Table(box=box.SIMPLE, show_header=True)
    t.add_column("Region")
    t.add_column("Score", justify="right")
    t.add_column("Tier")
    t.add_column("Net Load MWh", justify="right")
    t.add_column("Firm Cap MW", justify="right")
    t.add_column("Renewable %", justify="right")

    for region, data in sorted(joule_data.items()):
        color = TIER_COLORS.get(data["tier"], "white")
        t.add_row(
            region,
            f"{data['stress_score']:.1f}",
            f"[{color}]{data['tier']}[/{color}]",
            f"{data['net_load_mwh']:,.0f}",
            f"{data['firm_capacity_mw']:,.0f}",
            f"{data['renewable_pct']:.1f}%",
        )
    console.print(t)
    console.print()


def print_json(data: dict) -> None:
    console.print(json.dumps(data, indent=2))
