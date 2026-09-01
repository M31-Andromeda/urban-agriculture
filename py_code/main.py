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
        self.keys = ('Env_temperature_(°C)', 'Env_Humidity_(%)', 'Pressure_(hPa)', 
                     'Soil_Moisture_(%)', 'Plants_temp_(°C)', 'Plants_hum_(%)', 'Light_intensity_(lux)', 
                     'IR_(raw)', 'Current_(mA)', 'Voltage_(V)')
        
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
