// Papilio Automatic Library Builder - ESP32 Main Template
//
// This file demonstrates marker-based code injection. The regions between
// PAPILIO_AUTO_*_BEGIN and PAPILIO_AUTO_*_END markers are auto-generated.
// User code outside markers is preserved during regeneration.
//
// To disable auto-generation for a section, simply remove its markers.

//# PAPILIO_AUTO_INCLUDES_BEGIN
// Auto-generated includes
#include <PapilioSPISlave.h>
#include <PapilioWBRegister.h>
#include <RGBLed.h>
//# PAPILIO_AUTO_INCLUDES_END

// User includes (preserved)
#include <Arduino.h>

//# PAPILIO_AUTO_GLOBALS_BEGIN
// Auto-generated global objects
PapilioSPISlave papilioSpiSlave;
PapilioWBRegister papilioWbRegister(0x0x1000);
PapilioRgbLed papilioWishboneRgbLed(0x2000);
//# PAPILIO_AUTO_GLOBALS_END

// User global variables (preserved)
unsigned long lastPrint = 0;

void setup() {
    // Initialize serial for debugging
    Serial.begin(115200);
    delay(1000);
    
    Serial.println("=================================");
    Serial.println("Papilio Auto-Builder Example");
    Serial.println("=================================");
    
    //# PAPILIO_AUTO_INIT_BEGIN
// Auto-generated initialization
papilioSpiSlave.begin();
papilioWbRegister.begin();
    if (!papilioWishboneRgbLed.begin()) {
        Serial.println("Failed to initialize RGB LED");
    }
//# PAPILIO_AUTO_INIT_END
    
    // User setup code (preserved)
    Serial.println("Setup complete!");
}

void loop() {
    // User loop code (preserved)
    if (millis() - lastPrint > 1000) {
        lastPrint = millis();
        Serial.println("Running...");
    }
    
    //# PAPILIO_AUTO_CLI_BEGIN
// Auto-generated CLI dispatcher
#ifdef PAPILIO_CLI_ENABLED

void papilio_cli_dispatch(const char* cmd) {
    if (strncmp(cmd, "reg.read", 8) == 0) {
        papilioWbRegister.cliRead(cmd + 9);
        return;
    }
    if (strncmp(cmd, "reg.write", 9) == 0) {
        papilioWbRegister.cliWrite(cmd + 10);
        return;
    }
    Serial.println("Unknown command");
}

#endif // PAPILIO_CLI_ENABLED
//# PAPILIO_AUTO_CLI_END
}
