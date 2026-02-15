#!/usr/bin/env python3
"""ATG thermal comfort analysis from hourly simulation CSV data.

This script provides a pragmatic implementation of an adaptive comfort workflow
that can be used as a first iteration for ISSO 72 / Dutch ATG-style analyses.

Expected CSV columns (configurable via CLI):
- Timestamp
- Operative (or indoor air) temperature [°C]
- Outdoor temperature [°C]

Outputs:
- Console summary
- `comfort_hourly_results.csv` with per-hour comfort classification
- `comfort_monthly_summary.csv` with monthly comfort-hour KPIs
- `comfort_timeseries.png` time-series plot with comfort limits
- `comfort_monthly.png` monthly comfort-hour bars
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


@dataclass
class ATGConfig:
    """Configuration for comfort calculations.

    The default equations are adaptive-comfort style and can be tuned once
    project-specific ISSO 72 clauses are locked down.
    """

    alpha: float = 0.8  # exponentially weighted running-mean factor
    comfort_slope: float = 0.33
    comfort_intercept: float = 18.8
    deadband: float = 3.0


def compute_running_mean_outdoor(temp_outdoor: pd.Series, alpha: float = 0.8) -> pd.Series:
    """Compute exponentially weighted running-mean outdoor temperature.

    This is a common adaptive-comfort formulation:
      Trm_today = (T_{d-1} + alpha*T_{d-2} + ... ) / (1 + alpha + alpha^2 + ...)

    Implemented using a one-day shifted EWM on daily average outdoor temperature
    and then mapped back to each hour.
    """

    daily = temp_outdoor.resample("D").mean()
    shifted = daily.shift(1)
    trm_daily = shifted.ewm(alpha=(1 - alpha), adjust=True).mean()
    trm_hourly = trm_daily.reindex(temp_outdoor.index, method="ffill")
    return trm_hourly


def classify_comfort(df: pd.DataFrame, config: ATGConfig) -> pd.DataFrame:
    """Calculate comfort temperature and classify each hour."""

    out = df.copy()
    out["trm"] = compute_running_mean_outdoor(out["t_out"], alpha=config.alpha)
    out["t_comfort"] = config.comfort_slope * out["trm"] + config.comfort_intercept
    out["limit_low"] = out["t_comfort"] - config.deadband
    out["limit_high"] = out["t_comfort"] + config.deadband

    out["state"] = "comfortable"
    out.loc[out["t_op"] < out["limit_low"], "state"] = "too_cold"
    out.loc[out["t_op"] > out["limit_high"], "state"] = "too_warm"

    out["comfort_hour"] = (out["state"] == "comfortable").astype(int)
    out["discomfort_hour"] = 1 - out["comfort_hour"]
    return out


def monthly_summary(hourly: pd.DataFrame) -> pd.DataFrame:
    """Create monthly comfort KPIs."""

    grouped = hourly.groupby(pd.Grouper(freq="M"))
    summary = grouped.agg(
        total_hours=("comfort_hour", "count"),
        comfort_hours=("comfort_hour", "sum"),
        discomfort_hours=("discomfort_hour", "sum"),
        too_warm_hours=("state", lambda x: (x == "too_warm").sum()),
        too_cold_hours=("state", lambda x: (x == "too_cold").sum()),
        mean_t_op=("t_op", "mean"),
    )
    summary["comfort_pct"] = 100 * summary["comfort_hours"] / summary["total_hours"]
    return summary


def plot_timeseries(hourly: pd.DataFrame, output_path: Path) -> None:
    """Plot operative temperature with adaptive comfort limits."""

    plt.figure(figsize=(14, 5))
    plt.plot(hourly.index, hourly["t_op"], label="Operative temperature", linewidth=1)
    plt.plot(hourly.index, hourly["limit_low"], label="Comfort lower limit", linewidth=1)
    plt.plot(hourly.index, hourly["limit_high"], label="Comfort upper limit", linewidth=1)
    plt.ylabel("Temperature [°C]")
    plt.xlabel("Time")
    plt.title("Hourly temperature and adaptive comfort limits")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=180)
    plt.close()


def plot_monthly(summary: pd.DataFrame, output_path: Path) -> None:
    """Plot monthly comfort and discomfort hours."""

    month_labels = summary.index.strftime("%Y-%m")
    x = range(len(summary))

    plt.figure(figsize=(12, 5))
    plt.bar(x, summary["comfort_hours"], label="Comfort hours")
    plt.bar(x, summary["discomfort_hours"], bottom=summary["comfort_hours"], label="Discomfort hours")
    plt.xticks(x, month_labels, rotation=45, ha="right")
    plt.ylabel("Hours")
    plt.xlabel("Month")
    plt.title("Monthly thermal comfort hours")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=180)
    plt.close()


def load_and_prepare(csv_path: Path, timestamp_col: str, operative_col: str, outdoor_col: str) -> pd.DataFrame:
    """Load CSV and normalize to required columns and datetime index."""

    df = pd.read_csv(csv_path)
    missing = [c for c in [timestamp_col, operative_col, outdoor_col] if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in CSV: {missing}")

    df = df[[timestamp_col, operative_col, outdoor_col]].copy()
    df.columns = ["timestamp", "t_op", "t_out"]
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp", "t_op", "t_out"])
    df = df.sort_values("timestamp").set_index("timestamp")
    return df


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="ATG-style thermal comfort analysis from CSV")
    p.add_argument("csv", type=Path, help="Path to input CSV file")
    p.add_argument("--timestamp-col", default="timestamp", help="Timestamp column name")
    p.add_argument("--operative-col", default="t_op", help="Operative/indoor temperature column name")
    p.add_argument("--outdoor-col", default="t_out", help="Outdoor temperature column name")
    p.add_argument("--alpha", type=float, default=0.8, help="Running mean alpha factor")
    p.add_argument("--comfort-slope", type=float, default=0.33, help="Adaptive comfort slope")
    p.add_argument("--comfort-intercept", type=float, default=18.8, help="Adaptive comfort intercept")
    p.add_argument("--deadband", type=float, default=3.0, help="Comfort deadband ±[°C]")
    p.add_argument("--output-dir", type=Path, default=Path("results"), help="Output folder")
    return p


def main() -> None:
    args = build_arg_parser().parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    cfg = ATGConfig(
        alpha=args.alpha,
        comfort_slope=args.comfort_slope,
        comfort_intercept=args.comfort_intercept,
        deadband=args.deadband,
    )

    data = load_and_prepare(
        csv_path=args.csv,
        timestamp_col=args.timestamp_col,
        operative_col=args.operative_col,
        outdoor_col=args.outdoor_col,
    )
    hourly = classify_comfort(data, cfg)
    monthly = monthly_summary(hourly)

    hourly.to_csv(args.output_dir / "comfort_hourly_results.csv")
    monthly.to_csv(args.output_dir / "comfort_monthly_summary.csv")

    plot_timeseries(hourly, args.output_dir / "comfort_timeseries.png")
    plot_monthly(monthly, args.output_dir / "comfort_monthly.png")

    total_hours = int(hourly["comfort_hour"].count())
    comfort_hours = int(hourly["comfort_hour"].sum())
    pct = 100 * comfort_hours / total_hours if total_hours else 0

    print("ATG comfort analysis complete")
    print(f"Total hours: {total_hours}")
    print(f"Comfort hours: {comfort_hours}")
    print(f"Comfort percentage: {pct:.1f}%")
    print(f"Outputs written to: {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
