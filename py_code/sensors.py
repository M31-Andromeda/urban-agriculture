from arduino.app_utils import *
import math

import config as c

logger = Logger("Sensors")

class Sensor:
    _comand : str = ""
    _keys : tuple = tuple()
    
    def __init__(self):
        self.params = []
        self.raw_data = ""
        self.clean_data = dict()

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
        values = [self._map(float(value)) for value in self.raw_data.split(",")]
        
        if len(values) == len(self._keys):
            self.clean_data = dict(zip(self._keys, values))
            
        else:
            self._on_error()
    
    def _on_error(self):
        self.clean_data = {key: float('nan') for key in self._keys}
        
    def get_value(self):
        """returns a dictionary with the data parsed"""
        return self.clean_data
    
    def _map(self, value):
        return value


class Sht30(Sensor):
    _comand = "get_sht30"
    _keys = ("Plants_temp_(°C)", "Plants_hum_(%)")
          
                    
class MoistV1_2(Sensor):
    _comand = "get_moist_v1_2"
    _keys = ("Soil_Moisture_(%)",)
    
    def __init__(self, pin, min_val, max_val):
        super().__init__()
        self.params = [pin]
        self.min_val = min_val 
        self.max_val = max_val

    def _map(self, value):
        percentatge = ((self.max_val - value) / (self.max_val - self.min_val)) * 100.0
        return max(0.0, min(100.0, percentatge))

       
class MoistOrchest:
    def __init__(self, moist_sensors):
        self.moist_sensors = moist_sensors
        self.clean_data = (0.0,)
        self.raw_data = []
          
    def read(self):
        self.raw_data = []
        for s in self.moist_sensors:
            s.read()
            self.raw_data.append(s.get_value()["Soil_Moisture_(%)"])
        self._parse()
            
    def _parse(self):
        valid_data = [d for d in self.raw_data if not math.isnan(d) and d < 100 and d > 0]
        #print(self.raw_data)
        if not valid_data:
            self.clean_data = {"Soil_Moisture_(%)": float('nan')}
        else:
            self.clean_data = {"Soil_Moisture_(%)": round(sum(valid_data)/len(valid_data), 2)}

    def get_value(self):
        return self.clean_data


class Bme680(Sensor):
    _comand = "get_bme680"
    _keys = ("Env_temperature_(°C)", "Env_Humidity_(%)", "Pressure_(hPa)") 
    
    
class ModulinoLight(Sensor):
    _comand = "get_light"
    _keys = ("Light_intensity_(lux)", "IR_(raw)")
    
    
class Ina219(Sensor):
    _comand = "get_ina219"
    _keys = ("Voltage_(V)", "Current_(mA)")
      
      
class SensorOrchestra:
    def __init__(self, garden):
        
        self.garden = garden
        
        moist_sensor_list = []
        for sensor_config in c.MOIST_SENSORS_CONFIG:
            moist_sensor_list.append(MoistV1_2(*sensor_config))

        self.sensors = [Sht30(),
                        MoistOrchest(moist_sensor_list),
                        Bme680(),
                        ModulinoLight(),
                        Ina219()]        
        
    def run(self):
        for sensor in self.sensors:
            sensor.read()
        
        with self.garden.lock:
            for sensor in self.sensors:
                self.garden.sensors_readings.update(sensor.get_value())
        