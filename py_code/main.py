from arduino.app_utils import *
import time
import threading

import config as c

from sensors import SensorOrchestra
from data_manager import DataOrchestra

logger = Logger("garden")

class GardenState:
    """Class to hold the state of the garden, including sensor readings and a lock for thread-safe access."""
    def __init__(self):
        """Initializes the GardenState with a lock, sensor keys, and a dictionary to hold sensor readings."""

        self.lock = threading.Lock()
        self.keys = ('env_temperature_(°C)', 'env_humidity_(%)', 'pressure_(hPa)', 
                     'soil_moisture_(%)', 'plants_temp_(°C)', 'plants_hum_(%)', 'light_intensity_(lux)', 
                     'ir_(raw)', 'current_(mA)', 'voltage_(V)')
        
        self.sensors_readings = {key : 0.0 for key in self.keys}
    
@brick        
class Director:
    """Director class to manage the overall operation of the garden monitoring system, including sensor reading and data saving."""
    
    def __init__(self, garden):
        """Initializes the Director with a reference to the GardenState."""
        self.garden = garden
        
    def start(self):
        """instantiation of modules that compound the garden monitoring system"""
        
        logger.info("Initializing the garden monitoring system...")
        #----------instantiations----------#
        self.sensor_orchestra = SensorOrchestra(self.garden)
        self.data_orchestra = DataOrchestra(self.garden)
        
                
    @brick.loop
    def run(self):
        """Main loop that continuously executes all the modules, and waits for the next cycle based on the configured beat interval."""        
        logger.info("Starting the main loop of the garden monitoring system...")
        
        self.sensor_orchestra.run()
        self.data_orchestra.save_local()
        self.data_orchestra.save_online()

        logger.info(f"Cycle completed. Waiting for the next cycle in {c.BEAT} seconds...")
        time.sleep(c.BEAT)
        
garden = GardenState()
director = Director(garden)
App.run()
