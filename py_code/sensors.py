from arduino.app_utils import *
import math

import config as c

logger = Logger("Sensors")

class Sensor:
    """Base class for all sensors"""
    _command : str = ""
    _keys : tuple = tuple()
    
    def __init__(self):
        """Initializes the sensor with default values"""
        self.params = []
        self.raw_data = ""
        self.clean_data = dict()

    def read(self):
        """Reads the sensor data from the Arduino MCU using RPC and parses it into a dictionary"""
        try:
            self.raw_data = Bridge.call(f"{self._command}", *self.params, timeout=10)
            if self.raw_data == "error":
                self._on_error()
            else:
                self._parse()
            
        except Exception as e:
            logger.error(f"{self.__class__.__name__}: {e}")
            self._on_error()
            
    def _parse(self):
        """Parses the raw data into a dictionary with keys defined in _keys. If the parsing fails, it calls _on_error to set the clean_data to NaN values."""
        try:
            values = [self._map(float(value)) for value in self.raw_data.split(",")]
            if len(values) == len(self._keys):
                self.clean_data = dict(zip(self._keys, values))
            else:
                self._on_error()
                
        except Exception as e:
            logger.error(f"{self.__class__.__name__}: {e}")
            self._on_error()
    
    def _on_error(self):
        """Sets the clean_data to NaN values for all keys in case of an error"""
        self.clean_data = {key: float('nan') for key in self._keys}
        
    def get_value(self):
        """returns a dictionary with the data parsed"""
        return self.clean_data
    
    def _map(self, value):
        """Maps the raw value to a clean value. This method can be overridden in subclasses if needed."""
        return value


class Sht30(Sensor):
    """SHT30 sensor class for reading temperature and humidity data."""
    _command = "get_sht30"
    _keys = ("plants_temp_(°C)", "plants_hum_(%)")
          
                    
class MoistV1_2(Sensor):
    """ Moisture sensor class for reading soil moisture data. It maps the raw sensor value to a percentage based on the provided minimum and maximum values."""
    _command = "get_moist_v1_2"
    _keys = ("soil_moisture_(%)",)
    
    def __init__(self, pin, min_val, max_val):
        super().__init__()
        self.params = [pin]
        self.min_val = min_val 
        self.max_val = max_val

    def _map(self, value):
        percentage = ((self.max_val - value) / (self.max_val - self.min_val)) * 100.0
        return max(0.0, min(100.0, percentage))

       
class MoistOrchest:
    """Orchestra class for managing multiple moisture sensors. It reads data from all sensors, filters out invalid readings, and calculates the average soil moisture percentage."""
    def __init__(self, moist_sensors):
        self.moist_sensors = moist_sensors
        self.clean_data = (0.0,)
        self.raw_data = []
          
    def read(self):
        self.raw_data = []
        try:
            for s in self.moist_sensors:
                s.read()
                self.raw_data.append(s.get_value()["soil_moisture_(%)"])
            self._parse()
        except Exception as e:
            logger.error(f"MoistOrchest: {e}")
            self.clean_data = {"soil_moisture_(%)": float('nan')}
            
    def _parse(self):
        valid_data = [d for d in self.raw_data if not math.isnan(d)]
        #print(self.raw_data)
        if not valid_data:
            self.clean_data = {"soil_moisture_(%)": float('nan')}
        else:
            self.clean_data = {"soil_moisture_(%)": round(sum(valid_data)/len(valid_data), 2)}

    def get_value(self):
        return self.clean_data


class Bme680(Sensor):
    """ BME680 sensor class for reading environmental data such as temperature, humidity, and pressure."""
    _command = "get_bme680"
    _keys = ("env_temperature_(°C)", "env_humidity_(%)", "pressure_(hPa)") 
    
    
class ModulinoLight(Sensor):
    """ Modulino Light sensor class for reading light intensity and infrared data."""
    _command = "get_light"
    _keys = ("light_intensity_(lux)", "ir_(raw)")
    
    
class Ina219(Sensor):
    """ INA219 sensor class for reading voltage and current data."""
    _command = "get_ina219"
    _keys = ("voltage_(V)", "current_(mA)")
      
      
class SensorOrchestra:
    """Orchestra class for managing multiple sensors. It reads data from all sensors and updates the garden's sensor readings."""
    def __init__(self, garden):
        """Initializes the SensorOrchestra with a list of sensor instances and a reference to the garden state."""
        
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
        """Reads data from all sensors and updates the garden's sensor readings in a thread-safe manner."""
        
        for sensor in self.sensors:
            sensor.read()
        logger.info(f"Sensors reading completed.")
        
        with self.garden.lock:
            for sensor in self.sensors:
                self.garden.sensors_readings.update(sensor.get_value())
        logger.info(f"Garden state updated with new sensor readings.")
        