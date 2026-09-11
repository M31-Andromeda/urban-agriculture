from arduino.app_utils import *

import config as c
import time

logger = Logger("Actuators")

class Actuator:
    _command = "set_actuator"
    
    def __init__(self, name, pin):
        self.state = 0
        self.name = name
        self.pin = pin
         
    def set_state(self, new_state):
        
        new_state = 255 if new_state == "HIGH" else 0 if new_state == "LOW" else new_state
        
        params = [self.pin, new_state]
        try:
            response = Bridge.call(f"{self._command}", *params, timeout=10)
            if response != "ok":
                self._on_error()
            else:
                self.state = new_state
                logger.info(f"[{self.name}]: State changed to {new_state}")
                
        except Exception as e:
            logger.error(f"{self.name} (Pin:{self.pin}): {e}")
            self._on_error()
            
    def _on_error(self):
        logger.error(f"The state of the actuator {self.name} could not be modified.")
        
    def get_state(self):
        return self.state
        
        
class ActuatorOrchestra:
    def __init__(self, telegram_director=None):
        self.water_pump = Actuator("water_pump", c.WATER_PUMP_PIN)
        self.fans = Actuator("fans", c.FANS_PIN)
        self.telegram = telegram_director

    def stop_all(self):
        logger.info("Emergency stop activated. Setting all actuators to LOW.")
        self.water_pump.set_state("LOW")
        self.fans.set_state("LOW")

    def _notify(self, prediction, probability):
        if self.telegram:
            self.telegram.notify(prediction, probability=probability)

    def run(self, predictions):
        prediction, probability = sorted(predictions.items(), key = lambda x:-float(x[1]))[0]

        if prediction == "OK" or prediction == "NIGHT_OK":
            logger.info(f"Prediction is {prediction}. No action required.")

        elif prediction == "WATER":
            logger.info(f"Prediction is WATER. Activating water pump for {c.WATERING_DURATION}")
            self.water_pump.set_state("HIGH")
            time.sleep(c.WATERING_DURATION)
            self.water_pump.set_state("LOW")
            logger.info("Watering completed. Water pump turned off.")
            self._notify(prediction, probability)

        elif prediction == "EXCESS_WATER":
            logger.info("Prediction is EXCESS_WATER. Stop watering.")
            self._notify(prediction, probability)

        elif prediction == "HYDRIC_STRESS_ALERT":
            logger.info("Prediction is HYDRIC_STRESS_ALERT.")
            self._notify(prediction, probability)

        elif prediction == "FUNGI_ALERT_EXCESS_WATER":
            logger.info("Prediction is FUNGI_ALERT_EXCESS_WATER.")
            self._notify(prediction, probability)

        elif prediction == "VENTILATE":
            logger.info(f"Prediction is VENTILATE. Activating fans for {c.VENTILATION_DURATION}")
            self.fans.set_state("HIGH")
            time.sleep(c.VENTILATION_DURATION)
            self.fans.set_state("LOW")
            logger.info("Ventilation completed. Fans turned off")
            self._notify(prediction, probability)

        elif prediction == "LOW_TEMP_ALERT":
            logger.info("Prediction is LOW_TEMP_ALERT.")
            self._notify(prediction, probability)

        elif prediction == "LOW_LIGHT":
            logger.info("Prediction is LOW_LIGHT.")

        elif prediction == "NOT_ABLE_TO_WATER":
            logger.info("Prediction is NOT_ABLE_TO_WATER.")
            self._notify(prediction, probability)

        elif prediction == "NOT_ABLE_TO_VENTILATE":
            logger.info("Prediction is NOT_ABLE_TO_VENTILATE.")
            self._notify(prediction, probability)

        elif prediction == "INSUFFICIENT_DATA":
            logger.info("Prediction is INSUFFICIENT_DATA. Skipping actuation this cycle.")

        else:
            logger.warning(f"Unhandled prediction label: {prediction}")