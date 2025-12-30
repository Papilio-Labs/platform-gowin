# Gowin FPGA Platform for PlatformIO

PlatformIO platform for Gowin FPGA development. Supports pure FPGA projects (Verilog/SystemVerilog/VHDL) and dual-target projects (MCU + FPGA) using the Gowin Educational IDE toolchain.

## Supported Devices

- **GW1N Series** (Nano)
- **GW2A Series** (Arora)
- **GW5A Series** (Arora V) - including GW5A-25A
- **GW5AST Series** (Arora V with transceivers)

## Supported Boards

### Dual-Target Boards (ESP32 + FPGA)
- **Papilio RetroCade** (ESP32-S3 + GW2A-18) - `papilio_retrocade_esp32`
  - Supports Arduino framework + FPGA
  - Full SPI communication between ESP32 and FPGA
  - Automatic dual-target builds

### FPGA-Only Boards
- **Papilio RetroCade FPGA** (GW2A-18) - `papilio_retrocade_fpga`
- Tang Nano 9K
- Tang Nano 20K
- Sipeed boards (coming soon)
- Generic Gowin development boards

## Features

✅ Automatic HDL source file discovery (Verilog, SystemVerilog, VHDL)
✅ Mixed-language projects (Verilog + VHDL)
✅ Preserves user-added IP cores in Gowin projects
✅ Multiple upload protocols (pesptool, openFPGALoader, Gowin Programmer)
✅ Pure FPGA projects with `framework = hdl` (or `framework = verilog`)
✅ Dual-target projects (MCU + FPGA) with `framework = arduino`
✅ Integrated with PlatformIO ecosystem

## Installation

### Install Platform

```bash
# Install from GitHub
pio pkg install --global --platform https://github.com/Papilio-Labs/platform-gowin.git

# Or use platform_packages in platformio.ini
[env:myenv]
platform = https://github.com/Papilio-Labs/platform-gowin.git
board = papilio_retrocade
```

### Install Gowin EDA Toolchain

1. Download **Gowin EDA Educational** from [Gowin Semiconductor](https://www.gowinsemi.com/)
2. Install to standard location (e.g., `C:\Gowin_V1.9.9`)
3. Set environment variable (optional):
   ```bash
   # Windows
   setx GOWIN_HOME "C:\Gowin_V1.9.9"
   
   # Linux/Mac
   export GOWIN_HOME="/opt/gowin"
   ```

### Install Upload Tools

#### pesptool (for ESP32 + FPGA boards)

**Windows:** Automatically downloaded by PlatformIO when you set `upload_protocol = pesptool`

**Linux/Mac:** Manual installation required:
```bash
pip install git+https://github.com/Papilio-Labs/pesptool.git
```

#### openFPGALoader (universal FPGA programmer)

See [openFPGALoader installation](https://github.com/trabucayre/openFPGALoader#installation)

#### Gowin Programmer

Included with Gowin EDA installation.

## Quick Start

### FPGA-Only Project

```ini
[platformio]
default_envs = my_fpga

[env:my_fpga]
platform = gowin
board = papilio_retrocade
framework = hdl  ; Use 'hdl' for Verilog/VHDL (or 'verilog' for backwards compatibility)

; Upload via pesptool (ESP32 SPI bridge)
upload_protocol = pesptool
```

Project structure:
```
my_project/
├── platformio.ini
└── fpga/
    ├── project.gprj       # Gowin project file
    ├── src/
    │   ├── top.v          # Your Verilog code
    │   └── module.vhd     # Your VHDL code (optional)
    └── constraints/
        └── pins.cst       # Pin constraints
```

### Dual-Target Project (ESP32 + FPGA)

```ini
[platformio]
default_envs = my_dual_target

[env:my_dual_target]
platform = gowin
board = papilio_retrocade_esp32  ; ESP32-S3 + FPGA board
framework = arduino

; FPGA configuration
board_build.fpga_project = fpga/project.gprj
board_build.fpga_top_module = top

; ESP32 upload (FPGA builds automatically after ESP32 build)
upload_protocol = esptool
monitor_speed = 115200
```

Project structure:
```
my_project/
├── platformio.ini
├── src/
│   └── main.cpp          # ESP32 code
└── fpga/
    ├── project.gprj
    ├── src/
    │   └── top.v         # FPGA code
    └── constraints/
        └── pins.cst
```

## Examples

### Dual-Target Examples (ESP32 + FPGA)

#### [ESP32-FPGA Blinky](examples/esp32-fpga-blinky/)

Complete dual-target example with ESP32-S3 + Gowin FPGA.
- ESP32 controls FPGA reset and monitors configuration
- SPI communication between ESP32 and FPGA
- Independent LED patterns on both targets
- Demonstrates full Arduino + HDL integration

```bash
cd examples/esp32-fpga-blinky
pio run                    # Build both ESP32 and FPGA
pio run -t upload         # Upload ESP32 firmware
```

#### [Dual-Target Blinky](examples/dual-target-blinky/)

Advanced dual-target project with ESP32-S3 and FPGA communication via SPI.

```bash
cd examples/dual-target-blinky
pio run
pio run -t upload
```

### Pure FPGA Examples

#### [FPGA Mixed HDL](examples/fpga-mixed-hdl/)

Pure FPGA project demonstrating mixed Verilog/VHDL design.

```bash
cd examples/fpga-mixed-hdl
pio run
pio run -t upload
```

#### [WS2812B RGB LED](examples/ws2812b-rgb-led/)

FPGA-based WS2812B LED controller.

```bash
cd examples/ws2812b-rgb-led
pio run
pio run -t upload
```

## Configuration

### platformio.ini Options

```ini
[env:myenv]
platform = gowin
board = papilio_retrocade

; FPGA project file path
board_build.fpga_project = fpga/project.gprj

; Gowin toolchain path (auto-detected if not set)
board_build.gowin_path = C:/Gowin_V1.9.9

; FPGA top module name
board_build.fpga_top_module = top

; Upload protocol
upload_protocol = pesptool  ; or openfpgaloader, gowin, esptool
```

## Adding IP Cores

1. Open `fpga/project.gprj` in Gowin IDE
2. Use the IP Core Generator to add cores (PLL, RAM, FIFO, etc.)
3. Save the project file
4. Build with `pio run` - IP cores are automatically preserved

The build system manages HDL source files (`.v`, `.sv`, `.vhd`, `.vhdl`) and constraints (`.cst`). 
All IP cores and custom project settings are preserved.

### Mixed-Language Projects

The Gowin toolchain fully supports mixed Verilog and VHDL designs. Simply place your source files in the `fpga/src/` directory:

```
fpga/
├── src/
│   ├── top.v              # Verilog top module
│   ├── vhdl_module.vhd    # VHDL component
│   └── verilog_helper.sv  # SystemVerilog helper
└── constraints/
    └── pins.cst
```

The build system automatically detects and adds all HDL files to your `.gprj` project. You can instantiate VHDL components in Verilog modules and vice versa.

## Upload Protocols

### pesptool (Default for Papilio boards)

Uploads FPGA bitstream via ESP32-S3 SPI bridge to flash address 0x100000.

```ini
upload_protocol = pesptool
upload_port = COM3  ; or /dev/ttyUSB0
```

**Requirements:**
- Tang Primer bootloader pre-programmed at address 0x0
- pesptool installed

### openFPGALoader

Direct JTAG/USB upload (requires JTAG adapter or USB-JTAG on board).

```ini
upload_protocol = openfpgaloader
board_build.fpga_board_type = tangnano9k
```

### Gowin Programmer

Uses proprietary Gowin Programmer tool.

```ini
upload_protocol = gowin
```

## Board Definitions

### Using Existing Boards

The platform includes board definitions with correct FPGA device settings and pin mappings.

### Pin Constraint Templates

Reference CST files for supported boards are available in `misc/cst/`:

```bash
# Copy complete pin template for your board
cp misc/cst/papilio_retrocade.cst fpga/constraints/pins.cst

# Or copy individual peripheral sections as needed
```

See [misc/cst/README.md](misc/cst/README.md) for complete documentation on:
- Available peripherals per board
- Signal naming conventions
- IO standards and electrical specifications
- PULL_MODE and DRIVE strength guidance

### Creating Custom Board Definitions

Create custom board definitions in `boards/myboard.json`:

```json
{
  "build": {
    "device": "GW1NR-9",
    "fpga_family": "GW1N",
    "fpga_package": "QN88P",
    "fpga_project": "fpga/project.gprj"
  },
  "frameworks": ["hdl"],
  "name": "My Custom Board",
  "upload": {
    "protocol": "openfpgaloader"
  },
  "url": "https://example.com/myboard",
  "vendor": "MyCompany"
}
```

## Development

### Project Structure

```
platform-gowin/
├── platform.json          # Platform metadata
├── platform.py            # Platform class
├── boards/                # Board definitions
│   └── *.json
├── builder/
│   ├── main.py           # Main build script
│   ├── fpga_builder.py   # FPGA build functions
│   └── frameworks/
│       ├── verilog.py    # Verilog framework
│       └── arduino.py    # Arduino framework
└── examples/
    ├── fpga-blinky/
    └── papilio-blinky/
```

### Testing

```bash
# Run example builds
cd examples/fpga-blinky
pio run

cd examples/papilio-blinky
pio run
```

## Troubleshooting

### "gw_sh not found"

- Ensure Gowin EDA is installed
- Set `GOWIN_HOME` environment variable
- Or set `board_build.gowin_path` in platformio.ini

### "pesptool not found"

```bash
pip install git+https://github.com/Papilio-Labs/pesptool.git
```

### Pin constraint errors

- Verify pin assignments in `fpga/constraints/pins.cst`
- Check device package matches your hardware
- Consult FPGA datasheet for correct pin names

### FPGA build fails

- Check Gowin IDE can open and build `fpga/project.gprj` manually
- Verify top module name matches `board_build.fpga_top_module`
- Check build logs in `fpga/impl/pnr/` directory

## Resources

- [Gowin Semiconductor](https://www.gowinsemi.com/)
- [Gowin TCL API Reference](https://cdn.gowinsemi.com.cn/SUG1220E.pdf)
- [PlatformIO Documentation](https://docs.platformio.org/)
- [pesptool GitHub](https://github.com/Papilio-Labs/pesptool)
- [openFPGALoader](https://github.com/trabucayre/openFPGALoader)
- [Papilio Labs](https://papilio.cc/)

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add board definitions or examples
4. Test your changes
5. Submit a pull request

## License

Apache-2.0 License - see LICENSE file for details.
