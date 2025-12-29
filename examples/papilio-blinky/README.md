# Papilio RetroCade Blinky Example

Dual-target example demonstrating ESP32-S3 and Gowin FPGA communication via SPI.

## Hardware

- ESP32-S3 SuperMini (MCU)
- Gowin GW5A-25A FPGA (Tang Primer 20K)
- Papilio RetroCade Board

## Features

- ESP32 SPI master communication with FPGA
- FPGA LED blinky pattern
- SPI slave interface on FPGA
- Serial console commands for testing

## Building

```bash
# Build both ESP32 and FPGA
pio run

# Build ESP32 only
pio run -e esp32_only

# Build FPGA only
pio run -e fpga_only
```

## Uploading

```bash
# Upload both ESP32 firmware and FPGA bitstream
pio run -t upload
```

## Usage

1. Connect to serial monitor: `pio device monitor`
2. Send commands:
   - `r` - Reset FPGA
   - `i` - Read FPGA ID
   - `0-9` - Set LED pattern
   - `h` - Show help

## Pin Assignments

**IMPORTANT**: Verify pin assignments in `fpga/constraints/pins.cst` match your actual hardware before building!

### ESP32-S3 to FPGA SPI

- CLK: GPIO 12
- MISO: GPIO 9
- MOSI: GPIO 11
- CS: GPIO 10
- RST: GPIO 26

## Customization

### Add IP Cores

1. Open `fpga/project.gprj` in Gowin IDE
2. Add IP cores through the GUI
3. Save the project
4. Build with `pio run` - your IP cores will be preserved

### Modify FPGA Design

Edit Verilog files in `fpga/src/` - they will be automatically discovered and added to the build.

### Add Constraints

Add `.cst` files to `fpga/constraints/` - they will be automatically included.
