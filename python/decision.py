"""Predicts the garden's next action from sensor readings and the visual anomaly score."""

import pandas as pd
import joblib

from arduino.app_utils import *

import config as c


logger = Logger("DecisionSystem")



class DecisionOrchestra:
    """Loads the trained model and predicts the garden's action every cycle."""

    def __init__(self, garden, data_orchestra, model_name=c.decision_model_name):
        self.garden = garden
        self.data_orchestra = data_orchestra
        self.model_path = c.decision_model_training_directory / model_name
        self.model = joblib.load(self.model_path)

    def predict(self):
        """Builds this cycle's features and stores the top-3 predictions in GardenState."""
        with self.garden.lock:
            reading = self.garden.sensors_readings.copy()
            max_anomaly = self.garden.image_readings["anomaly_max_score"]
        moist_history = self.data_orchestra.read_column_history("soil_moisture_(%)", c.THRESHOLDS["moist_baseline_window"])
        moisture_baseline = sum(moist_history) / len(moist_history) if moist_history else reading["soil_moisture_(%)"]
        predictor = [
            {  
            "soil_moisture_(%)": reading["soil_moisture_(%)"], "soil_moisture_baseline": moisture_baseline,
            "env_temperature_(°C)": reading["env_temperature_(°C)"], "env_humidity_(%)": reading["env_humidity_(%)"],
            "plants_temp_(°C)": reading["plants_temp_(°C)"], "plants_hum_(%)": reading["plants_hum_(%)"],
            "light_intensity_(lux)": reading["light_intensity_(lux)"], "power_(W)": reading["power_(W)"],
            "max_anomaly_detected": max_anomaly
            },
        ]
        df = pd.DataFrame(predictor)
        df["moisture_vs_baseline"] = df["soil_moisture_(%)"] - df["soil_moisture_baseline"]

        if df[c.FEATURES].isna().any(axis=None):
            # A failed sensor reading leaves NaN in the features; the model can't handle
            # that (and was never trained on this label), so skip prediction this cycle.
            with self.garden.lock:
                self.garden.predictions = {"INSUFFICIENT_DATA": "1.00"}
            logger.warning("Sensor reading incomplete this cycle (NaN in features); skipping model prediction.")
            return

        probs = self.model.predict_proba(df[c.FEATURES])
        
        raw_top = sorted(zip(self.model.classes_, probs[0]), key=lambda x: -x[1])[:3]
        clean_top = {f"{label}":f"{p:.2f}" for label, p in raw_top}
        with self.garden.lock:
            self.garden.predictions = clean_top

        logger.info(f"Predictions calculated: {clean_top}")
        

    