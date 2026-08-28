from arduino.app_utils import *
import time
import threading
import random

import config as c
from sensors import *

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
        self.in_hum = 0.0
        self.in_temp = 0.0

        #Modulino Light mesura intensitat lluminosa
        self.amb_light = 0.0
        self.ir = 0.0

        #INA219 mesura intensitat i voltage del panell solar
        self.current = 0.0
        self.voltage = 0.0
       
@brick
class SensorOrchestra:
    def __init__(self, garden):
        self.garden = garden
        self.sensors = []        
        
    def start(self):
        self.sht30 = Sht30()
        self.sensors.append(self.sht30)
        
        moist_sensor_list = []
        for sensor_data in c.MOIST_SENSORS_CONFIG:
            moist_sensor_list.append(MoistV1_2(*sensor_data))
        self.moisture_orchestra = MoistOrchest(moist_sensor_list)
        self.sensors.append(self.moisture_orchestra)
        
        self.bme680 = Bme680()
        self.sensors.append(self.bme680)
        
        self.light_sensor = ModulinoLight()
        self.sensors.append(self.light_sensor)
        
        self.ina219 = Ina219()
        self.sensors.append(self.ina219)
        
    @brick.loop()
    def run(self):
        for sensor in self.sensors:
            sensor.read()
        
        with self.garden.lock:
            self.garden.in_temp, self.garden.in_hum = self.sht30.get_value()
            self.garden.moist_soil = self.moisture_orchestra.get_value()
            self.garden.env_temp, self.garden.env_hum, self.garden.pressure, self.garden.air_quality = self.bme680.get_value()
            self.garden.amb_light, self.garden.ir = self.light_sensor.get_value()
            self.garden.voltage, self.garden.current = self.ina219.get_value()
            
        
        time.sleep(c.BEAT)




garden = GardenState()
sensor_orchestra = SensorOrchestra(garden)

App.run()
