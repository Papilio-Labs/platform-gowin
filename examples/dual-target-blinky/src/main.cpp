/**
 * Papilio RetroCade - ESP32-S3 + FPGA Example
 * 
 * This example demonstrates basic communication between the ESP32-S3 and
 * the Gowin FPGA via SPI. The ESP32 acts as SPI master and can send
 * commands and data to the FPGA.
 * 
 * Hardware:
 * - ESP32-S3 SuperMini
 * - Gowin GW5A-25A FPGA (Tang Primer 20K)
 * 
 * SPI Connections (configured in platformio.ini):
 * - CLK:  GPIO 12
 * - MISO: GPIO 9
 * - MOSI: GPIO 11
 * - CS:   GPIO 10
 * - RST:  GPIO 26 (FPGA reset)
 */

#include <Arduino.h>
#include <SPI.h>

// Pin definitions (from build flags in platformio.ini)
#ifndef FPGA_SPI_CLK
#define FPGA_SPI_CLK    12
#endif
#ifndef FPGA_SPI_MISO
#define FPGA_SPI_MISO   9
#endif
#ifndef FPGA_SPI_MOSI
#define FPGA_SPI_MOSI   11
#endif
#ifndef FPGA_SPI_CS
#define FPGA_SPI_CS     10
#endif
#ifndef FPGA_RESET_PIN
#define FPGA_RESET_PIN  26
#endif

// SPI settings
#define FPGA_SPI_FREQ   10000000  // 10 MHz
#define FPGA_SPI_MODE   SPI_MODE0

// Command definitions for FPGA communication
#define CMD_NOP         0x00
#define CMD_READ_ID     0x01
#define CMD_WRITE_REG   0x02
#define CMD_READ_REG    0x03
#define CMD_LED_CONTROL 0x10

SPIClass * fpgaSPI = nullptr;

/**
 * Initialize FPGA communication
 */
void fpgaInit() {
    Serial.println("Initializing FPGA interface...");
    
    // Configure FPGA reset pin
    pinMode(FPGA_RESET_PIN, OUTPUT);
    digitalWrite(FPGA_RESET_PIN, HIGH);
    
    // Configure chip select
    pinMode(FPGA_SPI_CS, OUTPUT);
    digitalWrite(FPGA_SPI_CS, HIGH);
    
    // Initialize SPI
    fpgaSPI = new SPIClass(HSPI);
    fpgaSPI->begin(FPGA_SPI_CLK, FPGA_SPI_MISO, FPGA_SPI_MOSI, FPGA_SPI_CS);
    
    delay(100);
    Serial.println("FPGA interface initialized");
}

/**
 * Reset the FPGA
 */
void fpgaReset() {
    Serial.println("Resetting FPGA...");
    digitalWrite(FPGA_RESET_PIN, LOW);
    delay(10);
    digitalWrite(FPGA_RESET_PIN, HIGH);
    delay(100);
    Serial.println("FPGA reset complete");
}

/**
 * Send a command to the FPGA and receive response
 */
uint8_t fpgaTransaction(uint8_t cmd, uint8_t data = 0x00) {
    digitalWrite(FPGA_SPI_CS, LOW);
    delayMicroseconds(1);
    
    fpgaSPI->beginTransaction(SPISettings(FPGA_SPI_FREQ, MSBFIRST, FPGA_SPI_MODE));
    fpgaSPI->transfer(cmd);
    uint8_t response = fpgaSPI->transfer(data);
    fpgaSPI->endTransaction();
    
    delayMicroseconds(1);
    digitalWrite(FPGA_SPI_CS, HIGH);
    
    return response;
}

/**
 * Read FPGA ID/version
 */
uint8_t fpgaReadID() {
    return fpgaTransaction(CMD_READ_ID);
}

/**
 * Control FPGA LEDs (if implemented in FPGA design)
 */
void fpgaSetLEDs(uint8_t pattern) {
    fpgaTransaction(CMD_LED_CONTROL, pattern);
}

/**
 * Write to FPGA register
 */
void fpgaWriteReg(uint8_t addr, uint8_t value) {
    digitalWrite(FPGA_SPI_CS, LOW);
    delayMicroseconds(1);
    
    fpgaSPI->beginTransaction(SPISettings(FPGA_SPI_FREQ, MSBFIRST, FPGA_SPI_MODE));
    fpgaSPI->transfer(CMD_WRITE_REG);
    fpgaSPI->transfer(addr);
    fpgaSPI->transfer(value);
    fpgaSPI->endTransaction();
    
    delayMicroseconds(1);
    digitalWrite(FPGA_SPI_CS, HIGH);
}

/**
 * Read from FPGA register
 */
uint8_t fpgaReadReg(uint8_t addr) {
    uint8_t value;
    
    digitalWrite(FPGA_SPI_CS, LOW);
    delayMicroseconds(1);
    
    fpgaSPI->beginTransaction(SPISettings(FPGA_SPI_FREQ, MSBFIRST, FPGA_SPI_MODE));
    fpgaSPI->transfer(CMD_READ_REG);
    fpgaSPI->transfer(addr);
    value = fpgaSPI->transfer(0x00);
    fpgaSPI->endTransaction();
    
    delayMicroseconds(1);
    digitalWrite(FPGA_SPI_CS, HIGH);
    
    return value;
}

void setup() {
    // Initialize serial for debugging
    Serial.begin(115200);
    while (!Serial && millis() < 3000) {
        ; // Wait for serial port to connect (max 3 seconds)
    }
    
    Serial.println("\n\n");
    Serial.println("===========================================");
    Serial.println("  Papilio RetroCade - ESP32-S3 + FPGA");
    Serial.println("===========================================");
    Serial.println();
    
#if FPGA_ENABLED
    // Initialize FPGA interface
    fpgaInit();
    
    // Optional: Reset FPGA on startup
    // fpgaReset();
    
    // Read FPGA ID
    uint8_t fpgaID = fpgaReadID();
    Serial.print("FPGA ID: 0x");
    Serial.println(fpgaID, HEX);
    
    Serial.println("\nFPGA interface ready");
#else
    Serial.println("FPGA support disabled (FPGA_ENABLED=0)");
#endif
    
    Serial.println("Setup complete\n");
}

void loop() {
#if FPGA_ENABLED
    // Example: Cycle through LED patterns
    static uint8_t ledPattern = 0;
    static unsigned long lastUpdate = 0;
    
    if (millis() - lastUpdate > 500) {
        ledPattern++;
        fpgaSetLEDs(ledPattern);
        
        Serial.print("LED Pattern: 0x");
        Serial.println(ledPattern, HEX);
        
        lastUpdate = millis();
    }
    
    // Check for serial commands
    if (Serial.available()) {
        char cmd = Serial.read();
        
        switch (cmd) {
            case 'r':
                // Reset FPGA
                fpgaReset();
                break;
                
            case 'i':
                // Read FPGA ID
                Serial.print("FPGA ID: 0x");
                Serial.println(fpgaReadID(), HEX);
                break;
                
            case '0'...'9':
                // Set LED pattern
                ledPattern = cmd - '0';
                fpgaSetLEDs(ledPattern);
                Serial.print("Set LED pattern: ");
                Serial.println(ledPattern);
                break;
                
            case 'h':
                // Help
                Serial.println("\nCommands:");
                Serial.println("  r - Reset FPGA");
                Serial.println("  i - Read FPGA ID");
                Serial.println("  0-9 - Set LED pattern");
                Serial.println("  h - Show this help");
                Serial.println();
                break;
        }
    }
#else
    // No FPGA - just blink onboard LED
    static unsigned long lastBlink = 0;
    static bool ledState = false;
    
    if (millis() - lastBlink > 1000) {
        ledState = !ledState;
        digitalWrite(LED_BUILTIN, ledState);
        Serial.println(ledState ? "LED ON" : "LED OFF");
        lastBlink = millis();
    }
#endif
    
    delay(10);
}
