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

        #BME680: Colocat fora del entorn de les plantes per poder mesurar el estat ambiental general
        self.env_temp = 0.0
        self.env_hum = 0.0
        self.pressure = 0.0
        self.air_quality = 0.0
        
        #Capacitive moisture sensor v.1.2 x3 Humitat de la terra de cultiu
        self.moist_soil = 0.0

        #SHT30 Mesura temperatura i Humitat, pero estara disposat entre les plantes, per veure el seu estat d'aprop
        self.in_temp = 0.0
        self.in_hum = 0.0

        #Modulino Light mesura intensitat lluminosa
        self.amb_light = 0.0
        self.ir = 0.0

        #INA219 mesura intensitat i voltage del panell solar
        self.current = 0.0
        self.voltage = 0.0
       

@brick        
class Director:
    def __init__(self, garden):
        self.garden = garden
        
    def start(self):
        #----------instantiations----------#
        self.sensor_orchestra = SensorOrchestra(self.garden)
        self.data_orchestra = DataOrchestra(self.garden)
        
        #----------starts----------#
        self.sensor_orchestra.start()
        
    @brick.loop
    def run(self):        
        self.sensor_orchestra.run()
        self.data_orchestra.save_local()
        
        
        time.sleep(c.BEAT)
        
        




garden = GardenState()
director = Director(garden)


App.run()
