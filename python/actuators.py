from arduino.app_utils import *

import config as c

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
    def __init__(self):
        self.water_pump = Actuator("water_pump", c.WATER_PUMP_PIN)
        self.fans = Actuator("fans", c.FANS_PIN)

    def stop_all(self):
        logger.info("Emergency stop activated. Setting all actuators to LOW.")
        self.water_pump.set_state("LOW")
        self.fans.set_state("LOW")