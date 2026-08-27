#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME680.h>

Adafruit_BME680 bme; 

String bme680_initialization() {

    int count = 0;
    while (!bme.begin(0x76) && count < 10) {
        count++;
        delay(5);
    }

    if (count >= 10) {
        return "error";
    }

    bme.setTemperatureOversampling(BME680_OS_8X);
    bme.setHumidityOversampling(BME680_OS_2X);
    bme.setPressureOversampling(BME680_OS_4X);
    bme.setIIRFilterSize(BME680_FILTER_SIZE_3);

    bme.setGasHeater(320, 150); 

    return "ok";
}

String read_bme680() {
    if (!bme.performReading()) {
        return "error";
    }

    return  String(bme.temperature, 2) + "," + 
            String(bme.humidity, 2) + "," + 
            String(bme.pressure / 100.0, 2) + "," + 
            String(bme.gas_resistance / 1000.0, 2);
}
