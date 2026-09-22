"""Compute point-distance and spherical bounding-box IoU metrics."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import pandas as pd


EARTH_RADIUS_KM = 6371.0088
TRUTH_POINT = ("lat_truth", "lon_truth")
TRUTH_BOX = ("bbox_nom_s", "bbox_nom_w", "bbox_nom_n", "bbox_nom_e")


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def spherical_rectangle_area_km2(south: float, west: float, north: float, east: float) -> float:
    """Surface area of a latitude-longitude rectangle on a sphere."""
    if south >= north or west >= east:
        return 0.0
    lat_factor = abs(math.sin(math.radians(north)) - math.sin(math.radians(south)))
    lon_width = math.radians(east - west)
    return EARTH_RADIUS_KM**2 * lat_factor * lon_width


def spherical_iou(truth: tuple[float, ...], predicted: tuple[float, ...]) -> float:
    ts, tw, tn, te = truth
    ps, pw, pn, pe = predicted
    if ts >= tn or tw >= te or ps >= pn or pw >= pe:
        return math.nan

    intersection = spherical_rectangle_area_km2(
        max(ts, ps), max(tw, pw), min(tn, pn), min(te, pe)
    )
    truth_area = spherical_rectangle_area_km2(ts, tw, tn, te)
    predicted_area = spherical_rectangle_area_km2(ps, pw, pn, pe)
    union = truth_area + predicted_area - intersection
    return intersection / union if union else math.nan


def model_prefixes(columns: list[str]) -> list[str]:
    return sorted(column[:-4] for column in columns if column.endswith("_lat") and column != "lat_truth")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    frame = pd.read_csv(args.input)
    required = set(TRUTH_POINT + TRUTH_BOX)
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Missing truth columns: {', '.join(sorted(missing))}")

    for prefix in model_prefixes(list(frame.columns)):
        point_cols = (f"{prefix}_lat", f"{prefix}_lon")
        box_cols = (f"{prefix}_south", f"{prefix}_west", f"{prefix}_north", f"{prefix}_east")
        if not set(point_cols + box_cols).issubset(frame.columns):
            continue

        def distance(row: pd.Series) -> float:
            values = [row[c] for c in TRUTH_POINT + point_cols]
            return haversine_km(*map(float, values)) if pd.notna(values).all() else math.nan

        def iou(row: pd.Series) -> float:
            values = [row[c] for c in TRUTH_BOX + box_cols]
            return spherical_iou(tuple(map(float, values[:4])), tuple(map(float, values[4:]))) if pd.notna(values).all() else math.nan

        frame[f"{prefix}_distance_km"] = frame.apply(distance, axis=1)
        frame[f"{prefix}_iou"] = frame.apply(iou, axis=1)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.output, index=False)


if __name__ == "__main__":
    main()
