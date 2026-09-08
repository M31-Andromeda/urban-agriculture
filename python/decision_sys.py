import math

from arduino.app_utils import *

import config as c


logger = Logger("DecisionSystem")


class DecisionOrquestra:
    def __init__(self, garden, data_orchestra, model=None):
        self.garden = garden
        self.data_orchestra = data_orchestra
        self.model = model

    def decide(self) -> str:
        """Rule engine's vote for now; will combine with self.model once trained."""
        with self.garden.lock:
            reading = self.garden.sensors_readings.copy()
        moist_history = self.data_orchestra.read_column_history("soil_moisture_(%)")

        rule_action = self.labeler(reading, moist_history)

        # TODO: once self.model exists, predict with it here and combine with rule_action.

        return rule_action

    def _moisture_bounds(self, moist_history):
        """Judged against its own rolling baseline, not a fixed number — the
        capacitive sensor's calibration drifts when cleaned/reinserted. The
        2-day window keeps it from chasing a slow dry-down; moist_absolute_floor_pct
        in labeler() is the backstop."""
        window = c.THRESHOLDS["moist_baseline_window"]
        if len(moist_history) < window:
            return c.THRESHOLDS["moist_absolute_floor_pct"], 90.0

        baseline = sum(moist_history[-window:]) / window
        margin = c.THRESHOLDS["moist_baseline_margin_pct"]
        return baseline - margin, baseline + margin

    def labeler(self, reading, moist_history) -> str:
        """Pure rule engine; also used to auto-label the synthetic dataset."""
        moisture = reading.get("soil_moisture_(%)")
        env_temp = reading.get("env_temperature_(°C)")
        env_hum = reading.get("env_humidity_(%)")
        plants_temp = reading.get("plants_temp_(°C)")
        plants_hum = reading.get("plants_hum_(%)")
        light = reading.get("light_intensity_(lux)")
        power = reading.get("power_(W)")

        if any(v is None or (isinstance(v, float) and math.isnan(v)) for v in [moisture, env_temp, env_hum, plants_temp, plants_hum, light, power]):
            return "INSUFFICIENT_DATA"

        moist_low, moist_high = self._moisture_bounds(moist_history)
        env_temp_low, env_temp_high = c.THRESHOLDS["env_temp_low"], c.THRESHOLDS["env_temp_high"]
        plants_temp_low, plants_temp_high = c.THRESHOLDS["plants_temp_low"], c.THRESHOLDS["plants_temp_high"]

        is_night = (light < c.THRESHOLDS["light_night_lux"])

        if moisture < moist_low or moisture < c.THRESHOLDS["moist_absolute_floor_pct"]:
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
