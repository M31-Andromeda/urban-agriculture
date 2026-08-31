from arduino.app_utils import *
import csv
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import config as c


# --- DEPARTAMENTO 5: GESTIÓN DE DATOS ---
class DataOrchestra:
    def __init__(self, garden, max_rows=c.rows_logged):
        self.garden = garden
        
        self.filepath = c.data_directory / "sensors_data.csv"
        self.max_rows = max_rows
        self.headers = [
            "Time", "Env_temperature", "Env_Humidity", "Pressure",
            "Air_Quality_(VOC)", "Soil_Moisture", "Inside_Temperature", "Inside_Humidity",
            "Light_intensity", "IR", "Solar_Current", "Solar_Voltage"
        ]

    def save_local(self):
        rows = []
        
        if os.path.exists(self.filepath):
            with open(self.filepath, mode='r', newline='') as file:
                reader = csv.reader(file)
                next(reader, None) 
                for row in reader:
                    rows.append(row)

        now = datetime.now(ZoneInfo("Europe/Madrid")).strftime("%Y-%m-%d %H:%M:%S")
        
        with self.garden.lock:
            new_row = [
                now,
                self.garden.env_temp,
                self.garden.env_hum,
                self.garden.pressure,
                self.garden.air_quality,
                self.garden.moist_soil,
                self.garden.in_temp,
                self.garden.in_hum,
                self.garden.amb_light,
                self.garden.ir,
                self.garden.current,
                self.garden.voltage
            ]
            
        rows.append(new_row)
        
        if len(rows) > self.max_rows:
            rows = rows[-self.max_rows:]
            
        with open(self.filepath, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(self.headers)
            writer.writerows(rows)
            