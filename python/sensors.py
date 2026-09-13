"""Reads and cleans up physical sensor data over Bridge."""

from arduino.app_utils import *
import math

import config as c

logger = Logger("Sensors")

class Sensor:
    """Base for a sensor read over Bridge: fetches raw data and maps it to clean values."""

    _command : str = ""
    _keys : tuple = tuple()

    def __init__(self):
        self.params = []
        self.raw_data = ""
        self.clean_data = dict()

    def read(self):
        """Requests a reading from the MCU over Bridge and parses it."""
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
        """Turns the raw CSV response into a dict of mapped values."""
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
        """Falls back to NaN for every key when the reading fails."""
        self.clean_data = {key: float('nan') for key in self._keys}

    def get_value(self):
        return self.clean_data

    def _map(self, value):
        """Conversion hook, identity by default (overridden by subclasses as needed)."""
        return value


class Sht30(Sensor):
    """Plant-level temperature/humidity."""

    _command = "get_sht30"
    _keys = ("plants_temp_(°C)", "plants_hum_(%)")


class MoistV1_2(Sensor):
    """A single capacitive soil-moisture probe, calibrated with its own min/max."""

    _command = "get_moist_v1_2"
    _keys = ("soil_moisture_(%)",)

    def __init__(self, pin, min_val, max_val):
        super().__init__()
        self.params = [pin]
        self.min_val = min_val
        self.max_val = max_val

    def _map(self, value):
        """Converts the raw analog reading into a moisture percentage (0-100)."""
        percentage = ((self.max_val - value) / (self.max_val - self.min_val)) * 100.0
        return max(0.0, min(100.0, percentage))

       
class MoistOrchest:
    """Averages several soil-moisture probes, discarding NaN readings."""

    def __init__(self, moist_sensors):
        self.moist_sensors = moist_sensors
        self.clean_data = (0.0,)
        self.raw_data = []

    def read(self):
        """Reads all moisture probes and computes the average of the valid ones."""
        self.raw_data = []
        try:
            for s in self.moist_sensors:
                s.read()
                self.raw_data.append(s.get_value()["soil_moisture_(%)"])
            #logger.info(self.raw_data)
            self._parse()
        except Exception as e:
            logger.error(f"MoistOrchest: {e}")
            self.clean_data = {"soil_moisture_(%)": float('nan')}
            
    def _parse(self):
        """Averages the valid readings (drops NaN); NaN if none are valid."""
        valid_data = [d for d in self.raw_data if not math.isnan(d)]
        if not valid_data:
            self.clean_data = {"soil_moisture_(%)": float('nan')}
        else:
            self.clean_data = {"soil_moisture_(%)": round(sum(valid_data)/len(valid_data), 2)}

    def get_value(self):
        return self.clean_data


class Bme680(Sensor):
    """Ambient temperature/humidity/pressure."""

    _command = "get_bme680"
    _keys = ("env_temperature_(°C)", "env_humidity_(%)", "pressure_(hPa)")


class ModulinoLight(Sensor):
    """Ambient light and infrared from the Modulino."""

    _command = "get_light"
    _keys = ("light_intensity_(lux)", "ir_(raw)")


class Ina219(Sensor):
    """Voltage/current/power of the solar system."""

    _command = "get_ina219"
    _keys = ("voltage_(V)", "current_(mA)", "power_(W)")


class SensorOrchestra:
    """Reads all sensors every cycle and updates the shared garden state."""

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
        """Reads every sensor and writes the results into GardenState."""
        for sensor in self.sensors:
            sensor.read()
        logger.info(f"Sensors reading completed.")

        with self.garden.lock:
            for sensor in self.sensors:
                self.garden.sensors_readings.update(sensor.get_value())
        logger.info(f"Garden state updated with new sensor readings.")
        