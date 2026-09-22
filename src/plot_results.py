"""Create compact comparison plots from a cleaned evaluation result CSV."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def collect(frame: pd.DataFrame, suffix: str, value_name: str) -> pd.DataFrame:
    columns = [column for column in frame.columns if column.endswith(suffix)]
    parts = []
    for column in columns:
        model = column[: -len(suffix)]
        part = pd.DataFrame({"model": model, value_name: pd.to_numeric(frame[column], errors="coerce")})
        parts.append(part.dropna())
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=["model", value_name])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    frame = pd.read_csv(args.input)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")

    distance = collect(frame, "_distance_km", "distance_km")
    if not distance.empty:
        cap = distance["distance_km"].quantile(0.95)
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.boxplot(data=distance[distance["distance_km"] <= cap], x="model", y="distance_km", ax=ax)
        ax.set(title="Geoparsing distance error (up to the 95th percentile)", xlabel="Model", ylabel="Distance error (km)")
        fig.tight_layout()
        fig.savefig(args.output_dir / "distance_boxplot.png", dpi=180)
        plt.close(fig)

    iou = collect(frame, "_iou", "iou")
    if not iou.empty:
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.boxplot(data=iou, x="model", y="iou", ax=ax, showfliers=False)
        ax.set(title="Bounding-box overlap", xlabel="Model", ylabel="IoU", ylim=(0, 1))
        fig.tight_layout()
        fig.savefig(args.output_dir / "iou_boxplot.png", dpi=180)
        plt.close(fig)


if __name__ == "__main__":
    main()

