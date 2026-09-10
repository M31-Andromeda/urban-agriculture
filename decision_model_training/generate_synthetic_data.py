import csv
import math
import random
import sys
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python"))
import config as c  # noqa: E402

SEED = 15
N_SAMPLES = 4000
OUTPUT_PATH = Path(__file__).resolve().parent / "synthetic_dataset.csv"


class SyntheticDataGenerator:
    def __init__(self, rng_seed=SEED, n_samples=N_SAMPLES, output_path=OUTPUT_PATH):
        self.rng = random.Random(rng_seed)
        self.n_samples = n_samples
        self.output_path = output_path

    def sample_light(self):
        # Bucket proportions and the 157285.8 ceiling come from the real board's
        # historical_sensor_data.csv: sunny hours peg at that exact value.
        r = self.rng.random()
        if r < 0.19:
            return self.rng.uniform(1, 9999)
        if r < 0.38:
            return self.rng.uniform(10000, 49999)
        if self.rng.random() < 0.68:
            return 157285.8
        return self.rng.uniform(50000, 157285.8)

    def sample_reading(self):
        is_night = self.rng.random() < 0.35
        light = 0.0 if is_night else self.sample_light()

        if is_night:
            power = 0.0
        elif self.rng.random() < 0.05:
            power = self.rng.uniform(0.0, 0.15)
        else:
            power = max(0.0, (light / 157285.8) * self.rng.uniform(4.5, 6.0) + self.rng.gauss(0, 0.4))

        moist_baseline = self.rng.uniform(10, 95)
        if self.rng.random() < 0.6:
            moisture = max(0.0, min(100.0, moist_baseline + self.rng.gauss(0, 5)))
        else:
            moisture = self.rng.uniform(0, 100)

        env_temp = self.rng.uniform(5, 45)
        env_hum = self.rng.uniform(15, 95)
        plants_temp = max(0.0, min(50.0, env_temp + self.rng.gauss(-1.5, 2.0)))
        plants_hum = max(0.0, min(100.0, env_hum + self.rng.gauss(5.0, 8.0)))

        return {
            "soil_moisture_(%)": round(moisture, 2),
            "env_temperature_(°C)": round(env_temp, 2),
            "env_humidity_(%)": round(env_hum, 2),
            "plants_temp_(°C)": round(plants_temp, 2),
            "plants_hum_(%)": round(plants_hum, 2),
            "light_intensity_(lux)": round(light, 2),
            "power_(W)": round(power, 2),
            "soil_moisture_baseline": round(moist_baseline, 2),
        }

    def moisture_bounds(self, baseline):
        margin = c.THRESHOLDS["moist_baseline_margin_pct"]
        return baseline - margin, baseline + margin

    def labeler(self, reading) -> str:
        moisture = reading["soil_moisture_(%)"]
        env_temp = reading["env_temperature_(°C)"]
        env_hum = reading["env_humidity_(%)"]
        plants_temp = reading["plants_temp_(°C)"]
        plants_hum = reading["plants_hum_(%)"]
        light = reading["light_intensity_(lux)"]
        power = reading["power_(W)"]
        baseline = reading["soil_moisture_baseline"]

        values = [moisture, env_temp, env_hum, plants_temp, plants_hum, light, power, baseline]
        if any(isinstance(v, float) and math.isnan(v) for v in values):
            return "INSUFFICIENT_DATA"

        moist_low, moist_high = self.moisture_bounds(baseline)
        env_temp_low, env_temp_high = c.THRESHOLDS["env_temp_low"], c.THRESHOLDS["env_temp_high"]
        plants_temp_low, plants_temp_high = c.THRESHOLDS["plants_temp_low"], c.THRESHOLDS["plants_temp_high"]
        is_night = light < c.THRESHOLDS["light_night_lux"]

        if moisture < moist_low or moisture < c.THRESHOLDS["moist_absolute_floor_pct"]:
            if power < (c.THRESHOLDS["pumps_max_consum"] + c.THRESHOLDS["uno_q_consum"]):
                return "NOT_ABLE_TO_WATER"
            return "WATER"

        if moisture > moist_high:
            if (env_hum > c.THRESHOLDS["env_humidity_fungal_high"] or plants_hum > c.THRESHOLDS["plants_humidity_fungal_high"]) or is_night:
                return "FUNGI_ALERT_EXCESS_WATER"
            return "EXCESS_WATER"

        if env_temp > env_temp_high and env_hum < c.THRESHOLDS["env_humidity_stress_low"]:
            return "HYDRIC_STRESS_ALERT"

        if env_temp > env_temp_high or plants_temp > plants_temp_high:
            if power < (c.THRESHOLDS["fans_max_consum"] + c.THRESHOLDS["uno_q_consum"]):
                return "NOT_ABLE_TO_VENTILATE"
            return "VENTILATE"

        if env_temp < env_temp_low or plants_temp < plants_temp_low:
            return "LOW_TEMP_ALERT"

        if 0 < light < c.THRESHOLDS["light_low_lux"]:
            return "LOW_LIGHT"

        if is_night:
            return "NIGHT_OK"
        
        return "OK"

    def build_row(self):
        reading = self.sample_reading()
        if self.rng.random() < 0.03:
            reading[self.rng.choice(list(reading.keys()))] = float("nan")
        reading["label"] = self.labeler(reading)
        return reading

    def main(self):
        rows = [self.build_row() for _ in range(self.n_samples)]

        with open(self.output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

        counts = Counter(r["label"] for r in rows)
        print(f"Wrote {len(rows)} rows to {self.output_path}")
        print("Label distribution:")
        for label, count in counts.most_common():
            print(f"  {label:28s} {count:5d}  ({100 * count / len(rows):.1f}%)")


if __name__ == "__main__":
    SyntheticDataGenerator().main()
