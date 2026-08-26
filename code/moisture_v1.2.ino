#include <Wire.h>                  // Std Arduino lib - I2C COM


String read_capacitive_moisture_sensor_v1_2(int pin_index) {


    int pin = A0 + pin_index;

    long sum = 0;
    int num_samples = 10;
    
    for (int i = 0; i < num_samples; i++) {
        int val = analogRead(pin);
        sum += val;
        delay(5);
    }
    
    float average = (float)sum / num_samples;


    return String(average, 2);
}