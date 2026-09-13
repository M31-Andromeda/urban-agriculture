#include <Wire.h>

// Initializes the light Modulino over I2C.
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

// Reads ambient light and raw infrared from the Modulino.
String read_modulino_light() {
    // --- READ INFRARED ---
    Wire.beginTransmission(0x53);
    Wire.write(0x0A);
    Wire.endTransmission(false);

    if (Wire.requestFrom(0x53, 3) < 3) {
        return "error";  // I2C read failed - do not report this as "0 lux" (looks like night)
    }
    uint32_t raw_ir = Wire.read() | (Wire.read() << 8) | ((uint32_t)Wire.read() << 16);
    raw_ir &= 0x0FFFFF;

    // --- READ AMBIENT LIGHT ---
    Wire.beginTransmission(0x53);
    Wire.write(0x0D);
    Wire.endTransmission(false);

    if (Wire.requestFrom(0x53, 3) < 3) {
        return "error";  // I2C read failed - do not report this as "0 lux" (looks like night)
    }
    uint32_t raw_amb = Wire.read() | (Wire.read() << 8) | ((uint32_t)Wire.read() << 16);
    raw_amb &= 0x0FFFFF;

    float amb = (float)raw_amb * 0.6;

    return String(amb, 2) + "," + String(raw_ir);
}