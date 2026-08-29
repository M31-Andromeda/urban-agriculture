from arduino.app_utils import *
import time
import threading
import random
import math

import config as c

logger = Logger("Sensors")

class Sensor:
    _comand : str = ""
    
    def __init__(self):
        self.params = []
        self.raw_data = ""
        self.clean_data = []

    def read(self):
        try:
            self.raw_data = Bridge.call(f"{self._comand}", *self.params, timeout=10)
            if self.raw_data == "error":
                self._on_error()
            else:
                self._parse()
            
        except Exception as e:
            logger.error(f"{self.__class__.__name__}: {e}")
            self._on_error()
            
    def _parse(self):
        self.clean_data = tuple(float(elem) for elem in self.raw_data.split(","))
    
    def _on_error(self):
        self.clean_data = tuple(float('nan') for _ in range(self._expected_outputs))
        
    def get_value(self):
        """returns a tuple with the data parsed"""
        return self.clean_data


class Sht30(Sensor):
    _comand = "get_sht30"
    _expected_outputs = 2
    
    def get_value(self):
        """returns a tuple with (temperature (°C), humidity (%))"""
        return super().get_value()
               
                    
class MoistV1_2(Sensor):
    _comand = "get_moist_v1_2"
    _expected_outputs = 1
    
    def __init__(self, pin, min_val, max_val):
        super().__init__()
        self.params = [pin]
        self.min_val = min_val
        self.max_val = max_val

    def _num_map(self, valor):
        percentatge = ((self.max_val - valor) / (self.max_val - self.min_val)) * 100.0
        return max(0.0, min(100.0, percentatge))

    def _parse(self):
        self.clean_data = tuple([self._num_map(float(self.raw_data))])
    
          
class MoistOrchest:
    def __init__(self, moist_sensors):
        self.moist_sensors = moist_sensors
        self.total_moist_soil = 0.0
          
    def read(self):
        data = []
        for s in self.moist_sensors:
            s.read()
            data.append(s.get_value()[0])
        self._parse(data)
            
    def _parse(self, data):
        self.temporal = data
        valid_data = [d for d in data if not math.isnan(d) and d < 100 and d > 0]
        if not valid_data:
            self.total_moist_soil = tuple([float('nan')])
        else:
            self.total_moist_soil = tuple([round(sum(valid_data)/len(valid_data), 2)])

    def get_value(self):
        """returns a tuple with the average between the moisture sensors (%)"""
        return self.total_moist_soil


class Bme680(Sensor):
    _comand = "get_bme680"
    _expected_outputs = 4
    
    def get_value(self):
        """returns a tuple with (temperature (°C), humidity (%), pressure (hPa), VOC (kΩ))"""
        return super().get_value()
    
        
class ModulinoLight(Sensor):
    _comand = "get_light"
    _expected_outputs = 2
    
    def get_value(self):
        """returns a tuple with (ambient light (lux), IR (raw))"""
        return super().get_value()
    
class Ina219(Sensor):
    _comand = "get_ina219"
    _expected_outputs = 2
    
    def get_value(self):
        """returns a tuple with (voltage (V), current (mA))"""
        return super().get_value()
    
    
    
class SensorOrchestra:
    def __init__(self, garden):
        self.garden = garden
        self.sensors = []        
        
    def start(self):
        self.sht30 = Sht30()
        self.sensors.append(self.sht30)
        
        moist_sensor_list = []
        for sensor_data in c.MOIST_SENSORS_CONFIG:
            moist_sensor_list.append(MoistV1_2(*sensor_data))
        self.moisture_orchestra = MoistOrchest(moist_sensor_list)
        self.sensors.append(self.moisture_orchestra)
        
        self.bme680 = Bme680()
        self.sensors.append(self.bme680)
        
        self.light_sensor = ModulinoLight()
        self.sensors.append(self.light_sensor)
        
        self.ina219 = Ina219()
        self.sensors.append(self.ina219)
        
        
    def run(self):
        for sensor in self.sensors:
            sensor.read()
        
        with self.garden.lock:
            self.garden.in_temp, self.garden.in_hum = self.sht30.get_value()
            self.garden.moist_soil = self.moisture_orchestra.get_value()[0]
            self.garden.env_temp, self.garden.env_hum, self.garden.pressure, self.garden.air_quality = self.bme680.get_value()
            self.garden.amb_light, self.garden.ir = self.light_sensor.get_value()
            self.garden.voltage, self.garden.current = self.ina219.get_value()
        