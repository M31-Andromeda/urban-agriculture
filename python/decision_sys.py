
import pandas as pd
import joblib
from pathlib import Path

from arduino.app_utils import *

import config as c


logger = Logger("DecisionSystem")



class DecisionOrquestra:
    def __init__(self, garden, data_orchestra, model_name=c.decision_model_name):
        self.garden = garden
        self.data_orchestra = data_orchestra
        self.model_path = Path(__file__).resolve().parent.parent / "training" / model_name
        self.model = joblib.load(self.model_path)

    def decide(self):
        with self.garden.lock:
            reading = self.garden.sensors_readings.copy()
        moist_history = self.data_orchestra.read_column_history("soil_moisture_(%)", c.THRESHOLDS["moist_baseline_window"])
        
        # No history yet (e.g. first run): fall back to the current reading itself,
        # so moisture_vs_baseline is 0 instead of comparing against an arbitrary value.
        moisture_baseline = sum(moist_history) / len(moist_history) if moist_history else reading["soil_moisture_(%)"]
        
        predictor = [
            {  
            "soil_moisture_(%)": reading["soil_moisture_(%)"], "soil_moisture_baseline": moisture_baseline,
            "env_temperature_(°C)": reading["env_temperature_(°C)"], "env_humidity_(%)": reading["env_humidity_(%)"],
            "plants_temp_(°C)": reading["plants_temp_(°C)"], "plants_hum_(%)": reading["plants_hum_(%)"],
            "light_intensity_(lux)": reading["light_intensity_(lux)"], "power_(W)": reading["power_(W)"],
            },
        ]

        df = pd.DataFrame(predictor)
        df["moisture_vs_baseline"] = df["soil_moisture_(%)"] - df["soil_moisture_baseline"]

        probs = self.model.predict_proba(df[c.FEATURES])
        
        raw_top = sorted(zip(self.model.classes_, probs[0]), key=lambda x: -x[1])[:3]
        self.garden.predictions = {f"{label}":f"{p:.2f}" for label, p in raw_top}
        

    