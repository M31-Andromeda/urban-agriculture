from arduino.app_utils import *
import time
import threading

import config as c

from actuators import ActuatorOrchestra
from sensors import SensorOrchestra
from data_manager import DataOrchestra
from decision_sys import DecisionOrchestra
from telegram import TelegramDirector

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
    def __init__(self, garden, telegram_director):
        self.garden = garden
        self.telegram_director = telegram_director

    def start(self):
        logger.info("Initializing the garden monitoring system...")
        self.sensor_orchestra = SensorOrchestra(self.garden)
        self.data_orchestra = DataOrchestra(self.garden)
        self.decision_orchestra = DecisionOrchestra(self.garden, self.data_orchestra)
        self.actuator_orchestra = ActuatorOrchestra(self.telegram_director)

    @brick.loop
    def run(self):
        logger.info("Starting the main loop of the garden monitoring system...")

        self.sensor_orchestra.run()
        self.decision_orchestra.predict()
        self.data_orchestra.save_local()
        self.data_orchestra.save_online()
        self.actuator_orchestra.run(self.garden.predictions)

        logger.info(f"Cycle completed. Waiting for the next cycle in {c.BEAT} seconds...")
        time.sleep(c.BEAT)
        
garden = GardenState()

telegram_director = TelegramDirector(garden)
director = Director(garden, telegram_director)
App.run()