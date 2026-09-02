from arduino.app_utils import *
import csv
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import requests 


import config as c


class DataOrchestra:
    def __init__(self, garden, max_rows=c.rows_logged):
        self.garden = garden
        self.filepath = c.data_directory / "sensors_data.csv"
        self.max_rows = max_rows
        self.rows_num = self._count_csv_rows()
        self.headers = ["Time"] + list(self.garden.keys)
        
        self.data = dict()
        
    def update_data(self):
        """Updates the data stored in GardenState, asumes that the data is already updated"""
        with self.garden.lock:
            self.data = self.garden.sensors_readings.copy()
            
    def _count_csv_rows(self):
        if os.path.exists(self.filepath):
            with open(self.filepath, mode='r', newline='') as file:
                row_count = sum(1 for row in file)
                return max(0, row_count - 1)
        else:
            return 0

    def save_online(self):
        """Saves the data stored in GardenState, asumes that the data is already updated"""
        try:
            self.update_data()
            response = requests.post(c.URL_APPSCRIPT, json = self.data, allow_redirects = True, timeout = 20)

        except Exception as e:
            print("Error en la conexión:", e)

    def save_local(self):
        self.update_data()
        now = datetime.now(ZoneInfo("Europe/Madrid")).strftime("%Y-%m-%d %H:%M:%S")
        new_row = [now] + [self.data[key] for key in self.garden.keys]
        file_exists = os.path.exists(self.filepath)
        
        if file_exists and self.rows_num >= self.max_rows:
            with open(file=self.filepath, mode='r', newline="") as file:
                rows = list(csv.reader(file))[-(self.max_rows - 1):]
                rows.append(new_row)
                
            with open(self.filepath, mode='w', newline="") as file:
                writer = csv.writer(file)
                writer.writerow(self.headers)
                writer.writerows(rows)
                
        else:
            with open(file=self.filepath, mode='a', newline="") as file:
                writer = csv.writer(file)
                if not file_exists:
                    writer.writerow(self.headers)    
                writer.writerow(new_row)
            
            self.rows_num += 1
            