# Creating Papilio-Compatible Libraries - Developer Guide

Complete guide for library developers to create auto-discoverable libraries compatible with the Papilio automatic library integration system.

## Table of Contents

1. [Overview](#overview)
2. [Library Structure Standards](#library-structure-standards)
3. [Metadata Schema Reference](#metadata-schema-reference)
4. [Creating Gateware](#creating-gateware)
5. [Board-Specific Constraints](#board-specific-constraints)
6. [ESP32 Firmware API](#esp32-firmware-api)
7. [CLI Interface Integration](#cli-interface-integration)
8. [Testing Your Library](#testing-your-library)
9. [Publishing Guidelines](#publishing-guidelines)
10. [Reference Implementation](#reference-implementation)

## Overview

### What Makes a Library Auto-Discoverable?

A Papilio-compatible library provides three integrated components:

1. **FPGA Gateware** - Wishbone-compatible Verilog/VHDL modules
2. **ESP32 Firmware** - Arduino-compatible C++ API
3. **Optional CLI** - Interactive commands for PapilioOS

When users add your library to `lib_deps`, the build system automatically:
- Discovers and includes gateware modules
- Adds board-specific pin constraints
- Links firmware API to user code
- Registers CLI commands (if enabled)

### Design Philosophy

**Zero-Configuration Integration:**
- Users shouldn't edit project files manually
- Library provides everything needed for target boards
- Sensible defaults, configurable via parameters

**Consistency:**
- Standard Wishbone bus interface
- Predictable API patterns
- Common CLI command conventions

**Portability:**
- Support multiple boards via constraint files
- Parameterizable designs for flexibility
- Clear documentation of requirements

## Library Structure Standards

### Required Directory Layout

```
papilio_<library_name>/
├── library.json              # PlatformIO + Papilio metadata
├── README.md                 # User documentation
├── AI_SKILL.md               # AI assistant instructions
├── examples/
│   └── <Name>Example/
│       └── <Name>Example.ino
├── src/                      # ESP32 firmware
│   ├── Papilio<Name>.h       # Main API header
│   ├── Papilio<Name>.cpp     # Main API implementation
│   ├── Papilio<Name>OS.h     # CLI plugin header (conditional)
│   └── Papilio<Name>OS.cpp   # CLI implementation (conditional)
├── gateware/                 # FPGA modules (auto-discovered)
│   ├── README.md
│   ├── <module_name>.v       # Verilog modules
│   └── constraints/
│       ├── papilio_retrocade.cst
│       └── papilio_synth.cst
└── tests/                    # Optional test infrastructure
    ├── sim/                  # Verilog simulations
    └── hw/                   # Hardware tests
```

### Naming Conventions

**Library Name:**
- Format: `papilio_<functionality>`
- Example: `papilio_wb_register`, `papilio_wishbone_rgb_led`
- Use snake_case (lowercase with underscores)

**Class Names:**
- Format: `Papilio<Name>`
- Example: `PapilioWbRegister`, `PapilioRgbLed`
- Use PascalCase

**Module Names (Gateware):**
- Format: `<prefix>_<name>`
- Example: `wb_register_block`, `ws2812b_driver`
- Use snake_case

**CLI Module Names:**
- Format: lowercase, short
- Example: `wb_register`, `rgbled`
- Keep 2-12 characters for usability

## Metadata Schema Reference

### library.json Structure

```json
{
  "name": "papilio_<library_name>",
  "version": "0.1.0",
  "description": "Brief description for users",
  "keywords": ["papilio", "wishbone", "fpga", "gowin"],
  "authors": [
    {
      "name": "Your Name",
      "email": "you@example.com",
      "maintainer": true
    }
  ],
  "license": "MIT",
  "homepage": "https://github.com/yourusername/papilio_<library_name>",
  "repository": {
    "type": "git",
    "url": "https://github.com/yourusername/papilio_<library_name>.git"
  },
  "frameworks": ["arduino"],
  "platforms": ["espressif32"],
  
  "dependencies": [
    {
      "name": "papilio_wishbone_bus",
      "version": "*"
    },
    {
      "name": "papilio_os",
      "version": "*",
      "optional": true
    }
  ],
  
  "export": {
    "include": [
      "src/*.h",
      "src/*.cpp",
      "gateware/*.v",
      "gateware/*.sv",
      "gateware/*.vhd",
      "gateware/constraints/*.cst",
      "README.md",
      "AI_SKILL.md",
      "examples/*"
    ]
  },
  
  "papilio": {
    "gateware": {
      "modules": [
        {
          "name": "your_module_name",
          "file": "gateware/your_module.v",
          "description": "Clear description of module purpose",
          "parameters": {
            "BASE_ADDR": {
              "type": "integer",
              "default": "16'h0000",
              "description": "Wishbone base address"
            },
            "DATA_WIDTH": {
              "type": "integer",
              "default": 32,
              "description": "Data bus width (8/16/24/32)"
            }
          },
          "ports": {
            "wb_clk_i": "Wishbone clock input",
            "wb_rst_i": "Wishbone reset input",
            "wb_adr_i": "Address input (16-bit)",
            "wb_dat_i": "Data input",
            "wb_dat_o": "Data output",
            "wb_we_i": "Write enable",
            "wb_cyc_i": "Cycle valid",
            "wb_stb_i": "Strobe",
            "wb_ack_o": "Acknowledge output"
          }
        }
      ],
      "constraints": [
        {
          "board": "papilio_retrocade",
          "file": "gateware/constraints/papilio_retrocade.cst",
          "signals": [
            {
              "name": "external_pin",
              "pin": "23",
              "description": "External signal connection"
            }
          ]
        }
      ]
    },
    
    "wishbone": {
      "data_width": 32,
      "addr_width": 16,
      "supports_burst": false,
      "address_range": {
        "description": "How much address space required",
        "size_bytes": 32,
        "alignment": "Must be aligned to size boundary"
      }
    },
    
    "esp32": {
      "class": "PapilioYourLibrary",
      "header": "PapilioYourLibrary.h",
      "namespace": null,
      "dependencies": ["WishboneSPI"]
    },
    
    "cli": {
      "enabled": true,
      "module_name": "yourlib",
      "commands": [
        {
          "name": "status",
          "description": "Show device status",
          "usage": "yourlib status"
        },
        {
          "name": "read",
          "description": "Read from device",
          "usage": "yourlib read <address>"
        }
      ]
    }
  }
}
```

### Metadata Field Descriptions

**Standard PlatformIO Fields:**
- `name` - Unique library identifier (must start with `papilio_`)
- `version` - Semantic version (major.minor.patch)
- `description` - One-line summary (max 200 chars)
- `keywords` - Search terms for discovery
- `authors[]` - Creator and maintainer information
- `dependencies[]` - Required libraries

**Papilio Extensions:**

**gateware.modules[]:**
- `name` - Module name as used in Verilog `module` statement
- `file` - Relative path to module file
- `description` - Clear explanation of module purpose
- `parameters` - Configurable module parameters
- `ports` - All module ports with descriptions

**gateware.constraints[]:**
- `board` - Board identifier from board definition
- `file` - Relative path to constraint file
- `signals[]` - External signals with pin assignments

**wishbone:**
- `data_width` - Data bus width (8, 16, 24, or 32)
- `addr_width` - Address bus width (typically 16)
- `supports_burst` - Boolean for burst transfer capability
- `address_range` - Address space requirements and alignment

**esp32:**
- `class` - C++ class name
- `header` - Include file name
- `namespace` - C++ namespace (null if none)
- `dependencies` - Required ESP32 libraries

**cli:**
- `enabled` - Boolean for CLI support
- `module_name` - Short CLI identifier
- `commands[]` - Available commands with usage

## Creating Gateware

### Wishbone Interface Standard

All Papilio gateware modules MUST implement standard Wishbone Classic interface:

```verilog
module your_module_name #(
    parameter BASE_ADDR  = 16'h0000,  // Configurable base address
    parameter DATA_WIDTH = 32          // Configurable data width
) (
    // System signals
    input  wire                  clk,
    input  wire                  rst,
    
    // Wishbone classic slave interface
    input  wire [15:0]           wb_adr_i,   // 16-bit byte address
    input  wire [DATA_WIDTH-1:0] wb_dat_i,   // Data input
    output reg  [DATA_WIDTH-1:0] wb_dat_o,   // Data output
    input  wire                  wb_we_i,    // Write enable
    input  wire                  wb_cyc_i,   // Cycle valid
    input  wire                  wb_stb_i,   // Strobe
    output reg                   wb_ack_o,   // Acknowledge
    
    // External hardware interface
    output wire                  external_signal_out,
    input  wire                  external_signal_in
);

// Address decode - match BASE_ADDR
wire address_match = wb_cyc_i && wb_stb_i && 
                     (wb_adr_i >= BASE_ADDR) && 
                     (wb_adr_i < BASE_ADDR + 16'h0010);  // 16 bytes

// Register map (example: 4 registers)
reg [DATA_WIDTH-1:0] reg0, reg1, reg2, reg3;

// Wishbone interface logic
always @(posedge clk) begin
    if (rst) begin
        wb_ack_o <= 1'b0;
        wb_dat_o <= {DATA_WIDTH{1'b0}};
        reg0 <= {DATA_WIDTH{1'b0}};
        reg1 <= {DATA_WIDTH{1'b0}};
        reg2 <= {DATA_WIDTH{1'b0}};
        reg3 <= {DATA_WIDTH{1'b0}};
    end else begin
        wb_ack_o <= address_match && !wb_ack_o;  // Single-cycle ack
        
        if (address_match && !wb_ack_o) begin
            if (wb_we_i) begin
                // Write operation
                case (wb_adr_i[3:0])  // Bottom 4 bits select register
                    4'h0: reg0 <= wb_dat_i;
                    4'h4: reg1 <= wb_dat_i;
                    4'h8: reg2 <= wb_dat_i;
                    4'hC: reg3 <= wb_dat_i;
                endcase
            end else begin
                // Read operation
                case (wb_adr_i[3:0])
                    4'h0: wb_dat_o <= reg0;
                    4'h4: wb_dat_o <= reg1;
                    4'h8: wb_dat_o <= reg2;
                    4'hC: wb_dat_o <= reg3;
                    default: wb_dat_o <= {DATA_WIDTH{1'b0}};
                endcase
            end
        end
    end
end

// Your custom logic here
assign external_signal_out = reg0[0];

endmodule
```

### Wishbone Timing Requirements

**Single-Cycle Transfers:**
```
     ___     ___     ___     ___     ___
clk     |___|   |___|   |___|   |___|   
        _______________________
cyc    |                       |_______
        _______________________
stb    |                       |_______
        _______________________
we     |                       |_______  (for writes)
        _______________________
adr    X__valid_addr___________X_______
        _______________________
dat_i  X__valid_data___________X_______  (for writes)
                _______________________
ack            |                       | (respond in 1 cycle)
                _______________________
dat_o          X__valid_data___________X (for reads)
```

**Key Rules:**
1. Assert `ack_o` ONE cycle after `stb_i && cyc_i`
2. De-assert `ack_o` after one cycle
3. Hold `dat_o` valid when `ack_o` asserted (reads)
4. Sample `dat_i` when `we_i && ack_o` (writes)

### Address Map Documentation

**MUST document register map in three places:**

1. **Module header comments:**
```verilog
//
// Register Map (relative to BASE_ADDR):
// 0x00: Control Register
//   [0]    enable     - Enable module (1=on, 0=off)
//   [1]    reset      - Software reset (write 1)
//   [7:2]  reserved   - Must write 0
// 0x04: Status Register (read-only)
//   [0]    ready      - Module ready (1=ready)
//   [1]    error      - Error flag (1=error)
// 0x08: Data Register
//   [31:0] data       - Data value
//
```

2. **gateware/README.md**
3. **Main library README.md**

### Module Parameters

**Standard Parameters:**

```verilog
parameter BASE_ADDR  = 16'h0000;  // Wishbone base address
parameter DATA_WIDTH = 32;         // 8, 16, 24, or 32
```

**Optional Parameters:**

```verilog
parameter ADDR_WIDTH = 10;         // For memory blocks
parameter FIFO_DEPTH = 8;          // For FIFOs
parameter CLOCK_FREQ = 27000000;   // For timing logic
```

**Document all parameters** in module comments and metadata.

### Multiple Module Libraries

Libraries can provide multiple modules:

```
gateware/
├── main_module.v        # Primary module
├── helper_module.v      # Supporting module
└── fifo_sync.v          # Utility module
```

All `.v`/`.sv`/`.vhd` files are automatically included. Document instantiation relationships in README.

## Board-Specific Constraints

### Constraint File Requirements

**Create one `.cst` file per supported board:**

```
gateware/constraints/
├── papilio_retrocade.cst   # Papilio RetroCade
└── papilio_synth.cst       # Papilio Synth
```

### Constraint File Format

```
# Papilio RetroCade Constraint File
# Library: papilio_your_library
# Module: your_module_name

# External output signal
IO_LOC "external_signal_out" 23;
IO_PORT "external_signal_out" IO_TYPE=LVCMOS33 PULL_MODE=NONE DRIVE=8;

# External input signal
IO_LOC "external_signal_in" 24;
IO_PORT "external_signal_in" IO_TYPE=LVCMOS33 PULL_MODE=UP;

# Multi-bit bus example
IO_LOC "data_out[0]" 25;
IO_LOC "data_out[1]" 26;
IO_LOC "data_out[2]" 27;
IO_LOC "data_out[3]" 28;
IO_PORT "data_out[0]" IO_TYPE=LVCMOS33 DRIVE=8;
IO_PORT "data_out[1]" IO_TYPE=LVCMOS33 DRIVE=8;
IO_PORT "data_out[2]" IO_TYPE=LVCMOS33 DRIVE=8;
IO_PORT "data_out[3]" IO_TYPE=LVCMOS33 DRIVE=8;
```

### IO Standards and Electrical Properties

**IO_TYPE:**
- `LVCMOS33` - 3.3V CMOS (most common)
- `LVCMOS18` - 1.8V CMOS
- `LVTTL33` - 3.3V TTL

**PULL_MODE:**
- `UP` - Internal pull-up resistor
- `DOWN` - Internal pull-down resistor
- `NONE` - No pull resistor (external required)

**DRIVE:**
- `4` - 4mA drive strength (low power)
- `8` - 8mA drive strength (standard)
- `12` - 12mA drive strength (high current)
- `16` - 16mA drive strength (max)

**Example Guidelines:**
```
# Inputs - use pull resistors for floating inputs
IO_TYPE=LVCMOS33 PULL_MODE=UP     # Pull-up for active-low
IO_TYPE=LVCMOS33 PULL_MODE=DOWN   # Pull-down for active-high

# Outputs - drive strength by load
IO_TYPE=LVCMOS33 DRIVE=4          # LEDs, low-speed signals
IO_TYPE=LVCMOS33 DRIVE=8          # Standard digital I/O
IO_TYPE=LVCMOS33 DRIVE=12         # Heavy loads, long traces
```

### Signal Naming Conventions

**Use descriptive, consistent names:**

```verilog
// Good
module rgb_led_controller (
    output wire rgb_led_out,     // Clear purpose
    input  wire button_n,        // Active-low suffix
    output wire [7:0] led_array  // Width indicated
);

// Bad
module rgb_led_controller (
    output wire out,    // Too generic
    input  wire b,      // Cryptic
    output wire [7:0] l // Unclear
);
```

### Board Pin Assignment References

**Papilio RetroCade (GW5A-25A):**
- See `papilio_gowin_pio/misc/cst/Papilio_RetroCade.cst` for full pinout
- Common pins: PMOD connectors (pins 23-30), RGB LED (pin 79)

**Papilio Synth:**
- See board documentation for pinout
- Standard Arduino-compatible pin headers

**Document your pin choices** in constraint file comments.

## ESP32 Firmware API

### Header File Structure

`src/PapilioYourLibrary.h`:

```cpp
#ifndef PAPILIO_YOUR_LIBRARY_H
#define PAPILIO_YOUR_LIBRARY_H

#include <Arduino.h>
#include <WishboneSPI.h>  // Always required for Wishbone access

class PapilioYourLibrary {
public:
    // Constructor with base address
    PapilioYourLibrary(uint16_t baseAddress = 0x0000);
    
    // Initialize hardware
    bool begin();
    
    // Public API methods
    bool enable();
    bool disable();
    bool isReady();
    
    uint32_t read(uint8_t reg);
    void write(uint8_t reg, uint32_t value);
    
    // High-level convenience methods
    void setMode(uint8_t mode);
    uint8_t getStatus();
    
private:
    uint16_t _baseAddress;
    
    // Register offsets
    static const uint8_t REG_CONTROL = 0x00;
    static const uint8_t REG_STATUS  = 0x04;
    static const uint8_t REG_DATA    = 0x08;
    
    // Bit masks
    static const uint32_t CTRL_ENABLE = 0x01;
    static const uint32_t CTRL_RESET  = 0x02;
    static const uint32_t STAT_READY  = 0x01;
    static const uint32_t STAT_ERROR  = 0x02;
    
    // Helper methods
    uint32_t readReg(uint8_t offset);
    void writeReg(uint8_t offset, uint32_t value);
};

#endif
```

### Implementation File

`src/PapilioYourLibrary.cpp`:

```cpp
#include "PapilioYourLibrary.h"

PapilioYourLibrary::PapilioYourLibrary(uint16_t baseAddress)
    : _baseAddress(baseAddress) {
}

bool PapilioYourLibrary::begin() {
    // Verify Wishbone bus is initialized
    if (!WishboneSPI.isInitialized()) {
        return false;
    }
    
    // Perform initial setup
    writeReg(REG_CONTROL, CTRL_RESET);  // Reset module
    delay(10);  // Wait for reset
    
    // Verify module responds
    uint32_t status = readReg(REG_STATUS);
    return (status & STAT_READY) != 0;
}

bool PapilioYourLibrary::enable() {
    uint32_t ctrl = readReg(REG_CONTROL);
    ctrl |= CTRL_ENABLE;
    writeReg(REG_CONTROL, ctrl);
    return true;
}

bool PapilioYourLibrary::disable() {
    uint32_t ctrl = readReg(REG_CONTROL);
    ctrl &= ~CTRL_ENABLE;
    writeReg(REG_CONTROL, ctrl);
    return true;
}

bool PapilioYourLibrary::isReady() {
    uint32_t status = readReg(REG_STATUS);
    return (status & STAT_READY) != 0;
}

uint32_t PapilioYourLibrary::read(uint8_t reg) {
    return readReg(reg);
}

void PapilioYourLibrary::write(uint8_t reg, uint32_t value) {
    writeReg(reg, value);
}

// Private helper methods
uint32_t PapilioYourLibrary::readReg(uint8_t offset) {
    return WishboneSPI.read32(_baseAddress + offset);
}

void PapilioYourLibrary::writeReg(uint8_t offset, uint32_t value) {
    WishboneSPI.write32(_baseAddress + offset, value);
}
```

### API Design Guidelines

**1. Constructor takes base address:**
```cpp
// Good - flexible address
PapilioYourLibrary(uint16_t baseAddress = 0x0000);

// Bad - hardcoded address
PapilioYourLibrary();  // Uses fixed 0x1000
```

**2. Initialize in `begin()`:**
```cpp
bool begin() {
    // Verify bus ready
    // Reset hardware
    // Check device presence
    return success;
}
```

**3. Provide high-level methods:**
```cpp
// Good - clear intent
void setColor(uint8_t r, uint8_t g, uint8_t b);

// Bad - low-level
void writeReg(uint8_t reg, uint32_t val);
```

**4. Use consistent naming:**
```cpp
bool enable();     // Actions are verbs
bool isReady();    // State queries use is/has/get
uint8_t getStatus();
```

**5. Document register usage:**
```cpp
// Register map constants with comments
static const uint8_t REG_CONTROL = 0x00;  // Control register
static const uint8_t REG_STATUS  = 0x04;  // Status register (RO)
```

## CLI Interface Integration

### CLI Header File

`src/PapilioYourLibraryOS.h`:

```cpp
#ifndef PAPILIO_YOUR_LIBRARY_OS_H
#define PAPILIO_YOUR_LIBRARY_OS_H

#ifdef ENABLE_PAPILIO_OS  // Only compile when CLI enabled

#include <PapilioOS.h>
#include "PapilioYourLibrary.h"

class PapilioYourLibraryOS {
public:
    PapilioYourLibraryOS(PapilioYourLibrary* device);
    
private:
    PapilioYourLibrary* _device;
    
    // Command handlers
    static void handleStatus(int argc, char** argv);
    static void handleRead(int argc, char** argv);
    static void handleWrite(int argc, char** argv);
    static void handleHelp(int argc, char** argv);
    static void handleTutorial(int argc, char** argv);
    
    // Singleton instance for callbacks
    static PapilioYourLibraryOS* _instance;
};

#endif // ENABLE_PAPILIO_OS
#endif
```

### CLI Implementation

`src/PapilioYourLibraryOS.cpp`:

```cpp
#include "PapilioYourLibraryOS.h"

#ifdef ENABLE_PAPILIO_OS

PapilioYourLibraryOS* PapilioYourLibraryOS::_instance = nullptr;

PapilioYourLibraryOS::PapilioYourLibraryOS(PapilioYourLibrary* device)
    : _device(device) {
    
    _instance = this;
    
    // Register all commands
    PapilioOS.registerCommand("yourlib", "status", handleStatus, 
                              "Show device status");
    PapilioOS.registerCommand("yourlib", "read", handleRead,
                              "Read register: yourlib read <addr>");
    PapilioOS.registerCommand("yourlib", "write", handleWrite,
                              "Write register: yourlib write <addr> <value>");
    PapilioOS.registerCommand("yourlib", "help", handleHelp,
                              "Show all commands");
    PapilioOS.registerCommand("yourlib", "tutorial", handleTutorial,
                              "Interactive tutorial");
}

void PapilioYourLibraryOS::handleStatus(int argc, char** argv) {
    if (!_instance || !_instance->_device) return;
    
    Serial.println("\n=== Your Library Status ===");
    Serial.printf("Ready: %s\n", 
                  _instance->_device->isReady() ? "Yes" : "No");
    Serial.printf("Status: 0x%02X\n", 
                  _instance->_device->getStatus());
    Serial.println();
}

void PapilioYourLibraryOS::handleRead(int argc, char** argv) {
    if (!_instance || !_instance->_device) return;
    
    if (argc < 2) {
        Serial.println("Usage: yourlib read <address>");
        return;
    }
    
    uint8_t addr = strtoul(argv[1], nullptr, 0);
    uint32_t value = _instance->_device->read(addr);
    Serial.printf("Register 0x%02X: 0x%08X\n", addr, value);
}

void PapilioYourLibraryOS::handleWrite(int argc, char** argv) {
    if (!_instance || !_instance->_device) return;
    
    if (argc < 3) {
        Serial.println("Usage: yourlib write <address> <value>");
        return;
    }
    
    uint8_t addr = strtoul(argv[1], nullptr, 0);
    uint32_t value = strtoul(argv[2], nullptr, 0);
    _instance->_device->write(addr, value);
    Serial.printf("Wrote 0x%08X to register 0x%02X\n", value, addr);
}

void PapilioYourLibraryOS::handleHelp(int argc, char** argv) {
    Serial.println("\n=== Your Library Commands ===");
    Serial.println("yourlib status          - Show device status");
    Serial.println("yourlib read <addr>     - Read register");
    Serial.println("yourlib write <addr> <val> - Write register");
    Serial.println("yourlib tutorial        - Interactive tutorial");
    Serial.println("yourlib help            - This help");
    Serial.println();
}

void PapilioYourLibraryOS::handleTutorial(int argc, char** argv) {
    if (!_instance || !_instance->_device) return;
    
    auto tutorialStep = [](const char* desc, const char* cmd) {
        Serial.println(desc);
        Serial.print("Press Enter to continue...");
        while (!Serial.available()) delay(10);
        while (Serial.available()) Serial.read();
        Serial.println();
        PapilioOS.executeCommand(cmd);
    };
    
    Serial.println("\n╔════════════════════════════════════╗");
    Serial.println("║  Your Library Interactive Tutorial ║");
    Serial.println("╚════════════════════════════════════╝\n");
    
    tutorialStep(
        "Step 1: Check device status",
        "yourlib status"
    );
    
    tutorialStep(
        "Step 2: Read control register",
        "yourlib read 0"
    );
    
    tutorialStep(
        "Step 3: Write test value",
        "yourlib write 8 0xDEADBEEF"
    );
    
    tutorialStep(
        "Step 4: Read back value",
        "yourlib read 8"
    );
    
    Serial.println("✓ Tutorial complete!");
    Serial.println("Type 'yourlib help' for all commands\n");
}

#endif // ENABLE_PAPILIO_OS
```

### Required CLI Commands

**Every library MUST implement:**

1. `<module> status` - Show device state
2. `<module> help` - List all commands
3. `<module> tutorial` - Interactive walkthrough

**Additional commands as needed:**
- `read/write` - Register access
- Device-specific functions

### Tutorial Pattern

**Requirements:**
- Work without fully configured hardware
- Present steps sequentially
- Wait for Enter between steps
- Execute commands internally
- Support early exit

Use the `tutorialStep()` helper pattern shown above.

## Testing Your Library

### Directory Structure

```
tests/
├── sim/                      # Verilog simulations
│   ├── README.md
│   ├── tb_your_module.v      # Testbench
│   ├── run_sim.py            # Test runner
│   └── expected_output.txt   # Golden reference
└── hw/                       # Hardware tests
    ├── README.md
    ├── platformio.ini
    └── test/
        └── test_your_library.cpp
```

### Simulation Testing

`tests/sim/tb_your_module.v`:

```verilog
`timescale 1ns/1ps

module tb_your_module;

reg clk, rst;
reg [15:0] wb_adr_i;
reg [31:0] wb_dat_i;
wire [31:0] wb_dat_o;
reg wb_we_i, wb_cyc_i, wb_stb_i;
wire wb_ack_o;

// DUT instantiation
your_module #(
    .BASE_ADDR(16'h0000),
    .DATA_WIDTH(32)
) dut (
    .clk(clk),
    .rst(rst),
    .wb_adr_i(wb_adr_i),
    .wb_dat_i(wb_dat_i),
    .wb_dat_o(wb_dat_o),
    .wb_we_i(wb_we_i),
    .wb_cyc_i(wb_cyc_i),
    .wb_stb_i(wb_stb_i),
    .wb_ack_o(wb_ack_o)
);

// Clock generation
always #10 clk = ~clk;

// Wishbone write task
task wb_write(input [15:0] addr, input [31:0] data);
begin
    @(posedge clk);
    wb_adr_i <= addr;
    wb_dat_i <= data;
    wb_we_i <= 1;
    wb_cyc_i <= 1;
    wb_stb_i <= 1;
    @(posedge clk);
    while (!wb_ack_o) @(posedge clk);
    wb_cyc_i <= 0;
    wb_stb_i <= 0;
    @(posedge clk);
end
endtask

// Wishbone read task
task wb_read(input [15:0] addr, output [31:0] data);
begin
    @(posedge clk);
    wb_adr_i <= addr;
    wb_we_i <= 0;
    wb_cyc_i <= 1;
    wb_stb_i <= 1;
    @(posedge clk);
    while (!wb_ack_o) @(posedge clk);
    data = wb_dat_o;
    wb_cyc_i <= 0;
    wb_stb_i <= 0;
    @(posedge clk);
end
endtask

// Test sequence
initial begin
    // Initialize
    clk = 0;
    rst = 1;
    wb_adr_i = 0;
    wb_dat_i = 0;
    wb_we_i = 0;
    wb_cyc_i = 0;
    wb_stb_i = 0;
    
    #100 rst = 0;
    
    // Test 1: Write and read back
    $display("Test 1: Write/Read");
    wb_write(16'h0000, 32'h12345678);
    wb_read(16'h0000, wb_dat_i);
    if (wb_dat_i == 32'h12345678)
        $display("[PASS] Write/Read test");
    else
        $display("[FAIL] Expected 0x12345678, got 0x%08X", wb_dat_i);
    
    // Add more tests...
    
    #1000 $finish;
end

endmodule
```

### Hardware Testing

`tests/hw/test/test_your_library.cpp`:

```cpp
#include <Arduino.h>
#include <unity.h>
#include <WishboneSPI.h>
#include <PapilioYourLibrary.h>

PapilioYourLibrary device(0x0000);

void setUp(void) {
    WishboneSPI.begin();
    device.begin();
}

void tearDown(void) {
    // Clean up after each test
}

void test_device_ready(void) {
    TEST_ASSERT_TRUE(device.isReady());
}

void test_write_read(void) {
    device.write(0, 0x12345678);
    uint32_t value = device.read(0);
    TEST_ASSERT_EQUAL_HEX32(0x12345678, value);
}

void test_enable_disable(void) {
    device.enable();
    delay(10);
    TEST_ASSERT_TRUE(device.isReady());
    
    device.disable();
    delay(10);
    TEST_ASSERT_FALSE(device.isReady());
}

void setup() {
    delay(2000);  // Wait for serial
    UNITY_BEGIN();
    
    RUN_TEST(test_device_ready);
    RUN_TEST(test_write_read);
    RUN_TEST(test_enable_disable);
    
    UNITY_END();
}

void loop() {
    // Empty
}
```

## Publishing Guidelines

### Repository Setup

**1. Create GitHub repository:**
```bash
gh repo create papilio_your_library --public
cd papilio_your_library
git init
```

**2. Add standard files:**
- `README.md` - User documentation
- `LICENSE` - MIT recommended
- `library.json` - Complete metadata
- `.gitignore` - Standard Arduino/PlatformIO

**3. Tag releases:**
```bash
git tag -a v0.1.0 -m "Initial release"
git push origin v0.1.0
```

### Documentation Requirements

**README.md must include:**
1. Clear description and features
2. Hardware requirements
3. Installation instructions
4. Programmatic API examples
5. CLI interface examples (if applicable)
6. Register map documentation
7. Supported boards list
8. Pin assignments per board
9. Examples and tutorials
10. Contributing guidelines

**AI_SKILL.md must include:**
1. Library-specific instructions for AI
2. Complete register map with bit fields
3. Common operations (API + CLI + registers)
4. Board-specific pin assignments
5. Troubleshooting patterns
6. Reference to papilio_dev_tools for general skills

### Version Numbering

Follow Semantic Versioning (semver.org):

- **Major (X.0.0)** - Breaking API changes
- **Minor (0.X.0)** - New features, backward compatible
- **Patch (0.0.X)** - Bug fixes, no API changes

### Testing Before Release

**Required validation:**
- [ ] Simulation tests pass
- [ ] Hardware tests pass on all supported boards
- [ ] Examples compile and run
- [ ] Documentation complete
- [ ] Metadata validated (all boards have constraints)
- [ ] CLI tutorial works
- [ ] Compatible with latest papilio_os

### Continuous Integration

**Add GitHub Actions** for automated testing:

```yaml
# .github/workflows/test.yml
name: Test Library

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - name: Install PlatformIO
        run: pip install platformio
      - name: Run Tests
        run: pio test -e hardware_test
```

## Reference Implementation

### Study These Examples

**Minimal Reference:**
- `papilio_wb_register` - Simplest complete library
- Single module, clean patterns
- Good starting point

**Complete Reference:**
- `papilio_wishbone_bus` - Full-featured library
- Multiple modules, burst support
- Advanced patterns

**Template:**
- `papilio_lib_template` - Copy to start new library
- All standards included
- Rename and customize

### Getting Help

**Resources:**
- Template: `libs/papilio_lib_template/`
- Examples: Existing Papilio libraries
- Standards: `AGENTS.md` (Papilio Library Standards)
- Community: GitHub Discussions, Discord

### Contributing

Contributions welcome! Please:
1. Follow these standards
2. Test on real hardware
3. Document thoroughly
4. Submit pull requests

---

**Version:** 1.0.0  
**Last Updated:** January 2026  
**Platform:** Gowin FPGA Platform for PlatformIO
