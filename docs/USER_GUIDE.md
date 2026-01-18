# Automatic Library Integration - User Guide

Complete guide to using the automatic library integration feature in the Gowin FPGA Platform for PlatformIO.

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [How It Works](#how-it-works)
4. [Using Papilio Libraries](#using-papilio-libraries)
5. [Library Metadata Reference](#library-metadata-reference)
6. [Constraint Management](#constraint-management)
7. [Build Process](#build-process)
8. [Troubleshooting](#troubleshooting)

## Overview

The automatic library integration feature eliminates manual FPGA project file editing by automatically discovering and integrating gateware from PlatformIO libraries. When you add Papilio libraries to your project, their FPGA modules, constraint files, and ESP32 firmware are seamlessly integrated into your build.

### Key Benefits

- **Zero Configuration**: Add library to `lib_deps`, start using modules immediately
- **Board Portability**: Libraries provide constraint files for each supported board
- **Consistent Structure**: All Papilio libraries follow standard conventions
- **Dual Interface**: Programmatic API + optional CLI interface via PapilioOS
- **Version Control Friendly**: No manual `.gprj` file modifications

### What Gets Integrated Automatically

When you add a library dependency:

1. **FPGA Gateware** - Verilog/VHDL modules from `gateware/` directory
2. **Pin Constraints** - Board-specific `.cst` files for your target board
3. **ESP32 Firmware** - Arduino-compatible C++ classes
4. **CLI Interface** - Optional interactive commands (when PapilioOS enabled)

## Quick Start

### 1. Add Library Dependencies

Edit your `platformio.ini`:

```ini
[env:myproject]
platform = gowin
board = papilio_retrocade
framework = arduino

lib_deps = 
    papilio_wishbone_bus      ; SPI-Wishbone bridge
    papilio_wb_register       ; Register block
    papilio_wb_bram           ; Block RAM
```

### 2. Use Modules in FPGA Design

Create `fpga/src/top.v`:

```verilog
module top (
    input wire clk_27mhz,
    
    // SPI interface (auto-constrained by library)
    input  wire spi_sclk,
    input  wire spi_mosi,
    output wire spi_miso,
    input  wire spi_cs_n
);

// Wishbone bus from papilio_wishbone_bus library
wire [15:0] wb_adr;
wire [31:0] wb_dat_o, wb_dat_i;
wire wb_we, wb_cyc, wb_stb, wb_ack;

pwb_spi_wb_bridge #(
    .DATA_WIDTH(32)
) wb_bridge (
    .clk(clk_27mhz),
    .rst(1'b0),
    .spi_sclk(spi_sclk),
    .spi_mosi(spi_mosi),
    .spi_miso(spi_miso),
    .spi_cs_n(spi_cs_n),
    .wb_adr_o(wb_adr),
    .wb_dat_o(wb_dat_o),
    .wb_dat_i(wb_dat_i),
    .wb_we_o(wb_we),
    .wb_cyc_o(wb_cyc),
    .wb_stb_o(wb_stb),
    .wb_ack_i(wb_ack)
);

// Register block from papilio_wb_register library
wb_register_block #(
    .BASE_ADDR(16'h0000),
    .DATA_WIDTH(32)
) registers (
    .wb_clk_i(clk_27mhz),
    .wb_rst_i(1'b0),
    .wb_adr_i(wb_adr),
    .wb_dat_i(wb_dat_o),
    .wb_dat_o(wb_dat_i),
    .wb_we_i(wb_we),
    .wb_cyc_i(wb_cyc),
    .wb_stb_i(wb_stb),
    .wb_ack_o(wb_ack)
);

endmodule
```

### 3. Use API in ESP32 Firmware

Create `src/main.cpp`:

```cpp
#include <Arduino.h>
#include <WishboneSPI.h>
#include <PapilioWbRegister.h>

PapilioWbRegister registers(0x0000);

void setup() {
    Serial.begin(115200);
    
    // Initialize Wishbone bus
    if (!WishboneSPI.begin()) {
        Serial.println("Failed to initialize Wishbone SPI");
        return;
    }
    
    // Initialize register block
    if (!registers.begin()) {
        Serial.println("Failed to initialize registers");
        return;
    }
    
    Serial.println("System initialized");
}

void loop() {
    // Write to register 0
    registers.write(0, 0x12345678);
    
    // Read back
    uint32_t value = registers.read(0);
    Serial.printf("Register 0: 0x%08X\n", value);
    
    delay(1000);
}
```

### 4. Build and Upload

```bash
# Build everything
pio run

# Upload to hardware
pio run -t upload

# Monitor output
pio device monitor
```

**That's it!** The builder automatically:
- Discovered `pwb_spi_wb_bridge.v` and `wb_register_block.v`
- Added appropriate constraint files for Papilio RetroCade
- Compiled ESP32 firmware with library APIs
- Generated bitstream ready for upload

## How It Works

### Library Discovery Process

During the build, the FPGA builder:

1. **Scans dependencies** in `lib_deps` from `platformio.ini`
2. **Searches each library** for a `gateware/` directory
3. **Discovers HDL files**: `*.v`, `*.sv`, `*.vhd`, `*.vhdl`
4. **Finds constraint files** matching your board name
5. **Adds all discovered files** to the FPGA build
6. **Preserves order** (project files first, then libraries)

### Build Output Example

```
Building FPGA Gateware...
Found 2 Verilog, 0 VHDL, 1 constraint files

Library gateware discovered:
  - libs/papilio_wishbone_bus/gateware/*.v (3 files)
    - pwb_spi_wb_bridge.v
    - wb_arbiter.v
    - wb_decoder.v
  - libs/papilio_wb_register/gateware/*.v (1 files)
    - wb_register_block.v
  - libs/papilio_wb_bram/gateware/*.v (2 files)
    - wb_bram.v
    - fifo_sync.v

Adding library constraints:
  - libs/papilio_wishbone_bus/gateware/constraints/papilio_retrocade.cst
  - libs/papilio_wb_bram/gateware/constraints/papilio_retrocade.cst

Analyzing all files...
GowinSynthesis finish
Placement and routing...
[SUCCESS] Bitstream generated
```

### File Discovery Rules

The builder automatically includes:

- **Project HDL**: `fpga/src/**/*.{v,sv,vhd,vhdl}`
- **Project Constraints**: `fpga/constraints/**/*.cst`
- **Library Gateware**: `<library>/gateware/**/*.{v,sv,vhd,vhdl}`
- **Library Constraints**: `<library>/gateware/constraints/<board_name>.cst`

Files are added in this order:
1. Project HDL files (alphabetically)
2. Library HDL files (in dependency order)
3. Project constraints
4. Library constraints

## Using Papilio Libraries

### Available Libraries

Core infrastructure libraries:

- **papilio_wishbone_bus** - SPI to Wishbone bridge, utilities
- **papilio_spi_slave** - Low-level SPI slave interface
- **papilio_os** - CLI framework for interactive development

Wishbone peripheral libraries:

- **papilio_wb_register** - Simple register block (8 registers)
- **papilio_wb_bram** - Block RAM with burst support
- **papilio_wishbone_rgb_led** - WS2812B LED controller

### Installing Libraries

Libraries can be installed from:

**GitHub (recommended for development):**
```ini
lib_deps = 
    https://github.com/Papilio-Labs/papilio_wishbone_bus.git
    https://github.com/Papilio-Labs/papilio_wb_register.git
```

**Local workspace (for library development):**
```ini
lib_extra_dirs = 
    ../path/to/libs

lib_deps = 
    papilio_wishbone_bus
    papilio_wb_register
```

**PlatformIO Registry (future):**
```ini
lib_deps = 
    papilio/papilio_wishbone_bus
```

### Using Library APIs

Each library provides an Arduino-compatible C++ API:

```cpp
#include <WishboneSPI.h>      // papilio_wishbone_bus
#include <PapilioWbRegister.h> // papilio_wb_register
#include <PapilioWbBram.h>     // papilio_wb_bram
#include <PapilioRgbLed.h>     // papilio_wishbone_rgb_led

// Initialize Wishbone bus (do this first)
WishboneSPI.begin();

// Create library instances with base addresses
PapilioWbRegister registers(0x0000);
PapilioWbBram bram(0x1000, 4096);  // 4KB memory
PapilioRgbLed rgbled(0x2000);

void setup() {
    // Initialize each peripheral
    registers.begin();
    bram.begin();
    rgbled.begin();
    
    // Use APIs
    registers.write(0, 0x12345678);
    bram.write32(0, 0xDEADBEEF);
    rgbled.setRGB(0, 255, 0, 0);  // Red
}
```

### Enabling CLI Interface (Optional)

For interactive development, enable PapilioOS CLI:

```ini
[env:myproject]
platform = gowin
board = papilio_retrocade
framework = arduino

build_flags = 
    -DENABLE_PAPILIO_OS    ; Enable CLI interface

lib_deps = 
    papilio_os              ; CLI framework (add first)
    papilio_wishbone_bus
    papilio_wb_register
    papilio_wb_bram
```

Each library automatically registers CLI commands:

```
Papilio OS v0.2.0
Type 'help' for commands

> wb_register list
Registers at base 0x0000:
  [0] 0x00000000
  [1] 0x00000000
  ...

> wb_bram info
BRAM at 0x1000: 4096 bytes (1024 words)

> rgbled setrgb 0 255 0 0
LED 0 set to RGB(255, 0, 0)
```

## Library Metadata Reference

### Understanding library.json

Every Papilio library includes a `library.json` with metadata:

```json
{
  "name": "papilio_wb_register",
  "version": "0.2.0",
  "description": "8-register Wishbone peripheral",
  
  "papilio": {
    "gateware": {
      "modules": [
        {
          "name": "wb_register_block",
          "file": "gateware/wb_register_block.v",
          "description": "8-register block with Wishbone interface",
          "parameters": {
            "BASE_ADDR": {
              "type": "integer",
              "default": "16'h0000",
              "description": "Base address in Wishbone address space"
            },
            "DATA_WIDTH": {
              "type": "integer",
              "default": 32,
              "description": "Register width (8, 16, 24, or 32 bits)"
            }
          },
          "ports": {
            "wb_clk_i": "Wishbone clock input",
            "wb_rst_i": "Wishbone reset input",
            "wb_adr_i": "16-bit address input",
            "wb_dat_i": "Data input (DATA_WIDTH bits)",
            "wb_dat_o": "Data output (DATA_WIDTH bits)",
            "wb_we_i": "Write enable",
            "wb_cyc_i": "Cycle strobe",
            "wb_stb_i": "Data strobe",
            "wb_ack_o": "Acknowledge output"
          }
        }
      ],
      "constraints": [
        {
          "board": "papilio_retrocade",
          "file": "gateware/constraints/papilio_retrocade.cst",
          "signals": []
        }
      ]
    },
    
    "wishbone": {
      "data_width": 32,
      "addr_width": 16,
      "supports_burst": false,
      "address_range": {
        "description": "8 consecutive addresses starting at BASE_ADDR"
      }
    },
    
    "esp32": {
      "class": "PapilioWbRegister",
      "header": "PapilioWbRegister.h",
      "namespace": null,
      "dependencies": ["WishboneSPI"]
    },
    
    "cli": {
      "enabled": true,
      "module_name": "wb_register",
      "commands": [
        {
          "name": "list",
          "description": "List all register values",
          "usage": "wb_register list"
        },
        {
          "name": "read",
          "description": "Read a specific register",
          "usage": "wb_register read <index>"
        },
        {
          "name": "write",
          "description": "Write to a specific register",
          "usage": "wb_register write <index> <value>"
        }
      ]
    }
  }
}
```

### Metadata Sections

**gateware** - FPGA module information:
- `modules[]` - List of Verilog/VHDL modules
- `constraints[]` - Board-specific constraint files

**wishbone** - Bus interface specification:
- `data_width` - Data bus width (8, 16, 24, 32)
- `addr_width` - Address bus width (typically 16)
- `supports_burst` - Whether burst transfers are supported
- `address_range` - Address space requirements

**esp32** - Firmware API information:
- `class` - C++ class name
- `header` - Include file name
- `dependencies` - Required libraries

**cli** - Command-line interface (optional):
- `module_name` - CLI module identifier
- `commands[]` - Available commands with descriptions

## Constraint Management

### Board-Specific Constraints

Libraries provide constraint files for each supported board:

```
papilio_wishbone_bus/
└── gateware/
    └── constraints/
        ├── papilio_retrocade.cst
        └── papilio_synth.cst
```

The builder automatically selects the file matching your board:

```ini
[env:myproject]
board = papilio_retrocade  ; Selects papilio_retrocade.cst
```

### Constraint Priority and Overrides

Constraints are applied in this order:

1. **Project constraints**: `fpga/constraints/*.cst` (highest priority)
2. **Library constraints**: In dependency order (lower priority)

**Example:** Override library SPI pin assignments:

`fpga/constraints/pins.cst` (your project):
```
# Override SPI pins from library
IO_LOC "spi_sclk" 45;
IO_PORT "spi_sclk" IO_TYPE=LVCMOS33;
```

Your project constraint takes precedence over the library's default.

### Common Signal Names

Papilio libraries use standardized signal naming:

**Clock and Reset:**
- `clk_27mhz` - Main 27 MHz system clock
- `rst_n` - Active-low reset

**SPI Interface (from papilio_wishbone_bus):**
- `spi_sclk` - SPI clock
- `spi_mosi` - Master out, slave in
- `spi_miso` - Master in, slave out
- `spi_cs_n` - Active-low chip select

**RGB LED (from papilio_wishbone_rgb_led):**
- `rgb_led_out` - WS2812B data output

**PMODs and External I/O:**
- `pmod_*` - PMOD connector signals
- Check library documentation for specific signals

### Minimal Project Constraints

For most projects, you only need to constrain top-level I/O:

```
# Minimal constraints - library handles SPI pins
IO_LOC "clk_27mhz" 52;
IO_PORT "clk_27mhz" IO_TYPE=LVCMOS33;

# Your custom signals
IO_LOC "led_out" 10;
IO_PORT "led_out" IO_TYPE=LVCMOS33 PULL_MODE=NONE DRIVE=8;
```

SPI, Wishbone internal signals, and standard interfaces are handled by libraries.

## Build Process

### Build Stages

The FPGA builder executes these stages:

1. **Dependency Scanning**
   - Reads `lib_deps` from platformio.ini
   - Resolves library paths
   - Checks for `gateware/` directories

2. **File Discovery**
   - Scans project `fpga/src/` for HDL
   - Scans library `gateware/` for HDL
   - Finds constraint files matching board

3. **Project File Update**
   - Backs up `fpga/project.gprj`
   - Adds discovered files to `.gprj`
   - Preserves IP cores and custom settings

4. **Synthesis**
   - Runs Gowin synthesizer via `gw_sh`
   - Analyzes all HDL files
   - Generates netlist

5. **Place and Route**
   - Places logic in FPGA fabric
   - Routes connections
   - Applies timing constraints

6. **Bitstream Generation**
   - Creates `.fs` bitstream
   - Copies to build directory
   - Ready for upload

### Build Commands

```bash
# Full build (FPGA + ESP32)
pio run

# FPGA only
pio run -e fpga

# ESP32 only (in dual-target projects)
pio run -e esp32

# Clean rebuild (recommended after library changes)
pio run -e fpga -t clean -t upload

# Verbose output
pio run -v

# Upload to hardware
pio run -t upload
```

### Build Output Location

After successful build:

```
.pio/build/fpga/
├── project.fs          # FPGA bitstream
└── project.bin         # Binary format (for pesptool)

fpga/impl/
├── gwsynthesis/
│   └── *.vg           # Synthesized netlist
└── pnr/
    ├── *.rpt          # Timing reports
    └── *.pnr          # Place and route database
```

## Troubleshooting

### Library Gateware Not Found

**Symptom:** Module not found in FPGA build

**Causes:**
1. Library not in `lib_deps`
2. No `gateware/` directory in library
3. Typo in module name

**Solution:**
```bash
# Verify library is installed
pio pkg list

# Check for gateware directory
ls libs/papilio_*/gateware/

# Enable verbose build
pio run -v
```

### Constraint File Conflicts

**Symptom:** Pin assignment errors during place and route

**Causes:**
1. Multiple constraints for same signal
2. Invalid pin number for package
3. Signal name mismatch

**Solution:**
```bash
# Check which constraints are loaded
pio run -v | grep "Adding.*constraints"

# Verify signal names match between .v and .cst
grep "IO_LOC" fpga/constraints/*.cst
grep "input\|output" fpga/src/top.v
```

### Module Parameter Mismatches

**Symptom:** Synthesis errors about parameter types

**Causes:**
1. Wrong parameter value type
2. Missing required parameters
3. Parameter outside valid range

**Solution:**

Check library documentation for valid parameters:

```verilog
// Correct - using library defaults
wb_register_block #(
    .BASE_ADDR(16'h0000),  // 16-bit hex literal
    .DATA_WIDTH(32)         // Integer literal
) registers (
    // ...
);

// Incorrect - wrong literal format
wb_register_block #(
    .BASE_ADDR(0x0000),    // Missing width and base
    .DATA_WIDTH("32")       // String instead of integer
) registers (
    // ...
);
```

### Wishbone Bus Connection Issues

**Symptom:** FPGA loads but ESP32 can't communicate

**Causes:**
1. Missing SPI pin constraints
2. Wrong base addresses (overlap)
3. Clock domain issues
4. Unconnected Wishbone signals

**Solution:**

Verify connections systematically:

```verilog
// 1. Check all Wishbone signals connected
pwb_spi_wb_bridge bridge (
    .clk(clk_27mhz),        // ✓ Clock
    .rst(1'b0),             // ✓ Reset
    .spi_sclk(spi_sclk),    // ✓ SPI
    .spi_mosi(spi_mosi),
    .spi_miso(spi_miso),
    .spi_cs_n(spi_cs_n),
    .wb_adr_o(wb_adr),      // ✓ All WB signals
    .wb_dat_o(wb_dat_o),
    .wb_dat_i(wb_dat_i),
    .wb_we_o(wb_we),
    .wb_cyc_o(wb_cyc),
    .wb_stb_o(wb_stb),
    .wb_ack_i(wb_ack)       // ✓ Acknowledge
);

// 2. Verify address ranges don't overlap
// Register: 0x0000-0x0007 (8 addresses)
// BRAM:     0x1000-0x1FFF (4KB)
// RGB LED:  0x2000-0x2003 (4 addresses)
```

### Build Performance Issues

**Symptom:** Slow builds with many libraries

**Solutions:**

1. **Use local library cache:**
   ```ini
   lib_extra_dirs = 
       ../papilio_libs  ; Local cache of libraries
   ```

2. **Clean only when needed:**
   ```bash
   # Normal build (fast, incremental)
   pio run
   
   # Clean build (slow, when libraries change)
   pio run -t clean
   ```

3. **Disable unused libraries:**
   ```ini
   lib_deps = 
       papilio_wishbone_bus
       # papilio_wb_bram    ; Comment out if not used
   ```

### Common Error Messages

**Error:** `CT1135 - Pin XX is undefined in package`
- **Cause:** Wrong pin number in constraint file
- **Fix:** Check device datasheet, verify package type matches

**Error:** `MODULE 'xyz' is not found`
- **Cause:** Missing library or typo in module name
- **Fix:** Verify library installed, check module name spelling

**Error:** `Address conflict at 0xXXXX`
- **Cause:** Overlapping address ranges
- **Fix:** Adjust BASE_ADDR parameters to avoid overlap

**Error:** `SPI timeout`
- **Cause:** FPGA not programmed or SPI pins wrong
- **Fix:** Upload FPGA bitstream, verify constraints

### Getting Help

1. **Check library documentation:**
   - Each library has `README.md` and `AI_SKILL.md`
   - Review register maps and usage examples

2. **Enable verbose output:**
   ```bash
   pio run -v
   ```

3. **Check example projects:**
   - See `examples/` in platform repository
   - Working reference implementations

4. **Community support:**
   - GitHub Issues: Platform and library repositories
   - Discord: Papilio Labs community
   - Forum: PlatformIO community

## Next Steps

- **Developer Guide** - Learn to create auto-discoverable libraries
- **Migration Guide** - Convert existing projects to use automatic integration
- **Examples** - Study complete working projects in `examples/`
- **API Reference** - Detailed API documentation for each library

---

**Version:** 1.0.0  
**Last Updated:** January 2026  
**Platform:** Gowin FPGA Platform for PlatformIO
