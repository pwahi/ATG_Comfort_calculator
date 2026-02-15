# ATG Comfort Calculator

This repository now includes a first implementation of an **ATG-style thermal comfort analysis** workflow for hourly thermal simulation outputs.

## What it does

Given a CSV file, the script will:

1. Read hourly timestamps, indoor/operative temperature, and outdoor temperature.
2. Compute a running-mean outdoor temperature.
3. Calculate adaptive comfort limits.
4. Determine for each hour whether it is:
   - `comfortable`
   - `too_warm`
   - `too_cold`
5. Report total comfort hours and monthly comfort KPIs.
6. Generate plots.

## Files

- `atg_comfort.py` – main analysis script
- `requirements.txt` – python dependencies

## Input CSV format

By default, the script expects these columns:

- `timestamp`
- `t_op` (operative / indoor temperature)
- `t_out` (outdoor temperature)

You can map different names using CLI options.

## Usage

```bash
python atg_comfort.py your_simulation.csv
```

Example with custom column names:

```bash
python atg_comfort.py simulation.csv \
  --timestamp-col DateTime \
  --operative-col ZoneOperativeTemp \
  --outdoor-col OutdoorDryBulb
```

## Outputs

The script creates a `results/` folder (or custom `--output-dir`) with:

- `comfort_hourly_results.csv`
- `comfort_monthly_summary.csv`
- `comfort_timeseries.png`
- `comfort_monthly.png`

## Notes on ATG/ISSO 72 alignment

This is a practical starting point with configurable parameters:

- running-mean factor `alpha`
- comfort equation slope/intercept
- comfort deadband

When your ISSO 72 project criteria are finalized, update the defaults in `ATGConfig` or pass project-specific values via CLI.
