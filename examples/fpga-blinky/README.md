# FPGA Blinky Example

Pure FPGA project demonstrating LED blinking pattern on Gowin FPGA.

## Hardware

**Target Hardware**: Tang Primer 20K module or standalone GW5A-25A board with discrete LEDs

**Note for Papilio RetroCade Users**: This example is designed for boards with discrete LEDs (like Tang Primer 20K). The Papilio RetroCade board only has a single RGB LED that requires different control logic (WS2812/SK6812 protocol). For RGB LED control on Papilio RetroCade, use the `papilio-blinky` example instead, which demonstrates proper RGB LED control via the ESP32.

## Features

- Simple rotating LED pattern
- Mixed HDL design (Verilog + VHDL example)
- VHDL counter module demonstration
- Automatic source file discovery
- Multiple upload protocol support

## Building

```bash
pio run
```

## Uploading

```bash
# Via pesptool (ESP32 SPI bridge)
pio run -t upload

# Or specify protocol in platformio.ini:
# upload_protocol = openfpgaloader
# upload_protocol = gowin
```

## Pin Assignments

**CRITICAL**: The pin assignments in `fpga/constraints/pins.cst` are for **Tang Primer 20K** hardware only. They **will not work** on Papilio RetroCade without modification.

**Papilio RetroCade** does not have discrete LEDs - it has only a single RGB LED (WS2812/SK6812) that cannot be controlled with simple GPIO pins. To use this example on Papilio RetroCade:
1. Remove the LED pin assignments from `pins.cst`
2. Add your own peripheral pin assignments (buttons, sensors, etc.)
3. Or use the `papilio-blinky` example which demonstrates RGB LED control

### Default Pins (Tang Primer 20K Only)

- Clock: H11 (27 MHz oscillator)
- Reset: F11
- LEDs: E11, D11, C11, B11, A11, A10 (6 discrete LEDs)

## Customization

### Change LED Pattern

Edit `fpga/src/blinky.v` and modify the pattern logic.

### Add More Modules

Create additional `.v` files in `fpga/src/` - they will be automatically included.

### Add IP Cores

1. Open `fpga/project.gprj` in Gowin IDE
2. Add IP cores (PLL, RAM, etc.) through the GUI
3. Save and build with `pio run`

## Project Structure

```
fpga-blinky/
├── platformio.ini          # Build configuration
├── fpga/
│   ├── project.gprj       # Gowin project file
│   ├── src/
│   │   └── blinky.v       # Top module
│   └── constraints/
│       └── pins.cst       # Pin assignments
```
