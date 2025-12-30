/**
 * Custom ESP32 Board Example
 *
 * This example demonstrates using a custom ESP32 board with the Gowin platform.
 * The platform now supports ESP32 boards directly without needing to reference
 * the espressif32 platform separately.
 */

#include <Arduino.h>
#include <FastLED.h>

// LED configuration
#define LED_PIN 21
#define NUM_LEDS 1
CRGB leds[NUM_LEDS];

// FPGA communication pins (defined in platformio.ini)
#ifndef FPGA_RESET_PIN
#define FPGA_RESET_PIN 26
#endif

void setup() {
    // Initialize serial communication
    Serial.begin(115200);
    delay(1000);

    Serial.println("\n\n=================================");
    Serial.println("Custom ESP32+FPGA Board Example");
    Serial.println("=================================\n");

    // Initialize LED
    FastLED.addLeds<WS2812B, LED_PIN, GRB>(leds, NUM_LEDS);
    FastLED.setBrightness(50);

    // Initialize FPGA reset pin
    pinMode(FPGA_RESET_PIN, OUTPUT);
    digitalWrite(FPGA_RESET_PIN, HIGH);

    Serial.println("ESP32 initialized successfully!");
    Serial.printf("CPU Frequency: %d MHz\n", getCpuFrequencyMhz());
    Serial.printf("Flash Size: %d MB\n", ESP.getFlashChipSize() / (1024 * 1024));
    Serial.printf("Free Heap: %d bytes\n", ESP.getFreeHeap());

#ifdef FPGA_ENABLED
    Serial.println("FPGA support: ENABLED");
#else
    Serial.println("FPGA support: DISABLED");
#endif

    Serial.println("\nStarting main loop...\n");
}

void loop() {
    static uint8_t hue = 0;
    static unsigned long lastPrint = 0;

    // Cycle through rainbow colors on LED
    leds[0] = CHSV(hue++, 255, 255);
    FastLED.show();

    // Print status every second
    if (millis() - lastPrint > 1000) {
        Serial.printf("Running... Free Heap: %d bytes\n", ESP.getFreeHeap());
        lastPrint = millis();
    }

    delay(10);
}
