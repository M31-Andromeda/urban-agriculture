"""
Synthetic training-data generator for the Urban Agriculture decision system.

Not part of the deployed App (lives outside python/ on purpose) — this is dataset
prep tooling for training the RandomForest/XGBoost model that will eventually be
combined with decision_sys.labeler()'s rule-based vote.

Deliberately simple: it samples the raw readings decision_sys.labeler() actually
consumes, plus a short recent-history window for soil_moisture (the only variable
judged relative to itself), and calls the real labeler() to produce the label.
No parallel reimplementation of the bound-calculation logic — decision_sys stays
the single source of truth for what counts as "low" or "high".

Output: training/synthetic_dataset.csv — kept separate from data/ (real,
board-collected readings) so synthetic and real data are never mixed by accident.
"""

import csv
import random
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python"))

import config as c  # noqa: E402
from decision_sys import DecisionOrquestra  # noqa: E402

RNG_SEED = 42
N_SAMPLES = 4000
OUTPUT_PATH = Path(__file__).resolve().parent / "synthetic_dataset.csv"


def sample_moist_history(rng):
    """A short recent-history window around a random baseline — exactly what
    decision_sys._moisture_bounds needs to compute its rolling average."""
    window = c.THRESHOLDS["moist_baseline_window"]
    baseline = rng.uniform(10, 95)
    return [max(0.0, min(100.0, baseline + rng.gauss(0, 3))) for _ in range(window)]


def sample_light(rng):
    """Daytime bucket proportions and the exact saturation ceiling (157285.8)
    come from the real board's historical_sensor_data.csv, not a guess: the
    sensor spends most sunny hours pegged at that exact value rather than
    climbing further."""
    r = rng.random()
    if r < 0.19:
        return rng.uniform(1, 9999)          # low light / overcast (~19% of daytime)
    if r < 0.38:
        return rng.uniform(10000, 49999)     # normal daylight (~19%)
    if rng.random() < 0.68:
        return 157285.8                      # saturated (~62% of daytime, mostly at the real ceiling)
    return rng.uniform(50000, 157285.8)


def sample_reading(rng, moist_history):
    is_night = rng.random() < 0.35
    light = 0.0 if is_night else sample_light(rng)

    if is_night:
        power = 0.0
    elif rng.random() < 0.05:
        power = rng.uniform(0.0, 0.15)  # brownout / panel covered / disconnected
    else:
        # Daytime power roughly tracks light on a solar-charged system, plus noise.
        power = max(0.0, (light / 157285.8) * rng.uniform(4.5, 6.0) + rng.gauss(0, 0.4))

    baseline = sum(moist_history) / len(moist_history)
    # Usually near its own baseline (+/- noise) so most rows are "normal";
    # sometimes a clear excursion to cover the low/high cases.
    if rng.random() < 0.6:
        moisture = max(0.0, min(100.0, baseline + rng.gauss(0, 5)))
    else:
        moisture = rng.uniform(0, 100)

    env_temp = rng.uniform(5, 45)
    env_hum = rng.uniform(15, 95)
    # Leaf temperature/humidity track the surrounding air closely (transpiration
    # keeps them within a few degrees/points of it) -- not independent variables.
    plants_temp = max(0.0, min(50.0, env_temp + rng.gauss(-1.5, 2.0)))
    plants_hum = max(0.0, min(100.0, env_hum + rng.gauss(5.0, 8.0)))

    return {
        "soil_moisture_(%)": round(moisture, 2),
        "env_temperature_(°C)": round(env_temp, 2),
        "env_humidity_(%)": round(env_hum, 2),
        "plants_temp_(°C)": round(plants_temp, 2),
        "plants_hum_(%)": round(plants_hum, 2),
        "light_intensity_(lux)": round(light, 2),
        "power_(W)": round(power, 2),
    }


def build_row(rng, decision_orchestra):
    moist_history = sample_moist_history(rng)
    reading = sample_reading(rng, moist_history)

    if rng.random() < 0.03:  # missing/faulty sensor -> INSUFFICIENT_DATA
        reading[rng.choice(list(reading.keys()))] = float("nan")

    label = decision_orchestra.labeler(reading, moist_history)

    row = dict(reading)
    row["soil_moisture_baseline"] = round(sum(moist_history) / len(moist_history), 2)
    row["label"] = label
    return row


def main():
    rng = random.Random(RNG_SEED)

    # DecisionOrquestra only needs .labeler() here, which doesn't touch
    # garden/data_orchestra, so passing None for both is safe.
    decision_orchestra = DecisionOrquestra(garden=None, data_orchestra=None)

    rows = [build_row(rng, decision_orchestra) for _ in range(N_SAMPLES)]

    with open(OUTPUT_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    counts = Counter(r["label"] for r in rows)
    print(f"Wrote {len(rows)} rows to {OUTPUT_PATH}")
    print("Label distribution:")
    for label, count in counts.most_common():
        print(f"  {label:28s} {count:5d}  ({100 * count / len(rows):.1f}%)")


if __name__ == "__main__":
    main()
