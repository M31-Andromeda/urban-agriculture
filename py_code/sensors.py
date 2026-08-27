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
        pass
    
    def _on_error(self):
        pass
        
    def get_value(self):
        pass


class Sht30(Sensor):
    _comand = "get_sht30"
    
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
        self.min_val = min_val
        self.max_val = max_val
        self.moist_soil = 0.0

    def _num_map(self, valor):
        porcentaje = ((self.max_val - valor) / (self.max_val - self.min_val)) * 100.0
        return max(0.0, min(100.0, porcentaje))

    def _parse(self):
        self.moist_soil = self._num_map(float(self.data))
        
    def _on_error(self):
        self.moist_soil = float('nan')
        
    def get_value(self):
        return self.moist_soil
        
        
class MoistOrchest:
    def __init__(self, moist_sensors):
        self.moist_sensors = moist_sensors
        self.total_moist_soil = 0.0
          
    def read(self):
        data = []
        for s in self.moist_sensors:
            s.read()
            data.append(s.get_value())
        self._parse(data)
            
    def _parse(self, data):
            self.total_moist_soil = round(sum(data)/len(self.moist_sensors), 2)

    def get_value(self):
        return self.total_moist_soil


class Bme680(Sensor):
    _comand = "get_bme680"
    
    def __init__(self):
        super().__init__()
        self.env_temp = 0.0
        self.env_hum = 0.0
        self.pressure = 0.0
        self.air_quality = 0.0
        
    def _parse(self):
        env_temp_str, env_hum_str, pressure_str, air_quality_str = self.data.split(",")
        self.env_temp = float(env_temp_str)
        self.env_hum = float(env_hum_str)
        self.pressure = float(pressure_str) #hPa
        self.air_quality = float(air_quality_str) #kohm
        
    def _on_error(self):
        self.env_temp = float('nan')
        self.env_hum = float('nan')
        self.pressure = float('nan')
        self.air_quality = float('nan')
        
    def get_value(self):
        return  (self.env_temp,
                self.env_hum, 
                self.pressure, 
                self.air_quality)
                

    


        
    