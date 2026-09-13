#include <Wire.h>

// Sets the pump and fan pins to LOW (off).
String actuator_initialization() {
    pinMode(6, OUTPUT); // Water Pump
    analogWrite(6, 0);

    pinMode(5, OUTPUT); // Fans
    analogWrite(5, 0);
    return "ok";
}

// Writes a PWM value to the given pin (called from Python over Bridge).
String set_actuator(int pin, int state) {
    analogWrite(pin, state);
    return "ok";
}