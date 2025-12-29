#include <Arduino.h>
#include <SPI.h>

// ESP32-S3 pins connected to FPGA (from Papilio RetroCade schematic)
#define FPGA_SPI_CS    10  // ESP32 GPIO10 -> FPGA pin A9
#define FPGA_SPI_CLK   12  // ESP32 GPIO12 -> FPGA pin B12
#define FPGA_SPI_MOSI  11  // ESP32 GPIO11 -> FPGA pin B11
#define FPGA_SPI_MISO  13  // ESP32 GPIO13 -> FPGA pin C12

SPIClass* fpgaSPI = nullptr;
uint8_t testPattern = 0;

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n=== Papilio RetroCade - ESP32 + FPGA Test ===");
  
  // Initialize SPI for FPGA communication
  fpgaSPI = new SPIClass(FSPI);  // Use FSPI peripheral
  fpgaSPI->begin(FPGA_SPI_CLK, FPGA_SPI_MISO, FPGA_SPI_MOSI, FPGA_SPI_CS);
  
  pinMode(FPGA_SPI_CS, OUTPUT);
  digitalWrite(FPGA_SPI_CS, HIGH);
  
  Serial.println("FPGA SPI Interface initialized");
  Serial.printf("  CS:   GPIO%d\n", FPGA_SPI_CS);
  Serial.printf("  CLK:  GPIO%d\n", FPGA_SPI_CLK);
  Serial.printf("  MOSI: GPIO%d\n", FPGA_SPI_MOSI);
  Serial.printf("  MISO: GPIO%d\n", FPGA_SPI_MISO);
}

void loop() {
  // Send test pattern to FPGA
  digitalWrite(FPGA_SPI_CS, LOW);
  uint8_t response = fpgaSPI->transfer(testPattern);
  digitalWrite(FPGA_SPI_CS, HIGH);
  
  Serial.printf("Sent: 0x%02X -> Received: 0x%02X\n", testPattern, response);
  
  testPattern++;
  delay(500);
}
