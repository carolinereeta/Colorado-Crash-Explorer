"""Beginner-friendly descriptive analysis of the published CDOT aggregates.

Run from the repository root:
    python scripts/quick_insights.py

This script uses the already-derived CSVs, so it does NOT require 300 MB of raw Excel data.
It deliberately excludes the incomplete 2026 year and does not estimate crash risk.
"""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

import plotly.graph_objects as go

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "processed" / "annual.csv"
OUTPUT = ROOT / "docs" / "annual_comparison.html"

with INPUT.open(newline="", encoding="utf-8") as handle:
    records = list(csv.DictReader(handle))

# Keep only the five complete calendar years available in these uploads.
records = [r for r in records if 2021 <= int(r["year"]) <= 2025]

by_area: dict[str, list[dict]] = defaultdict(list)
for row in records:
    by_area[row["area"]].append(row)

print("\nCDOT crash listings | 2021–2025 | counts, not risk rates")
print("-" * 78)
for area, rows in by_area.items():
    rows.sort(key=lambda r: int(r["year"]))
    crashes = sum(int(r["crashes"]) for r in rows)
    fatalities = sum(int(r["fatal_crashes"]) for r in rows)
    injury = sum(int(r["injury_crashes"]) for r in rows)
    share = (100 * (injury + fatalities) / crashes) if crashes else 0
    first, last = int(rows[0]["crashes"]), int(rows[-1]["crashes"])
    change = (100 * (last - first) / first) if first else 0
    print(f"{area:20} | crashes: {crashes:>8,} | injury/fatal crash share: {share:5.1f}% | 2021→2025: {change:+5.1f}%")

fig = go.Figure()
for area, rows in by_area.items():
    # Use separate panels later if comparing magnitudes; city is nested in county/state.
    # Indexing each 2021 series to 100 makes the shape of the trends comparable.
    baseline = int(rows[0]["crashes"])
    fig.add_trace(go.Scatter(
        x=[int(r["year"]) for r in rows],
        y=[round(100 * int(r["crashes"]) / baseline, 1) for r in rows],
        mode="lines+markers",
        name=area,
        hovertemplate="Year %{x}<br>Index %{y:.1f} (2021=100)<extra>%{fullData.name}</extra>",
    ))
fig.update_layout(
    title="Reported crash trends, indexed to 2021 = 100",
    xaxis_title="Year", yaxis_title="Crash count index (2021=100)",
    template="plotly_white", hovermode="x unified",
)
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
fig.write_html(OUTPUT, include_plotlyjs="cdn")
print(f"\nWrote interactive example chart: {OUTPUT}")
print("Reminder: changes in reported crash counts are not changes in exposure-adjusted risk.")
