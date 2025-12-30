# Custom ESP32 Board Example

This example demonstrates how to use a custom ESP32 board with the Gowin platform without needing additional code or platform references.

## Overview

The Gowin platform now supports defining custom ESP32+FPGA boards directly within the platform. This means you can:

- Define your custom ESP32 board configuration in a single board JSON file
- Use `platform = gowin` for both ESP32 and FPGA builds
- Build ESP32 firmware and FPGA gateware in a unified workflow
- No need to reference the `espressif32` platform separately

## Board Definition

The example uses the `papilio_retrocade` board, which is defined in `/boards/papilio_retrocade.json`. This board definition includes:

- **ESP32 Configuration**: MCU type, clock speed, flash size, upload protocol, etc.
- **FPGA Configuration**: Device, family, package, project file, etc.
- **Supported Frameworks**: `arduino`, `hdl`, `verilog`

## Project Structure

```
custom-esp32-board/
├── platformio.ini          # Project configuration
├── src/
│   └── main.cpp           # ESP32 Arduino code
├── include/               # ESP32 headers
└── fpga/
    ├── project.gprj       # Gowin project file
    ├── src/
    │   └── top.v          # FPGA Verilog code
    └── constraints/
        └── pins.cst       # Pin constraints
```

## Building

### Build Both ESP32 and FPGA

```bash
pio run -e papilio_retrocade
```

This will:
1. Build the ESP32 firmware
2. Automatically build the FPGA gateware after ESP32 build completes

### Build ESP32 Only

```bash
pio run -e esp32_only
```

### Build FPGA Only

```bash
pio run -e fpga_only
```

## Uploading

### Upload ESP32 Firmware

```bash
pio run -e papilio_retrocade -t upload
```

### Upload FPGA Bitstream

```bash
pio run -e fpga_only -t upload
```

## Creating Your Own Custom Board

To create your own custom ESP32+FPGA board:

1. **Create a board definition file** in `/boards/your_board.json`:

```json
{
  "build": {
    "core": "esp32",
    "mcu": "esp32s3",
    "f_cpu": "240000000L",
    "device": "GW2A-18",
    "fpga_family": "GW2A",
    "fpga_project": "fpga/project.gprj",
    ...
  },
  "frameworks": ["arduino", "hdl"],
  "upload": {
    "protocol": "esptool",
    "protocols": ["esptool", "pesptool", ...]
  }
}
```

2. **Use your board in platformio.ini**:

```ini
[env:my_custom_board]
platform = gowin
board = your_board
framework = arduino
```

3. **That's it!** The platform will automatically configure the ESP32 toolchain and build tools based on your board definition.

## Key Features

- ✅ Single platform for both ESP32 and FPGA
- ✅ Automatic toolchain selection based on MCU type
- ✅ Support for ESP32, ESP32-S2, ESP32-S3, ESP32-C3, ESP32-C6, ESP32-H2
- ✅ Automatic pesptool download on Windows
- ✅ Multiple upload protocols (esptool, pesptool, openfpgaloader, gowin)
- ✅ Unified build workflow

## Notes

- Make sure to install the Gowin EDA toolchain for FPGA builds
- Update `board_build.gowin_path` in platformio.ini to match your Gowin installation
- The platform will automatically download required ESP32 toolchains and tools
