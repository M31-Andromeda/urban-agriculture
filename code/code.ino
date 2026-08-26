
#include <Wire.h>                   // Std Arduino lib - I2C COM              
#include "Arduino_RouterBridge.h"   // Arduino UNO Q - RPC Bridge
#include <SPI.h>                    // Std Arduino lib - SPI COM
#include <Adafruit_Sensor.h>        // Adafruit Unified Sensor (librería base)
#include "Adafruit_BME680.h"        // Driver sensor BME680 (Temp, Hum, Pres, Gas)



void setup() {

    Bridge.begin(); //RPC Com
    Wire.begin();   //I2C COM

    

    //--------------------------PROVIDES--------------------------

    Bridge.provide("get_sht_30", read_sht30);
    Bridge.provide("get_moist_v1_2", read_capacitive_moisture_sensor_v1_2);
}


void loop() {
}







