# FPGA Blinky Example

Pure FPGA project demonstrating LED blinking pattern on Gowin FPGA.

## Hardware

- Gowin GW5A-25A FPGA (Tang Primer 20K module)
- Papilio RetroCade Board (or any Tang Primer 20K compatible board)

## Features

- Simple rotating LED pattern
- Pure Verilog design (no MCU code)
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

**IMPORTANT**: The pin assignments in `fpga/constraints/pins.cst` are examples. 
Verify them against your actual hardware schematic before building!

### Default Pins (Tang Primer 20K)

- Clock: H11 (27 MHz oscillator)
- Reset: F11
- LEDs: E11, D11, C11, B11, A11, A10

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
