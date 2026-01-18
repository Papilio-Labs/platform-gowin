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

## Automatic Library Integration

The FPGA builder automatically discovers and integrates gateware from PlatformIO libraries. When you add Papilio libraries to your project dependencies, their FPGA modules and constraint files are automatically included in your build.

### How It Works

1. **Add library dependency** to `platformio.ini`:
   ```ini
   [env:myenv]
   lib_deps = 
       papilio_wishbone_bus
       papilio_wb_register
       papilio_wishbone_rgb_led
   ```

2. **Build automatically integrates gateware:**
   - Discovers `.v`/`.sv`/`.vhd` files in `library/gateware/`
   - Adds constraint files from `library/gateware/constraints/<board_name>.cst`
   - Includes modules in FPGA build without manual project file editing

3. **Use modules in your top-level design:**
   ```verilog
   module top (
       input wire clk,
       // ... pins ...
   );
   
   // Wishbone bus from library
   pwb_spi_wb_bridge wb_bridge (
       .clk(clk),
       // ... connections ...
   );
   
   // Register block from library
   wb_register_block regs (
       .wb_clk_i(clk),
       // ... connections ...
   );
   
   endmodule
   ```

### Library Gateware Structure

Papilio libraries follow this structure for automatic integration:

```
papilio_<library_name>/
├── library.json              # PlatformIO metadata with papilio section
├── src/                      # ESP32 firmware API
│   ├── Papilio<Name>.h
│   └── Papilio<Name>.cpp
└── gateware/                 # FPGA modules (auto-discovered)
    ├── module.v
    └── constraints/
        ├── papilio_retrocade.cst
        └── papilio_synth.cst
```

The `library.json` includes a `papilio` section documenting the gateware:

```json
{
  "name": "papilio_wishbone_bus",
  "papilio": {
    "gateware": {
      "modules": [
        {
          "name": "pwb_spi_wb_bridge",
          "file": "gateware/pwb_spi_wb_bridge.v",
          "description": "SPI to Wishbone bridge"
        }
      ]
    }
  }
}
```

### Board-Specific Constraints

Libraries provide constraint files per supported board:

- `gateware/constraints/papilio_retrocade.cst` - Papilio RetroCade pins
- `gateware/constraints/papilio_synth.cst` - Papilio Synth pins

The builder automatically selects the correct file based on your board configuration. Library constraints are included **after** project constraints, allowing you to override library defaults if needed.

### Constraint File Priority

Constraints are processed in this order:

1. Project constraints: `fpga/constraints/*.cst`
2. Library constraints: `<library>/gateware/constraints/<board>.cst` (in dependency order)

Later constraints override earlier ones for the same signal.

### Example: Using Wishbone Libraries

```ini
[env:esp32]
platform = gowin
board = papilio_retrocade
framework = arduino

lib_deps = 
    papilio_wishbone_bus       ; SPI-Wishbone bridge + utilities
    papilio_wb_register        ; Register block with CLI
    papilio_wb_bram           ; Block RAM with burst support
    papilio_wishbone_rgb_led   ; WS2812B LED controller
```

Your FPGA build automatically includes:
- `pwb_spi_wb_bridge.v` - SPI to Wishbone bridge
- `wb_register_block.v` - 8-register block  
- `wb_bram.v` - Configurable block RAM
- `fifo_sync.v` - FIFO for burst transfers
- `ws2812b_driver.v` - RGB LED controller
- Pin constraints for all modules

**Build output shows discovery:**
```
Building FPGA Gateware...
Found 5 Verilog, 0 VHDL, 3 constraint files
Library gateware discovered:
  - libs/papilio_wishbone_bus/gateware/*.v (3 files)
  - libs/papilio_wb_bram/gateware/*.v (2 files)
  - libs/papilio_wishbone_rgb_led/gateware/*.v (2 files)
```

### Creating Library Gateware

To make your library auto-discoverable:

1. **Create gateware directory:**
   ```
   my_library/
   ├── library.json
   ├── src/              # ESP32 code
   └── gateware/         # FPGA modules
       ├── my_module.v
       └── constraints/
           └── papilio_retrocade.cst
   ```

2. **Document in library.json:**
   ```json
   {
     "name": "my_library",
     "papilio": {
       "gateware": {
         "modules": [
           {
             "name": "my_module",
             "file": "gateware/my_module.v",
             "description": "Module description"
           }
         ]
       }
     }
   }
   ```

3. **Users automatically get gateware** when they add `my_library` to `lib_deps`

See `libs/papilio_lib_template/` for a complete library template following these standards.

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
# Start with the minimal SPI-only template (recommended default)
cp misc/cst/papilio_arcade_base.cst fpga/constraints/pins.cst

# Copy the full template when you need every peripheral
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
