from arduino.app_utils import *
import numpy as np

import config as c


logger = Logger("DecisionSystem")




class DecisionOrquestra:
    def __init__(self, garden, data_orchestra, model=None):
        self.garden = garden
        self.data_orchestra = data_orchestra
        self.model = model

    def decide(self) -> str:
        """La decisión final de verdad. Todavía no combina nada porque
        aún no hay modelo entrenado — de momento solo devuelve el voto
        de las reglas."""
        with self.garden.lock:
            reading = self.garden.sensors_readings.copy()
        moist_history = self.data_orchestra.read_column_history("soil_moisture_(%)")
        env_temp_history = self.data_orchestra.read_column_history("env_temperature_(°C)")
        plants_temp_history = self.data_orchestra.read_column_history("plants_temp_(°C)")

        rule_action = self.labeler(reading, moist_history, env_temp_history, plants_temp_history)

        # TODO: cuando self.model exista, predecir con él aquí y combinar
        # con rule_action. Justo lo que toca decidir ahora.

        return rule_action
    
    def _get_bounds(self, type_of_data,  data_history, min_readings=20):
        
        if len(data_history) > min_readings:
            low = np.percentile(data_history, c.THRESHOLDS["low_pct"])
            high = np.percentile(data_history, c.THRESHOLDS["high_pct"])
            return low, high
        return ((40.0, 90.0) if type_of_data == "soil_moisture_(%)" 
                else (c.THRESHOLDS["env_temp_high"], c.THRESHOLDS["env_temp_low"]) if type_of_data == "env_temperature_(°C)" 
                else (c.THRESHOLDS["plants_temp_low"], c.THRESHOLDS["plants_temp_high"]) if type_of_data == "plants_temp_(°C)" 
                else (0.0, 100.0))


    def labeler(self, reading, moist_history, env_temp_history, plants_temp_history) -> str:
        """Motor de reglas puro. Etiqueta el dataset sintético de entrenamiento,
        y en producción es uno de los dos votos que combina DecisionOrquestra.decide()."""
        moisture = reading.get("soil_moisture_(%)")
        env_temp = reading.get("env_temperature_(°C)")
        env_hum = reading.get("env_humidity_(%)")
        plants_temp = reading.get("plants_temp_(°C)")
        plants_hum = reading.get("plants_hum_(%)")
        light = reading.get("light_intensity_(lux)")
        power = reading.get("power_(W)")

        if any(v is None or (isinstance(v, float) and np.isnan(v)) for v in [moisture, env_temp, env_hum, plants_temp, plants_hum, light, power]):
            return "DATOS_INSUFICIENTES"

        moist_low, moist_high = self._get_bounds("soil_moisture_(%)", moist_history, min_readings=20)
        env_temp_low, env_temp_high = self._get_bounds("env_temperature_(°C)", env_temp_history, min_readings=20)
        plants_temp_low, plants_temp_high = self._get_bounds("plants_temp_(°C)", plants_temp_history, min_readings=20)

        is_night = (light == 0)

        if moisture < moist_low:
            if (light > c.THRESHOLDS["light_intense_lux"] or env_temp > env_temp_high):
                if power < (c.THRESHOLDS["pumps_max_consum"] + c.THRESHOLDS["uno_q_consum"]):
                    return "NOT_ABLE_TO_WATER"
            return "WATER"

        if moisture > moist_high:
            if (env_hum > c.THRESHOLDS["env_humidity_fungal_high"] or plants_hum > c.THRESHOLDS["plants_humidity_fungal_high"]) or is_night:
                return "FUNGI_ALERT_EXCESS_WATER"
            return "EXCESS_WATER"

        if env_temp > env_temp_high and env_hum < c.THRESHOLDS["env_humidity_stress_low"]:
            return "HYDRIC_STRESS_ALERT"

        if env_temp > env_temp_high or plants_temp > plants_temp_high:
            if power < (c.THRESHOLDS["fans_max_consum"] + c.THRESHOLDS["uno_q_consum"]):
                return "NOT_ABLE_TO_VENTILATE"
            return "VENTILATE"

        if env_temp < env_temp_low or plants_temp < plants_temp_low:
            return "LOW_TEMP_ALERT"

        if 0 < light < c.THRESHOLDS["light_low_lux"]:
            return "LOW_LIGHT"

        return "OK"
