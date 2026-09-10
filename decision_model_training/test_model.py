import sys
import joblib
import pandas as pd

from pathlib import Path

sys.path.insert(0, "../python")
from generate_synthetic_data import SyntheticDataGenerator

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python"))
import config as c  # noqa: E402

model = joblib.load(c.decision_model_name)

#EXAMPLE
samples = [
    {  
        "soil_moisture_(%)": 79, "soil_moisture_baseline": 80,
        "env_temperature_(°C)": 25, "env_humidity_(%)": 80,
        "plants_temp_(°C)": 27, "plants_hum_(%)": 50,
        "light_intensity_(lux)": 0.0, "power_(W)": 4,
    },
]

df = pd.DataFrame(samples)
df["moisture_vs_baseline"] = df["soil_moisture_(%)"] - df["soil_moisture_baseline"]

preds = model.predict(df[c.FEATURES])
probs = model.predict_proba(df[c.FEATURES])

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