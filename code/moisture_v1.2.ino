#include <Wire.h>                  // Std Arduino lib - I2C COM


#define NUM_ITERS 10;

String read_capacitive_moisture_sensor_v1_2(int pin_index) {


    int pin = A0 + pin_index;
    long sum = 0;
    int iters = NUM_ITERS;
    int num_iters = 0;
    
    for (int i = 0; i < iters; i++) {

        int val = analogRead(pin);
        if (val < 3 || val > 1020 ) {
            continue;
        }

        num_iters++;
        sum += val;
        delay(5);
    }
    
    float average = (float)sum / num_iters;



    return String(average, 2);
}