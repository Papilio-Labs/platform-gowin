# Gowin FPGA Platform for PlatformIO

PlatformIO platform for Gowin FPGA development. Supports pure FPGA projects (Verilog/SystemVerilog/VHDL) and dual-target projects (MCU + FPGA) using the Gowin Educational IDE toolchain.

## Supported Devices

- **GW1N Series** (Nano)
- **GW2A Series** (Arora)
- **GW5A Series** (Arora V) - including GW5A-25A
- **GW5AST Series** (Arora V with transceivers)

## Supported Boards

- **Papilio RetroCade** (ESP32-S3 + GW5A-25A) - Dual-target
- Tang Nano 9K
- Tang Nano 20K
- Sipeed boards (coming soon)
- Generic Gowin development boards

## Features

✅ Automatic HDL source file discovery (Verilog, SystemVerilog, VHDL)
✅ Mixed-language projects (Verilog + VHDL)
✅ Preserves user-added IP cores in Gowin projects
✅ Direct resident-loader USB serial and HTTP uploads, plus legacy programmers
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

#### Resident Papilio ESP bootloader (recommended for RetroCade)

No desktop Loader, MCP server, Node.js, global pip installation, or pesptool
executable is required. PlatformIO installs its managed `tool-esptoolpy`;
the platform ships a Python uploader that uses PlatformIO's pyserial and
Python's HTTP library. The board must already have the resident Papilio
factory loader and the supported 4 MB factory/OTA partition layout.

```ini
[env:fpga]
platform = https://github.com/Papilio-Labs/platform-gowin.git
board = papilio_retrocade_fpga
framework = hdl
upload_protocol = papilio_serial
; Optional if board detection is unambiguous:
; upload_port = COM10
```

For HTTP uploads, select `papilio_ota` and set `custom_papilio_host` to the
board's IP/hostname. `custom_papilio_http_port` defaults to 3232. A running
factory loader requires no USB connection for this transport.

```ini
upload_protocol = papilio_ota
custom_papilio_host = 192.168.1.100
; For an app without a network /goto-loader handler, enter factory over USB:
; custom_papilio_enter_via_usb = yes
; custom_papilio_usb_port = COM10
```

USB recovery first verifies the partition checksum/layout and factory
application identity. It saves otadata under
`.pio/build/<environment>/papilio-backups/`, then clears only OTA
selection/rollback metadata and watchdog-resets into factory. Application
images, partition table, factory firmware, and loader NVS stay intact.
The loader's separate NVS last-slot record chooses update/resume slots.
Release serial monitors before uploading. If native-USB reset fails,
follow the explicit RESET/BOOT instructions; the uploader never falls back
to mass erase or full firmware replacement.

FPGA uploads write external FPGA flash at **0x0**, automatically loading
the embedded bridge on-board. They resume the existing ESP application
unless `custom_papilio_stay_in_loader = yes` is set. No host SPI pin
configuration is needed. USB transfer errors and missing completion
responses fail the upload; HTTP uploads check status and response bodies.
An HTTP application success response confirms image validation/selection,
not independent observation of the app's subsequent boot.

The same repository also has a `tool-papilio-upload` tool manifest, so an
ESP PlatformIO environment can install the same scripts through
`platform_packages`. See the
[project template](https://github.com/Papilio-Labs/papilio_project_template)
for its application-only custom-upload hook and partition configuration.
Existing pesptool/openFPGALoader/Gowin protocols are unchanged.

Live Windows tests cover both transports with FPGA and ESP images;
Linux/macOS hardware validation and repeated reset/power-cycle testing
remain necessary. On Linux, grant the normal serial-device permissions.

#### pesptool (for ESP32 + FPGA boards)

This is the legacy bridge/multiboot path, not the recommended resident-loader
uploader. It does not prepare the current on-board FPGA bridge by itself.

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

### Dual-Target Project (MCU + FPGA)

```ini
[platformio]
default_envs = my_dual_target

[env:my_dual_target]
platform = gowin
board = papilio_retrocade
framework = arduino

; FPGA builds automatically after ESP32 build
upload_protocol = esptool
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

### [FPGA Blinky](examples/fpga-blinky/)

Pure FPGA project with rotating LED pattern.

```bash
cd examples/fpga-blinky
pio run
pio run -t upload
```

### [Papilio Blinky](examples/papilio-blinky/)

Dual-target project with ESP32-S3 and FPGA communication via SPI.

```bash
cd examples/papilio-blinky
pio run
pio run -t upload
```

## Configuration

### Uploader tests

```bash
python -m unittest discover -s tests -p "test_*.py"
```

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

### Library Gateware

The FPGA environment discovers HDL under the `gateware/` directory of its
resolved `lib_deps` libraries and their dependencies. Declare the libraries
in the FPGA environment as well as the firmware environment, for example:

```ini
[env:fpga]
platform = gowin
board = papilio_retrocade_fpga
framework = hdl
lib_deps = ${env:esp32.lib_deps}
```

PlatformIO installs these libraries when the FPGA environment is built.
Verilog headers are tracked as dependencies and their directories are added
to the Gowin include path; they are not compiled as standalone sources.
The build does not generate or modify FPGA or firmware source code. Wire
peripherals and add board pin constraints in the project yourself. Library
constraint files are not included automatically.

If installed libraries contain conflicting HDL modules, exclude the
unwanted files explicitly using paths relative to the library storage
directory. Shell-style wildcards are supported:

```ini
board_build.fpga_exclude_sources =
    papilio_spi_slave/gateware/spi_wb_bridge.v
```

The exclusion above is needed when using the current SPI and Wishbone bus
libraries together: each contains a different `simple_spi_wb_bridge` module.
Choose exclusions appropriate to the design; the platform does not silently
choose between conflicting implementations.

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
