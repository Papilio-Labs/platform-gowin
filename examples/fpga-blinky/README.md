# FPGA Blinky Example

Pure FPGA project demonstrating LED blinking pattern on Gowin FPGA.

## Hardware

**Target Hardware**: Papilio RetroCade (Gowin GW2AR-18)

**Note**: This example uses the PMOD connector pins as outputs. You'll need to connect external LEDs (with appropriate resistors) to the PMOD connector to see the blinking pattern. The Papilio RetroCade does not have on-board discrete LEDs, only a WS2812 RGB LED.

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

Pin assignments are defined in `fpga/constraints/pins.cst` for the **Papilio RetroCade** board.

### Papilio RetroCade Pins

- **Clock**: ESP32_GPIO1 (A9) - Requires ESP32 to provide clock signal
- **Reset**: ESP32_GPIO2 (L12) - Active low
- **LED Outputs** (PMOD connector):
  - led[0]: PMOD_IOA0 (N9)
  - led[1]: PMOD_IOA1 (R9)
  - led[2]: PMOD_IOA2 (N8)
  - led[3]: PMOD_IOA3 (L9)
  - led[4]: PMOD_IOB0 (L8)
  - led[5]: PMOD_IOB1 (M6)

**Important**: Connect LEDs with appropriate current-limiting resistors to the PMOD pins. The PMOD connector outputs 3.3V logic levels.

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
