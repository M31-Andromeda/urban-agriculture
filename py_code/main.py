from arduino.app_utils import *
import time
import threading
import random

import config as c

from sensors import *

logger = Logger("Hort")

class EstatHort:
    def __init__(self):

        self.lock = threading.Lock()

        #BME680: Colocat fora del entorn de les plantes per poder mesurar el estat ambiental general
        self.qualitat_aire = 0.0
        self.ambi_hum = 0.0
        self.ambi_temp = 0.0
        self.pressio = 0.0

        #Capacitive moisture sensor v.1.2 x3 Humitat de la terra de cultiu
        self.terra_hum = 0.0

        #SHT30 Mesura temperatura i Humitat, pero estara disposat entre les plantes, per veure el seu estat d'aprop
        self.in_hum = 0.0
        self.in_temp = 0.0

        #Modulino Light mesura intensitat lluminosa
        self.light_intens = 0.0
        self.ir = 0.0

        #INA219 mesura intensitat i voltage del panell solar
        self.intensitar = 0.0
        self.voltatge = 0.0
       
@brick
class SensorOrchestra:
    def __init__(self, hort):
        self.hort = hort
        self.sensors = []        
        
    def start(self):
        self.sht30 = Sht30()
        self.sensors.append(self.sht30)
        
        s1_moist = MoistV1_2(0, 275, 682)
        s2_moist = MoistV1_2(1, 290, 685)
        s3_moist = MoistV1_2(2, 287, 683)
        self.moisture_orchestra = MoistOrchest([s1_moist, s2_moist, s3_moist])
        self.sensors.append(self.moisture_orchestra)
        
        
    @brick.loop()
    def run(self):
        for sensor in self.sensors:
            sensor.read()
        
        self.hort.in_temp, self.hort.in_hum = self.sht30.get_value()
        self.hort.terra_hum = self.moisture_orchestra.get_value()
        
        
            
        ###------testing-------------
        for atr, val in vars(self.hort).items():
            if atr != "lock":
                print(f"{atr}: {val}", end = " ")
            
        print()

        ###------end-testing---------
        
        time.sleep(c.BEAT)

        

               
    
                    
        

hort = EstatHort()

sensor_orchestra = SensorOrchestra(hort)





# ###----------------------------Test_Space----------------------------###
# @brick
# class Beater:
    
#     @brick.loop()
#     def pulse(self):
#         dato =  Bridge.call(f"get_moist_v1_2", 1)
#         print("hola")
#         print(dato)
#         time.sleep(2)
            
    
# beat = Beater()
# ###------------------------------------------------------------------###
        

App.run()
