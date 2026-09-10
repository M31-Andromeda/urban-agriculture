from arduino.app_utils import *
import math

import config as c

logger = Logger("Sensors")

class Sensor:
    _command : str = ""
    _keys : tuple = tuple()

    def __init__(self):
        self.params = []
        self.raw_data = ""
        self.clean_data = dict()

    def read(self):
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
        self.clean_data = {key: float('nan') for key in self._keys}

    def get_value(self):
        return self.clean_data

    def _map(self, value):
        """Override in subclasses to transform the raw value."""
        return value


class Sht30(Sensor):
    _command = "get_sht30"
    _keys = ("plants_temp_(°C)", "plants_hum_(%)")


class MoistV1_2(Sensor):
    _command = "get_moist_v1_2"
    _keys = ("soil_moisture_(%)",)

    def __init__(self, pin, min_val, max_val):
        super().__init__()
        self.params = [pin]
        self.min_val = min_val
        self.max_val = max_val

    def _map(self, value):
        # Inverted on purpose: this probe's raw ADC reading goes DOWN as the soil gets wetter.
        percentage = ((self.max_val - value) / (self.max_val - self.min_val)) * 100.0
        return max(0.0, min(100.0, percentage))

       
class MoistOrchest:
    """Averages readings from multiple moisture probes, skipping NaNs."""
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
        if not valid_data:
            self.clean_data = {"soil_moisture_(%)": float('nan')}
        else:
            self.clean_data = {"soil_moisture_(%)": round(sum(valid_data)/len(valid_data), 2)}

    def get_value(self):
        return self.clean_data


class Bme680(Sensor):
    _command = "get_bme680"
    _keys = ("env_temperature_(°C)", "env_humidity_(%)", "pressure_(hPa)")


class ModulinoLight(Sensor):
    _command = "get_light"
    _keys = ("light_intensity_(lux)", "ir_(raw)")


class Ina219(Sensor):
    _command = "get_ina219"
    _keys = ("voltage_(V)", "current_(mA)", "power_(W)")


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
        logger.info(f"Sensors reading completed.")

        with self.garden.lock:
            for sensor in self.sensors:
                self.garden.sensors_readings.update(sensor.get_value())
        logger.info(f"Garden state updated with new sensor readings.")
        