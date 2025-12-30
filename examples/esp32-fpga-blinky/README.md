# ESP32 + Gowin FPGA Dual-Target Blinky Example

This example demonstrates how to develop dual-target projects combining ESP32-S3 microcontroller with Gowin FPGA using PlatformIO.

## Features

- **ESP32-S3** running Arduino framework
- **Gowin FPGA** with Verilog HDL design
- **Automatic dual-target build**: FPGA bitstream builds after ESP32 firmware
- **SPI communication** between ESP32 and FPGA
- **FPGA status monitoring** via CDONE pin
- **FPGA reset control** from ESP32

## Hardware Requirements

- Board with ESP32-S3 + Gowin FPGA (e.g., Papilio RetroCade)
- USB cable for programming
- LEDs connected to FPGA outputs (8 LEDs for full demo)

## Pin Connections

### ESP32 → FPGA Interface

| Signal | ESP32 GPIO | FPGA Pin | Description |
|--------|-----------|----------|-------------|
| SPI CS | GPIO 10 | (board specific) | SPI chip select |
| SPI SCK | GPIO 12 | (board specific) | SPI clock |
| SPI MOSI | GPIO 11 | (board specific) | SPI data to FPGA |
| SPI MISO | GPIO 13 | (board specific) | SPI data from FPGA |
| RESET | GPIO 14 | (board specific) | FPGA reset control |
| CDONE | GPIO 21 | (board specific) | FPGA configuration status |

**⚠️ Important:** Update `fpga/constraints/pins.cst` with your actual hardware pin assignments!

## Project Structure

```
esp32-fpga-blinky/
├── platformio.ini          # Platform configuration
├── src/
│   └── main.cpp           # ESP32 Arduino code
└── fpga/
    ├── project.gprj       # Gowin FPGA project file
    ├── src/
    │   └── top.v          # FPGA Verilog code
    └── constraints/
        └── pins.cst       # FPGA pin assignments
```

## Building

### Build Both Targets

```bash
pio run
```

This will:
1. Compile ESP32 firmware (Arduino)
2. Synthesize FPGA bitstream (Gowin)
3. Generate uploadable binaries

### Build Only ESP32

```bash
pio run --target build
```

### Upload to Hardware

Upload ESP32 firmware:
```bash
pio run --target upload
```

For FPGA programming, see your board's specific instructions (typically via pesptool or dedicated FPGA programmer).

## How It Works

### ESP32 Side (main.cpp)

1. Initializes serial communication at 115200 baud
2. Sets up onboard LED for blinking
3. Configures FPGA interface pins (SPI, reset, CDONE)
4. Resets the FPGA and checks configuration status
5. Initializes SPI for FPGA communication
6. Sends counter values to FPGA every 5 seconds

### FPGA Side (top.v)

1. Implements rotating LED pattern (Knight Rider style)
2. Receives SPI data from ESP32
3. Updates internal counter based on ESP32 commands
4. Runs independently at 27 MHz

### Communication Protocol

Simple SPI protocol:
- **Byte 0**: Command (0x01 = set counter)
- **Byte 1**: Counter high byte
- **Byte 2**: Counter low byte

## Customization

### Modify LED Pattern

Edit `fpga/src/top.v` and change the `blink_pattern` logic:

```verilog
// Example: Binary counter instead of rotating pattern
blink_pattern <= blink_pattern + 1;
```

### Change SPI Protocol

Modify both:
- ESP32: `src/main.cpp` - function `loop()`
- FPGA: `fpga/src/top.v` - SPI receiver logic

### Add More Features

Ideas to extend this example:
- Read FPGA status back to ESP32 via SPI MISO
- Control LED speed from ESP32
- Add button inputs on FPGA
- Implement bidirectional communication

## Pin Constraint Template

The `fpga/constraints/pins.cst` file contains template pin assignments. You **must** update these to match your hardware!

To find the correct pins for your board:
1. Check your board schematic
2. Refer to FPGA datasheet for package pinout
3. Use Gowin IDE's pin planner tool

## Troubleshooting

### FPGA Not Configured (CDONE Low)

- Verify FPGA bitstream was built successfully
- Check FPGA programming procedure
- Ensure proper power supply to FPGA
- Verify pin constraints are correct

### SPI Communication Not Working

- Check pin assignments in both ESP32 code and FPGA constraints
- Verify SPI wiring connections
- Use logic analyzer to debug SPI signals
- Check that FPGA is configured before ESP32 starts communication

### Build Errors

**"gw_sh not found"**
- Install Gowin EDA toolchain
- Set `GOWIN_HOME` environment variable or `board_build.gowin_path` in platformio.ini

**"No such file: project.gprj"**
- Ensure you're in the project root directory
- Check that `fpga/project.gprj` exists

## Serial Monitor Output

Expected output:
```
=================================
ESP32 + Gowin FPGA Dual-Target
=================================

✓ ESP32 LED initialized

FPGA Interface:
  SPI CS:    GPIO10
  SPI MOSI:  GPIO11
  SPI MISO:  GPIO13
  SPI SCK:   GPIO12
  Reset:     GPIO14
  CDONE:     GPIO21

Resetting FPGA... ✓ FPGA is configured!
✓ SPI initialized for FPGA communication

Starting blink loop...

Sent counter to FPGA: 5
ESP32 uptime: 10 seconds
Sent counter to FPGA: 10
ESP32 uptime: 20 seconds
```

## Resources

- [Gowin Semiconductor](https://www.gowinsemi.com/)
- [ESP32-S3 Datasheet](https://www.espressif.com/en/products/socs/esp32-s3)
- [PlatformIO Documentation](https://docs.platformio.org/)
- [Platform-Gowin GitHub](https://github.com/Papilio-Labs/platform-gowin)

## License

Apache-2.0 - See LICENSE file for details.
