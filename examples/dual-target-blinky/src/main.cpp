/**
 * Papilio RetroCade - Simple GPIO Pass-through Example
 * ESP32-S3 + FPGA
 * 
 * Simple test: ESP32 toggles GPIO1, FPGA passes it through to all PMOD pins.
 * 
 * Hardware:
 * - ESP32-S3 SuperMini
 * - Gowin GW2A-18 FPGA (Papilio RetroCade)
 * 
 * Connections:
 * - ESP32 GPIO 1 -> FPGA gpio1_in (A9)
 * - FPGA drives all 8 PMOD pins with the same signal
 */

#include <Arduino.h>

// Pin definitions
#define GPIO1_PIN 1    // GPIO pin connected to FPGA (maps to A9 - ESP32_GPIO1)

void setup() {
    // Initialize serial for debugging
    Serial.begin(115200);
    delay(1000);
    
    Serial.println("\n\n");
    Serial.println("===========================================");
    Serial.println("  Papilio RetroCade - GPIO Pass-through");
    Serial.println("===========================================");
    Serial.println();
    Serial.println("ESP32 will toggle GPIO1 to control PMOD pins");
    Serial.print("Using GPIO ");
    Serial.println(GPIO1_PIN);
    Serial.println();
    
    // Configure GPIO1 as output
    pinMode(GPIO1_PIN, OUTPUT);
    digitalWrite(GPIO1_PIN, LOW);
    
    Serial.println("Setup complete - starting toggle loop\n");
}

void loop() {
    static unsigned long lastToggle = 0;
    static bool toggleState = false;
    
    // Toggle pin every second
    if (millis() - lastToggle > 1000) {
        toggleState = !toggleState;
        digitalWrite(GPIO1_PIN, toggleState ? HIGH : LOW);
        
        Serial.print("GPIO1: ");
        Serial.println(toggleState ? "HIGH" : "LOW");
        
        lastToggle = millis();
    }
    
    delay(10);
}
