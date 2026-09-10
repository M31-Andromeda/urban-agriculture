from arduino.app_utils import *
import time
import threading

import config as c

from actuators import ActuatorOrchestra
from sensors import SensorOrchestra
from data_manager import DataOrchestra
from decision_sys import DecisionOrquestra

logger = Logger("Director")

class GardenState:
    def __init__(self):
        self.lock = threading.Lock()
        self.keys = ('env_temperature_(°C)', 'env_humidity_(%)', 'pressure_(hPa)', 
                     'soil_moisture_(%)', 'plants_temp_(°C)', 'plants_hum_(%)', 'light_intensity_(lux)', 
                     'ir_(raw)', 'current_(mA)', 'voltage_(V)', 'power_(W)')
        
        self.sensors_readings = {key : 0.0 for key in self.keys}
        
        self.predictions = dict()
    
@brick
class Director:
    def __init__(self, garden):
        self.garden = garden

    def start(self):
        logger.info("Initializing the garden monitoring system...")
        self.sensor_orchestra = SensorOrchestra(self.garden)
        self.data_orchestra = DataOrchestra(self.garden)
        self.actuator_orchestra = ActuatorOrchestra()
        self.decision_orchestra = DecisionOrquestra(self.garden, self.data_orchestra)
               
    @brick.loop
    def run(self):
        logger.info("Starting the main loop of the garden monitoring system...")

        self.sensor_orchestra.run()
        self.decision_orchestra.decide()

        self.data_orchestra.save_local()
        self.data_orchestra.save_online()

        # TODO: drive actuator_orchestra from self.garden.predictions — not wired up yet.

        logger.info(f"Cycle completed. Waiting for the next cycle in {c.BEAT} seconds...")
        time.sleep(c.BEAT)
        
garden = GardenState()
director = Director(garden)
App.run()