from arduino.app_utils import *
import csv
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import requests
import math


import config as c

logger = Logger("DataManager")

class DataOrchestra:
    """Class to manage the data saving operations, both locally and online, for the garden monitoring system."""
    def __init__(self, garden, max_rows=c.rows_logged):
        """Initializes the DataOrchestra with a reference to the GardenState, the file path for local data storage, and the maximum number of rows to keep in the local CSV file."""
        self.garden = garden
        self.file_name = "sensors_data.csv"
        self.filepath = c.data_directory / self.file_name
        self.max_rows = max_rows
        self.rows_num = self._count_csv_rows()
        self.headers = ["Time"] + list(self.garden.keys) + ["label_1", "label_2", "label_3"]
        
        self.data = dict()
        
    def update_data(self):
        """Updates the data dictionary with the latest sensor readings from the GardenState in a thread-safe manner."""
        with self.garden.lock:
            self.data = self.garden.sensors_readings.copy()
            
    def _count_csv_rows(self):
        """Counts the number of rows in the local CSV file, excluding the header row."""
        if os.path.exists(self.filepath):
            with open(self.filepath, mode='r', newline='') as file:
                row_count = sum(1 for row in file)
                return max(0, row_count - 1)
        else:
            return 0
        
        
    def read_column_history(self, type_of_measure, rows_num):
        """Returns the historical values of a given column as floats, skipping NaNs.
        Rows that are missing the column or contain a value that cannot be parsed as
        a float (e.g. a truncated row from a crash mid-write) are skipped instead of
        raising, so a single corrupted row can't take down the decision loop."""

        lst_values = list()
        rows_counter = 0
        
        if os.path.exists(self.filepath):
            with open(self.filepath, mode='r', newline='') as file:
                data_dict = csv.DictReader(file)
                for row in data_dict:
                    if rows_counter <= rows_num:
                        elem = float(row[type_of_measure])
                        if not math.isnan(elem):
                            lst_values.append(elem)
                            rows_counter += 1
                    else:
                        break

        return lst_values
                        

    def save_online(self):
        """Saves the data online in google servers"""
        if not c.URL_APPSCRIPT:
            logger.warning("URL_APPSCRIPT is not set (missing environment variable); skipping online save.")
            return False
        try:
            self.update_data()
            response = requests.post(c.URL_APPSCRIPT, json = self.data, allow_redirects = True)
            
            if response.status_code == 200:
                logger.info("Data successfully sent to the server.")
                return True
            else:
                logger.error(f"Data failed to be sent to the server. Status code: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Error in the connection: {e}")

    def save_local(self):
        """Saves the data locally in a CSV file, maintaining a maximum number of rows as specified by max_rows."""
        try:
            self.update_data()
            now = datetime.now(ZoneInfo("Europe/Madrid")).strftime("%Y-%m-%d %H:%M:%S")
            labels = [f"{label}: {p}" for label, p in self.garden.predictions.items()]
            new_row = [now] + [self.data[key] for key in self.garden.keys] + labels
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

            logger.info(f"Data saved locally at {self.file_name}. Current number of rows: {self.rows_num}")
            
        except Exception as e:
            logger.error(f"Error saving data locally: {e}")
            