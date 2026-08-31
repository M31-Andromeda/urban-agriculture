from arduino.app_utils import *
import time
import threading
import random

import config as c

logger = Logger("Sensors")

class Sensor:
    _comand : str = ""
    
    def __init__(self):
        self.params = []
        self.data = ""

    def read(self):
        try:
            self.data = Bridge.call(f"{self._comand}", *self.params)
            if self.data == "error":
                self._on_error()
            else:
                self._parse()
            
        except Exception as e:
            logger.error(f"{self.__class__.__name__}: {e}")
            self._on_error()
            
        
        
    def _parse(self):
        #Splits the string containing the data collected by the sensor in the Bridge.call() into variables
        pass
    
    def _on_error(self):
        #Invalidates the data in case of an error in the sensor 
        self.data = float('nan')
        
    def get_value(self):
        #Returns the current data stored in the variables (once already extracted form the .data string)
        pass


class Sht30(Sensor):
    _comand = "get_sht_30"
    
    def __init__(self):
        super().__init__()
        self.in_temp = 0.0
        self.in_hum = 0.0 
    
    def _parse(self):
            in_temp_str, in_hum_str = self.data.split(",")
            self.in_temp = float(in_temp_str)
            self.in_hum = float(in_hum_str)

    def _on_error(self):
            self.in_temp = float('nan')
            self.in_hum = float('nan')

                    
    def get_value(self):
        return self.in_temp, self.in_hum
                    
                    
class MoistV1_2(Sensor):
    _comand = "get_moist_v1_2"

    def __init__(self, pin, min_val, max_val):

        super().__init__()

        self.params = [pin]


        #Threshold values to check the incoming data
        self.min_val = min_val 
        self.max_val = max_val

        #The resulting data
        self.clean_data = 0.0

    def _num_map(self, valor):
        porcentaje = ((self.max_val - valor) / (self.max_val - self.min_val)) * 100.0
        return max(0.0, min(100.0, porcentaje))

    def _parse(self):
        self.clean_data = self._num_map(float(self.data))
        
    def _on_error(self):
        self.clean_data = float('nan')
        
    def get_value(self):
        return self.clean_data
        
        
class MoistOrchest:
    def __init__(self, moist_sensors):
        self.moist_sensors = moist_sensors
        self.clean_data = 0.0
          
    def read(self):
        data = []
        for s in self.moist_sensors:
            s.read()
            data.append(s.get_value())
        self._parse(data)
            
    def _parse(self, data):
            self.clean_data = round(sum(data)/len(self.moist_sensors), 2)

    def get_value(self):
        return self.clean_data
