# Development Notes

## Project
ATG Comfort Calculator (no‑build React, single `index.html`).

## Repo
`https://github.com/pwahi/ATG_Comfort_calculator` (branch `main`)

## Current Features
- Local‑only web app in `index.html` (no build step).
- CSV header row detection even with extra rows.
- Decimal handling for comma format.
- Comfort tab:
  - Zone group filter
  - Resultant temperature zone dropdown
  - Comfort plot + summary table
- Loads tab:
  - Load view: Total building / Zone group / Single zone
  - Heating, Cooling, Lighting, Equipment (incl. Equipment Sensible Gain)
  - COP inputs (heating/cooling)
  - Load intensity plot (W/m²)
  - Load breakdown chart (kWh/m²)
  - Yearly kWh/m² table
- Excel export includes comfort summary + load summary.

## CSV Assumptions
- Column names include:
  - `Hour`
  - `External Temperature`
  - `{Zone} Resultant Temp (°C)`
  - `{Zone} Heating Load (W)`
  - `{Zone} Cooling Load (W)`
  - `{Zone} Lighting Gain (W)`
  - `{Zone} Equipment Gain (W)`
  - `{Zone} Equipment Sensible Gain (W)`
- Zone floor area row exists: `Zone Floor Area (m²)` (used for W/m²).

## Recent Changes
- Added handling for lighting/equipment + equipment sensible gain.
- Added COP inputs to loads.
- Loads breakdown chart and totals (kWh/m²).
- Grouped zones by name prefix (before numeric suffix).

## Known TODOs
- (Add any future tasks here)
