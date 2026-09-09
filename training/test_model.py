import sys

import joblib
import pandas as pd

sys.path.insert(0, "../python")
from generate_synthetic_data import SyntheticDataGenerator

model = joblib.load("moisture_decision_model.joblib")

FEATURES = [
    "soil_moisture_(%)", "soil_moisture_baseline", "moisture_vs_baseline",
    "env_temperature_(°C)", "env_humidity_(%)",
    "plants_temp_(°C)", "plants_hum_(%)",
    "light_intensity_(lux)", "power_(W)",
]

samples = [
    {  
        "soil_moisture_(%)": 60, "soil_moisture_baseline": 80,
        "env_temperature_(°C)": 38, "env_humidity_(%)": 40.0,
        "plants_temp_(°C)": 37, "plants_hum_(%)": 50,
        "light_intensity_(lux)": 40000.0, "power_(W)": 4,
    },
]

df = pd.DataFrame(samples)
df["moisture_vs_baseline"] = df["soil_moisture_(%)"] - df["soil_moisture_baseline"]

preds = model.predict(df[FEATURES])
probs = model.predict_proba(df[FEATURES])

d = SyntheticDataGenerator()

for i, sample in enumerate(samples):
    rule_label = d.labeler(sample)

    print(f"\n--- muestra {i} ---")
    print("regla (labeler):", rule_label)
    print("modelo (predict):", preds[i])
    top3 = sorted(zip(model.classes_, probs[i]), key=lambda x: -x[1])[:3]
    print("top-3 probabilidades del modelo:")
    for label, p in top3:
        print(f"  {label:28s} {p:.2f}")