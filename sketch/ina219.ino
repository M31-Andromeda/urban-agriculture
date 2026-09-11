#include <Wire.h>
#include <Adafruit_INA219.h>

Adafruit_INA219 ina219;

String ina219_initialization() {
    Wire.begin();
    delay(50);
    
    if (!ina219.begin()) {
        return "error";
    }
    
    ina219.setCalibration_32V_1A(); 
    
    return "ok";
}

String read_ina219() {
    float voltage_V = ina219.getBusVoltage_V();
    float current_mA = ina219.getCurrent_mA();

    float power_W = voltage_V * (current_mA / 1000.0);
    
    return String(voltage_V, 2) + "," + String(current_mA, 2) + "," + String(power_W, 2);
}