/**
 * ESP32 + Gowin FPGA Dual-Target Blinky Example
 *
 * This example demonstrates:
 * 1. ESP32-S3 controlling an onboard LED
 * 2. ESP32 communicating with Gowin FPGA via SPI
 * 3. FPGA status monitoring (CDONE pin)
 * 4. FPGA reset control
 */

#include <Arduino.h>
#include <SPI.h>

// LED pins
#define LED_BUILTIN 48  // ESP32-S3 onboard LED

// FPGA interface pins (defined in platformio.ini and board config)
#ifndef FPGA_SPI_CS
#define FPGA_SPI_CS 10
#endif

#ifndef FPGA_SPI_MOSI
#define FPGA_SPI_MOSI 11
#endif

#ifndef FPGA_SPI_MISO
#define FPGA_SPI_MISO 13
#endif

#ifndef FPGA_SPI_SCK
#define FPGA_SPI_SCK 12
#endif

#ifndef FPGA_RESET_PIN
#define FPGA_RESET_PIN 14
#endif

#ifndef FPGA_CDONE_PIN
#define FPGA_CDONE_PIN 21
#endif

// SPI settings
SPIClass * fpga_spi = nullptr;

void setup() {
    Serial.begin(115200);
    delay(1000);

    Serial.println("\n\n=================================");
    Serial.println("ESP32 + Gowin FPGA Dual-Target");
    Serial.println("=================================\n");

    // Setup ESP32 LED
    pinMode(LED_BUILTIN, OUTPUT);
    Serial.println("✓ ESP32 LED initialized");

    #ifdef BOARD_HAS_FPGA
    // Setup FPGA control pins
    pinMode(FPGA_RESET_PIN, OUTPUT);
    pinMode(FPGA_CDONE_PIN, INPUT);
    pinMode(FPGA_SPI_CS, OUTPUT);
    digitalWrite(FPGA_SPI_CS, HIGH);  // CS idle high

    Serial.println("\nFPGA Interface:");
    Serial.printf("  SPI CS:    GPIO%d\n", FPGA_SPI_CS);
    Serial.printf("  SPI MOSI:  GPIO%d\n", FPGA_SPI_MOSI);
    Serial.printf("  SPI MISO:  GPIO%d\n", FPGA_SPI_MISO);
    Serial.printf("  SPI SCK:   GPIO%d\n", FPGA_SPI_SCK);
    Serial.printf("  Reset:     GPIO%d\n", FPGA_RESET_PIN);
    Serial.printf("  CDONE:     GPIO%d\n", FPGA_CDONE_PIN);

    // Reset FPGA (pulse low)
    Serial.print("\nResetting FPGA... ");
    digitalWrite(FPGA_RESET_PIN, LOW);
    delay(100);
    digitalWrite(FPGA_RESET_PIN, HIGH);
    delay(200);

    // Check FPGA configuration status
    bool fpga_configured = digitalRead(FPGA_CDONE_PIN);
    if (fpga_configured) {
        Serial.println("✓ FPGA is configured!");
    } else {
        Serial.println("⚠ FPGA not configured (CDONE low)");
        Serial.println("  Make sure to upload FPGA bitstream:");
        Serial.println("  pio run -t upload-fpga");
    }

    // Initialize SPI for FPGA communication
    fpga_spi = new SPIClass(HSPI);
    fpga_spi->begin(FPGA_SPI_SCK, FPGA_SPI_MISO, FPGA_SPI_MOSI, FPGA_SPI_CS);
    Serial.println("✓ SPI initialized for FPGA communication");

    #else
    Serial.println("⚠ Board does not have FPGA support");
    #endif

    Serial.println("\nStarting blink loop...\n");
}

uint32_t counter = 0;

void loop() {
    // Blink ESP32 LED
    digitalWrite(LED_BUILTIN, HIGH);
    delay(500);
    digitalWrite(LED_BUILTIN, LOW);
    delay(500);

    counter++;

    // Every 5 seconds, send data to FPGA via SPI
    #ifdef BOARD_HAS_FPGA
    if (counter % 5 == 0) {
        // Check if FPGA is still configured
        if (digitalRead(FPGA_CDONE_PIN)) {
            // Example: Send counter value to FPGA
            digitalWrite(FPGA_SPI_CS, LOW);
            fpga_spi->transfer(0x01);  // Command byte
            fpga_spi->transfer((counter >> 8) & 0xFF);  // Counter high byte
            fpga_spi->transfer(counter & 0xFF);         // Counter low byte
            digitalWrite(FPGA_SPI_CS, HIGH);

            Serial.printf("Sent counter to FPGA: %d\n", counter);
        } else {
            Serial.println("⚠ FPGA lost configuration!");
        }
    }
    #endif

    // Print status every 10 seconds
    if (counter % 10 == 0) {
        Serial.printf("ESP32 uptime: %d seconds\n", counter);
    }
}
