# Papilio Automatic Library Builder Example

This example demonstrates the Papilio Automatic Library Builder feature, which automatically integrates Papilio peripheral libraries into your FPGA + ESP32 project.

## Features Demonstrated

- **Automatic Library Discovery**: Libraries in `lib_deps` are automatically scanned for `papilio` metadata
- **Marker-Based Code Injection**: Generated code is injected between `//# PAPILIO_AUTO_*` markers
- **Wishbone Address Allocation**: Non-overlapping addresses are auto-assigned to peripherals
- **FPGA Integration**: Module instantiations and interconnect logic are auto-generated
- **ESP32 Integration**: Include directives, object declarations, and init code are auto-generated

## How It Works

1. **Add libraries to `platformio.ini`**:
   ```ini
   lib_deps = 
       papilio_spi_slave
       papilio_wb_register
   ```

2. **Add markers to your source files**:
   - In `fpga/src/top.v`: Add `//# PAPILIO_AUTO_*_BEGIN/END` markers
   - In `src/main.cpp`: Add matching markers for ESP32 code

3. **Build the project**:
   ```bash
   pio run
   ```

4. **The builder automatically**:
   - Discovers libraries with `papilio` metadata in `library.json`
   - Allocates Wishbone addresses without conflicts
   - Generates and injects code into marker regions
   - Preserves your code outside the markers

## Marker Types

### Verilog (fpga/src/top.v)

| Marker | Purpose |
|--------|---------|
| `PAPILIO_AUTO_PORTS` | Top-level port declarations |
| `PAPILIO_AUTO_WIRES` | Internal wire declarations |
| `PAPILIO_AUTO_MODULE_INST` | Module instantiations |
| `PAPILIO_AUTO_WISHBONE` | Wishbone interconnect logic |

### C++ (src/main.cpp)

| Marker | Purpose |
|--------|---------|
| `PAPILIO_AUTO_INCLUDES` | #include directives |
| `PAPILIO_AUTO_GLOBALS` | Global object declarations |
| `PAPILIO_AUTO_INIT` | Initialization in setup() |
| `PAPILIO_AUTO_CLI` | CLI command dispatcher |

## Disabling Auto-Generation

To take manual control of a section, simply remove its markers. The builder will detect missing markers and skip code generation for that section.

## Configuration Options

In `platformio.ini`:

```ini
; Enable/disable auto-builder (default: enabled)
board_build.papilio_auto_builder = 1

; Enable verbose output
board_build.papilio_verbose = 1

; Enable CLI generation
build_flags = -DPAPILIO_CLI_ENABLED=1
```

## Generated Files

After building, check the `.papilio/` directory for:
- `address_map.txt` - Human-readable Wishbone address allocation

## Project Structure

```
papilio-auto-builder/
├── platformio.ini              # Project configuration
├── fpga/
│   ├── project.gprj            # Gowin project file
│   ├── src/
│   │   └── top.v               # FPGA top module with markers
│   └── constraints/
│       └── pins.cst            # Pin constraints
└── src/
    └── main.cpp                # ESP32 code with markers
```

## Requirements

- PlatformIO with `gowin` platform
- Gowin EDA toolchain
- Libraries with `papilio` metadata section in `library.json`
