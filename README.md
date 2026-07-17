# GridPulse

CLI tool that fuses EIA electricity demand/generation data with NOAA weather forecasts into a regional grid stress index.

```
  Region  Name             Score  Tier        Bar
  CAL     California         3.8  LOW         ....................
  TEX     Texas             64.8  HIGH        ############........
  MIDA    Mid-Atlantic      35.5  ELEVATED    #######.............
  NE      New England       54.5  HIGH        ##########..........
```

## What it does

- Pulls EIA API hourly demand and generation mix (solar, wind, gas, nuclear, coal) by region
- Pulls NOAA hourly weather forecasts (temperature, wind speed, cloud cover)
- Computes a stress index per region per hour: `score = clamp((net_load / firm_capacity - 0.6) / 0.4 * 100, 0, 100)`
- Four alert tiers: **LOW** [0-25) / **ELEVATED** [25-50) / **HIGH** [50-75) / **CRITICAL** [75-100]
- What-if scenarios: "what if wind drops 20%?", "polar vortex demand surge"
- Claude Haiku brief explaining what's driving a stress spike in plain language
- Joule export: outputs stress index in format compatible with **joule** DoD SMR suitability screener

## Regions

| Code | Region | Firm Capacity |
|---|---|---|
| CAL | California | 52 GW |
| TEX | Texas | 71 GW |
| MIDA | Mid-Atlantic | 64 GW |
| MIDW | Midwest | 78 GW |
| NE | New England | 28 GW |
| NY | New York | 38 GW |

## Setup

```bash
cd gridpulse
cp .env.example .env
# EIA_API_KEY: free key at eia.gov/opendata (optional — DEMO_MODE=True works without it)
# ANTHROPIC_API_KEY: optional, only for live Claude briefs
pip install -r requirements.txt
```

## Usage

```bash
# All-region stress overview at current hour
python main.py dashboard

# Hourly timeline for a single region
python main.py region NE
python main.py region TEX

# Claude stress-driver brief for a region
python main.py brief TEX

# What-if scenario analysis
python main.py scenario TEX --scenario wind_drop
python main.py scenario NE --scenario polar_vortex
python main.py scenario CAL --wind-pct -20 --demand-pct 15

# Export stress index in joule format (DoD SMR suitability integration)
python main.py export
python main.py export --format json

# Run all demo commands (no API keys needed)
python main.py demo

# Control number of hours shown (default: 6)
python main.py --hours 12 region TEX
```

## Scenarios

| Name | Description |
|---|---|
| `wind_drop` | Wind falls 20% (calm weather, turbine curtailment) |
| `solar_drop` | Solar falls 30% (cloud cover, haze) |
| `demand_surge` | Demand rises 15% (heat wave peak) |
| `polar_vortex` | Demand up 25% + wind down 10% (winter storm) |

Custom modifiers: `--wind-pct`, `--solar-pct`, `--demand-pct` accept any float.

## Stress formula

```
net_load = demand_mwh - solar_mwh - wind_mwh
score = clamp((net_load / firm_capacity_mw - 0.6) / 0.4 * 100, 0, 100)
```

- **score = 0**: firm capacity at 60% utilization — comfortable reserve
- **score = 50**: firm capacity at 80% utilization — elevated but manageable
- **score = 100**: firm capacity at 100%+ — crisis conditions

## joule integration

GridPulse's stress index is the grid-side input the **joule** DoD installation SMR suitability screener needs. A DoD installation in a HIGH or CRITICAL stress region has higher SMR value as a resilience asset — the regional grid cannot absorb additional demand disruption.

```bash
# Export in joule-compatible format
python main.py export --format json > gridpulse_joule.json
```

Output structure:
```json
{
  "TEX": {
    "stress_score": 64.8,
    "tier": "HIGH",
    "net_load_mwh": 61000.0,
    "firm_capacity_mw": 71000.0,
    "demand_mwh": 68000.0,
    "renewable_pct": 10.3,
    "hour": "2026-06-23T14"
  }
}
```

## Data sources

- **EIA API v2** (`api.eia.gov/v2`) — electricity demand and generation mix. Free API key required for live data.
- **NOAA API** (`api.weather.gov`) — hourly weather forecasts. No API key required.
- **DEMO_MODE=True** (default): all data comes from pre-seeded values matching summer peak conditions across all 6 regions.

## Tests

```bash
python -m pytest tests/ -v
```

221 tests covering stress formula math (boundary conditions, clamping, tier thresholds), scenario modifiers, seed data integrity, API client demo mode, and full pipeline merge.

## Honest limitations

- Firm capacity values are estimates, not live NERC data
- NOAA cloud cover is parsed from text forecast, not measured
- Stress formula uses a single reserve threshold (60%) for all regions; real grid operators use region-specific reliability standards
- In DEMO_MODE, data is static — use live EIA + NOAA for real-time conditions
