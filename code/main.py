from arduino.app_utils import *
import time
import threading

LECTURE_TIME = 60*3 # 3 minuts

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
class SHT30:

    @brick.loop()
    def read(self):

        data = Bridge.call("get_sht_30")
        temp_str, hum_str = data.split(",")
        temp = float(temp_str)
        hum = float(hum_str)

        ##
        print(temp, hum)
        ##


        time.sleep(LECTURE_TIME)



#hort = EstatHort()

sht30_1 = SHT30()

App.run()






        

