#include <Wire.h>


String modulino_light_initialization() {
    Wire.begin();
    delay(50);

    Wire.beginTransmission(0x53);
    Wire.write(0x00);
    Wire.write(0x06); 
    
    if (Wire.endTransmission() == 0) {
        delay(100); 
        return "ok";
    } else {
        return "error";
    }
}

String read_modulino_light() {
    // --- LEER INFRARROJO ---
    Wire.beginTransmission(0x53);
    Wire.write(0x0A);
    Wire.endTransmission(false);
    
    uint32_t raw_ir = 0;
    if (Wire.requestFrom(0x53, 3) >= 3) {
        raw_ir = Wire.read() | (Wire.read() << 8) | ((uint32_t)Wire.read() << 16);
        raw_ir &= 0x0FFFFF;
    }

    // --- LEER LUZ AMBIENTAL ---
    Wire.beginTransmission(0x53);
    Wire.write(0x0D);
    Wire.endTransmission(false);
    
    uint32_t raw_amb = 0;
    if (Wire.requestFrom(0x53, 3) >= 3) {
        raw_amb = Wire.read() | (Wire.read() << 8) | ((uint32_t)Wire.read() << 16);
        raw_amb &= 0x0FFFFF; 
    }

    float amb = (float)raw_amb * 0.6;
    
    return String(amb, 2) + "," + String(raw_ir);
}