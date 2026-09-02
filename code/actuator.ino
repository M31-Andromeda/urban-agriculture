#include <Wire.h>


String actuator_initialization() {
    pinMode(6, OUTPUT); // Water Pump
    analogWrite(6, 0);

    pinMode(5, OUTPUT); // Fans
    analogWrite(5, 0);
    return "ok";
}

String set_actuator(int pin, int state) {
    analogWrite(pin, state);
    return "ok";
}