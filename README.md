# Papilio RetroCade - PlatformIO + Gowin FPGA Project

This project template supports building both ESP32-S3 firmware and Gowin FPGA gateware in a unified PlatformIO workflow. The FPGA bitstream is automatically built after ESP32 compilation and both can be uploaded in a single operation.

## Hardware

- **MCU**: ESP32-S3 SuperMini
- **FPGA**: Gowin GW5A-25A (Tang Primer 20K module)
- **Board**: Papilio RetroCade

## Features

- ✅ Dual-target build (ESP32 + FPGA) with single `pio run` command
- ✅ Automatic FPGA source file discovery and project sync
- ✅ Preserves user-added IP cores in Gowin project file
- ✅ Multiple upload protocols (pesptool, openFPGALoader, Gowin Programmer)
- ✅ SPI communication between ESP32 and FPGA
- ✅ Example LED blinky + SPI slave interface

## Prerequisites

### Required

1. **PlatformIO** - Install via VS Code extension or CLI
2. **Gowin EDA Educational** - Download from [Gowin Semiconductor](https://www.gowinsemi.com/)
3. **esptool** - Automatically installed by PlatformIO

### Optional (for different upload protocols)

- **pesptool** (default): `pip install git+https://github.com/Papilio-Labs/pesptool.git`
- **openFPGALoader**: [Installation guide](https://github.com/trabucayre/openFPGALoader)
- **Gowin Programmer**: Included with Gowin EDA

## Project Structure

```
papilio_gowin_pio/
├── platformio.ini          # PlatformIO configuration
├── src/                    # ESP32-S3 source code
│   └── main.cpp           # Main ESP32 application
├── fpga/                   # FPGA gateware
│   ├── src/
│   │   └── top.v          # Top-level Verilog module
│   ├── constraints/
│   │   └── pins.cst       # Pin constraint file
│   └── project.gprj       # Gowin project file (edit in Gowin IDE)
└── scripts/                # Build automation
    ├── build_fpga.py      # FPGA build script
    └── upload_dual.py     # Dual upload script
```

## Quick Start

### 1. Configure Gowin Toolchain

Set the `GOWIN_HOME` environment variable or edit `platformio.ini`:

```ini
board_build.gowin_path = C:/Gowin_V1.9.9
```

### 2. Update Pin Constraints

**IMPORTANT**: Edit `fpga/constraints/pins.cst` to match your actual hardware! The example pins are placeholders and must be verified against your board schematic.

### 3. Build

```bash
# Build both ESP32 and FPGA
pio run

# Build ESP32 only
pio run -e esp32_only

# Build FPGA only
pio run -e fpga_only
```

### 4. Upload

```bash
# Upload both ESP32 and FPGA (via pesptool)
pio run -t upload

# Upload with specific protocol
pio run -t upload --upload-port COM3
```

## Adding IP Cores

1. Open `fpga/project.gprj` in Gowin EDA IDE
2. Use the IDE to add IP cores (PLL, RAM, etc.)
3. Save the project file
4. The build script will preserve your IP cores when syncing source files

## Upload Protocols

### pesptool (Default)

Uploads FPGA bitstream via ESP32-S3 SPI bridge to flash address 0x100000.

```ini
upload_command = 
    python scripts/upload_dual.py 
    --fpga-protocol pesptool
```

Requirements:
- Tang Primer bootloader pre-programmed at address 0x0
- pesptool installed

### openFPGALoader

Direct JTAG/USB upload (requires JTAG adapter or USB-JTAG on board).

```ini
upload_command = 
    python scripts/upload_dual.py 
    --fpga-protocol openfpgaloader
    --fpga-board tangnano9k
```

### Gowin Programmer

Uses proprietary Gowin Programmer tool.

```ini
upload_command = 
    python scripts/upload_dual.py 
    --fpga-protocol gowin
    --fpga-device GW5A-25A
```

## Communication Protocol

The example implements a simple SPI slave interface on the FPGA:

### Commands (from ESP32 to FPGA)

| Command | Value | Description |
|---------|-------|-------------|
| `CMD_NOP` | 0x00 | No operation |
| `CMD_READ_ID` | 0x01 | Read FPGA ID (returns 0xA5) |
| `CMD_WRITE_REG` | 0x02 | Write to register |
| `CMD_READ_REG` | 0x03 | Read from register |
| `CMD_LED_CONTROL` | 0x10 | Control LED pattern |

### Serial Commands (via USB)

Connect to serial monitor and send:

- `r` - Reset FPGA
- `i` - Read FPGA ID
- `0-9` - Set LED pattern
- `h` - Show help

## Customization

### Change FPGA Device

Edit `fpga/project.gprj`:

```xml
<Device name="GW5A-25A" pn="GW5A-LV25MG121NES">
```

### Change Top Module Name

Edit `fpga/project.gprj`:

```xml
<TopModule name="top"></TopModule>
```

And update `platformio.ini` if needed.

### Add More Verilog Modules

Simply add `.v` or `.sv` files to `fpga/src/` and they will be automatically included in the build.

## Troubleshooting

### FPGA build fails with "gw_sh not found"

- Ensure Gowin EDA is installed
- Set `GOWIN_HOME` environment variable or `board_build.gowin_path` in platformio.ini
- Check that `gw_sh` exists in `<GOWIN_HOME>/IDE/bin/`

### Upload fails with "pesptool not found"

```bash
pip install git+https://github.com/Papilio-Labs/pesptool.git
```

### Pin constraint errors

- Verify pin assignments in `fpga/constraints/pins.cst` match your hardware
- Check device package (MG121NES) is correct
- Consult Tang Primer 20K pinout diagram

### ESP32 can't communicate with FPGA

- Verify SPI pin assignments match in both `platformio.ini` and `pins.cst`
- Check FPGA bitstream uploaded successfully
- Use logic analyzer to verify SPI signals
- Ensure FPGA is not in reset

## Resources

- [Gowin Semiconductor](https://www.gowinsemi.com/)
- [Gowin TCL API Reference](https://cdn.gowinsemi.com.cn/SUG1220E.pdf)
- [PlatformIO Documentation](https://docs.platformio.org/)
- [pesptool GitHub](https://github.com/Papilio-Labs/pesptool)
- [Papilio Labs](https://papilio.cc/)

## License

This template is provided as-is for educational and development purposes.
