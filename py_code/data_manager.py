from arduino.app_utils import *
import csv
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import requests 
import json


import config as c


class DataOrchestra:
    def __init__(self, garden, max_rows=c.rows_logged):
        self.garden = garden
        
        self.filepath = c.data_directory / "sensors_data.csv"
        self.max_rows = max_rows

        
        self.headers = ["Time"] + list(self.garden.keys)
        
        self.data = dict()
        
    def actualize_data(self):
        """Updates the data stored in GardenState, asumes that the data is already updated"""
        with self.garden.lock:
            self.data = self.garden.sensors_readings.copy()

    def save_online(self):
        """Saves the data stored in GardenState, asumes that the data is already updated"""

        try:
            self.actualize_data()
            response = requests.post(c.URL_APPSCRIPT, json = self.data, allow_redirects = True)

        except Exception as e:
            print("Error en la conexión:", e)

    def save_local(self):
        rows = []
        
        if os.path.exists(self.filepath):
            with open(self.filepath, mode='r', newline='') as file:
                reader = csv.reader(file)
                next(reader, None) 
                for row in reader:
                    rows.append(row)

        now = datetime.now(ZoneInfo("Europe/Madrid")).strftime("%Y-%m-%d %H:%M:%S")
        self.actualize_data()
        rows.append([now] + [self.data[key] for key in self.garden.keys])
        
        if len(rows) > self.max_rows:
            rows = rows[-self.max_rows:]
            
        with open(self.filepath, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(self.headers)
            writer.writerows(rows)
            