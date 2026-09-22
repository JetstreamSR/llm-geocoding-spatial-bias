"""Run blind LLM geoparsing from addresses.

Reference coordinates or bounding boxes may be present in the input CSV, but this
module deliberately sends only the address field to each model.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from typing import Any

import pandas as pd


SYSTEM_PROMPT = (
    "You are a geoparsing assistant. Return valid JSON only, with the keys "
    "lat, lon, south, west, north, and east. Values must be decimal degrees."
)

MODEL_CONFIG = {
    "gpt-3.5-turbo": ("openai", "gpt-3.5-turbo"),
    "gpt-4": ("openai", "gpt-4"),
    "deepseek": ("deepseek", None),
}

FIELDS = ("lat", "lon", "south", "west", "north", "east")


def load_env_file(path: Path = Path(".env")) -> None:
    """Load simple KEY=VALUE entries without overwriting existing variables."""
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def build_clients() -> dict[str, Any]:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("Install the project dependencies before querying models") from exc

    clients: dict[str, Any] = {}
    if key := os.getenv("OPENAI_API_KEY"):
        clients["openai"] = OpenAI(api_key=key)
    if key := os.getenv("DEEPSEEK_API_KEY"):
        clients["deepseek"] = OpenAI(api_key=key, base_url="https://api.deepseek.com")
    return clients


def parse_prediction(content: str) -> dict[str, float]:
    start, end = content.find("{"), content.rfind("}")
    if start < 0 or end < start:
        raise ValueError("The response did not contain a JSON object")
    raw: dict[str, Any] = json.loads(content[start : end + 1])
    result = {field: float(raw[field]) for field in FIELDS}
    if not -90 <= result["lat"] <= 90 or not -180 <= result["lon"] <= 180:
        raise ValueError("Predicted coordinates are outside valid ranges")
    if result["south"] > result["north"] or result["west"] > result["east"]:
        raise ValueError("Predicted bounding-box coordinates are not ordered")
    return result


def predict(client: Any, model: str, address: str) -> dict[str, float]:
    prompt = (
        f"Geoparse this place description: {address}\n"
        'Return {"lat": number, "lon": number, "south": number, '
        '"west": number, "north": number, "east": number}.'
    )
    response = client.chat.completions.create(
        model=model,
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )
    return parse_prediction(response.choices[0].message.content or "")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--models", nargs="+", choices=sorted(MODEL_CONFIG), required=True)
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--retries", type=int, default=3)
    args = parser.parse_args()

    load_env_file()
    runtime_config = dict(MODEL_CONFIG)
    if deepseek_model := os.getenv("DEEPSEEK_MODEL"):
        runtime_config["deepseek"] = ("deepseek", deepseek_model)

    clients = build_clients()
    frame = pd.read_csv(args.input)
    if "address" not in frame.columns:
        raise ValueError("Input CSV must contain an 'address' column")

    missing = sorted({runtime_config[m][0] for m in args.models} - clients.keys())
    if missing:
        raise RuntimeError(f"Missing API credentials for: {', '.join(missing)}")
    if "deepseek" in args.models and not runtime_config["deepseek"][1]:
        raise RuntimeError("Set DEEPSEEK_MODEL to an explicit DeepSeek API model identifier")

    rows: list[dict[str, Any]] = []
    for index, source in frame.iterrows():
        output = source.to_dict()
        for public_name in args.models:
            provider, api_model = runtime_config[public_name]
            assert api_model is not None
            prefix = public_name.replace(".", "").replace("-", "_")
            output[f"{prefix}_model"] = api_model
            last_error = ""
            for attempt in range(args.retries):
                try:
                    prediction = predict(clients[provider], api_model, str(source["address"]))
                    output.update({f"{prefix}_{key}": value for key, value in prediction.items()})
                    output[f"{prefix}_error"] = ""
                    break
                except Exception as exc:  # keep a row-level audit trail
                    last_error = str(exc)
                    if attempt + 1 < args.retries:
                        time.sleep(args.delay)
            else:
                output.update({f"{prefix}_{key}": None for key in FIELDS})
                output[f"{prefix}_error"] = last_error
        rows.append(output)
        pd.DataFrame(rows).to_csv(args.output, index=False)
        print(f"Saved {index + 1}/{len(frame)}")
        time.sleep(args.delay)


if __name__ == "__main__":
    main()
