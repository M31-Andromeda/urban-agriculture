import math
import sys
import pandas as pd
from pathlib import Path

from arduino.app_utils import *

import config as c


logger = Logger("DecisionSystem")


class DecisionOrquestra:
    def __init__(self, garden, data_orchestra, model=None):
        self.garden = garden
        self.data_orchestra = data_orchestra
        self.model_path = Path(__file__).resolve().parent.parent / "training" / model

    def decide(self) -> str:
        """Rule engine's vote for now; will combine with self.model once trained."""
        with self.garden.lock:
            reading = self.garden.sensors_readings.copy()
        moist_history = self.data_orchestra.read_column_history("soil_moisture_(%)")
        
        
        moisture_baseline = None
        
        predictors = [
        {  
            "soil_moisture_(%)": reading["soil_moisture_(%)"], "soil_moisture_baseline": moisture_baseline,
            "env_temperature_(°C)": reading["env_temperature_(°C)"], "env_humidity_(%)": reading["env_humidity_(%)"],
            "plants_temp_(°C)": reading["plants_temp_(°C)"], "plants_hum_(%)": reading["plants_hum_(%)"],
            "light_intensity_(lux)": reading["light_intensity_(lux)"], "power_(W)": reading["power_(W)"],
        },
        ]



        return 

    