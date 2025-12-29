# Pin Constraint Templates

This directory contains reference CST (Constraint) files for supported boards.

## Usage

Copy the relevant sections from these files to your project's `fpga/constraints/pins.cst` file based on which peripherals you're using in your design.

## Available Templates

### papilio_retrocade.cst

Complete pin mapping for Papilio RetroCade board (GW2AR-18 FPGA).

**Peripherals included:**
- SDRAM interface (32MB SDRAM chip)
- HDMI output (differential pairs for video output)
- ESP32-S3 GPIO connections (15 bidirectional pins + UART)
- PMOD connector (8 GPIO pins for expansion)
- RGB LED (WS2812B addressable LED)
- Audio interface (audio jack outputs)
- USB-C interface (data pins + pullup control)

**Example usage:**

```bash
# Copy entire file as starting point
cp misc/cst/papilio_retrocade.cst fpga/constraints/pins.cst

# Then remove unused sections and rename signals as needed
```

Or copy individual sections:

```verilog
// In your pins.cst, copy just the HDMI section:
//HDMI Data Differential Pairs
IO_LOC "HDMI_D0_P" M6;
IO_LOC "HDMI_D0_N" T8;
// ... etc
```

## Board-Specific Notes

### Papilio RetroCade

- **Device**: GW2AR-LV18QN88C8/I7
- **Package**: QN88C (88-pin QFN)
- **No on-board oscillator**: Clock must be provided by ESP32 or generated internally via PLL
- **Voltage**: All I/O is 3.3V (LVCMOS33)
- **HDMI**: Uses differential signaling (LVCMOS33D)
- **RGB LED**: Single WS2812B requires serial protocol (not simple GPIO)

### Signal Naming Conventions

When adapting these templates:
- Keep the IO_LOC pin assignments (these are physical pins)
- Rename signals in quotes to match your HDL module ports
- Verify IO_TYPE matches your design requirements
- Adjust PULL_MODE and DRIVE strength as needed

### IO_TYPE Options

- **LVCMOS33**: Standard 3.3V CMOS (most common)
- **LVCMOS33D**: Differential signaling at 3.3V (for HDMI, LVDS)
- **LVCMOS25**: 2.5V CMOS
- **LVCMOS18**: 1.8V CMOS

### PULL_MODE Options

- **UP**: Internal pull-up resistor
- **DOWN**: Internal pull-down resistor
- **NONE**: No internal resistor (external pull required)

### DRIVE Strength

Output drive strength in mA: **4**, **8**, **16**, **24**

Higher drive strength for:
- High-speed signals
- Longer traces
- Driving multiple loads
- LED outputs

## Adding New Board Templates

To add a new board:

1. Create `misc/cst/boardname.cst` with complete pin mappings
2. Add board to `boards/boardname.json`
3. Document peripherals and special requirements
4. Add example to `examples/`

## References

- [Gowin Pin Constraint User Guide](https://www.gowinsemi.com/)
- [Papilio RetroCade Hardware](https://github.com/Papilio-Labs/papilio_retrocade_hardware)
