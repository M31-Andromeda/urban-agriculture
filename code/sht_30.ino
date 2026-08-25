#include <Wire.h>                  // Std Arduino lib - I2C COM
#include <vector>

#define SHT30_ADDR 0x44


String read_sht30() {
    uint8_t data[6];

    Wire.beginTransmission(SHT30_ADDR);
    Wire.write(0x2C);
    Wire.write(0x06);
    Wire.endTransmission();

    delay(50); 

    Wire.requestFrom(SHT30_ADDR, 6);

    if (Wire.available() == 6) {
        data[0] = Wire.read(); // Temperatura MSB
        data[1] = Wire.read(); // Temperatura LSB
        data[2] = Wire.read(); 
        data[3] = Wire.read(); // Humitat MSB
        data[4] = Wire.read(); // Humitat LSB
        data[5] = Wire.read(); 

        uint16_t t_raw = (data[0] << 8) | data[1];
        float temp = -45.0 + (175.0 * t_raw / 65535.0); 

        uint16_t h_raw = (data[3] << 8) | data[4];
        float hum = 100.0 * (h_raw / 65535.0);

        return String(temp, 2) + "," + String(hum, 2);
    }

    return "None, None"; 
}
