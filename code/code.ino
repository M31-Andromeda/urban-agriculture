
#include <Wire.h>                   // Std Arduino lib - I2C COM              
#include "Arduino_RouterBridge.h"   // Arduino UNO Q - RPC Bridge
#include <SPI.h>                    // Std Arduino lib - SPI COM




void setup() {

    Bridge.begin(); //RPC Com
    Wire.begin();   //I2C COM


    

    //--------------------------PROVIDES--------------------------
    Bridge.provide("get_sht30", read_sht30);

    Bridge.provide("get_moist_v1_2", read_capacitive_moisture_sensor_v1_2);

    Bridge.provide("bme_680_ini", bme680_initialization);
    Bridge.provide("get_bme680", read_bme680);

    Bridge.provide("get_light", read_modulino_light);
    Bridge.provide("light_ini", modulino_light_initialization);

    Bridge.provide("get_ina219", read_ina219);
    Bridge.provide("ina219_ini", ina219_initialization);


    //--------------------------INITIALIZATORS--------------------------
    bme680_initialization();
    modulino_light_initialization();
    ina219_initialization();
}


void loop() {
    
}
