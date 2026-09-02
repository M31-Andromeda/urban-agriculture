from arduino.app_utils import *
import time
import threading

import config as c

from sensors import SensorOrchestra
from data_manager import DataOrchestra

logger = Logger("garden")

class GardenState:
    def __init__(self):

        self.lock = threading.Lock()
        self.keys = ('env_temperature_(°C)', 'env_humidity_(%)', 'pressure_(hPa)', 
                     'soil_moisture_(%)', 'plants_temp_(°C)', 'plants_hum_(%)', 'light_intensity_(lux)', 
                     'ir_(raw)', 'current_(mA)', 'voltage_(V)')
        
        self.sensors_readings = {key : 0.0 for key in self.keys}
    
@brick        
class Director:
    def __init__(self, garden):
        self.garden = garden
        
    def start(self):
        #----------instantiations----------#
        self.sensor_orchestra = SensorOrchestra(self.garden)
        self.data_orchestra = DataOrchestra(self.garden)
        
                
    @brick.loop
    def run(self):        
        self.sensor_orchestra.run()
        self.data_orchestra.save_local()
        self.data_orchestra.save_online()
    
        time.sleep(c.BEAT)
        
garden = GardenState()
director = Director(garden)
App.run()
