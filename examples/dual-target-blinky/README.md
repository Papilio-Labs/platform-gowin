# Papilio RetroCade GPIO Pass-through Example

Simple dual-target example demonstrating ESP32-S3 and Gowin FPGA GPIO communication.

## Hardware

- ESP32-S3 SuperMini (MCU)
- Gowin GW2A-18 FPGA
- Papilio RetroCade Board

## Features

- ESP32 toggles GPIO1 pin
- FPGA passes the signal through to all 8 PMOD pins
- Pure combinational logic (no clock required)
- Serial console output

## Building

```bash
# Build both ESP32 and FPGA
pio run

# Build ESP32 only
pio run -e esp32_only

# Build FPGA only
pio run -e fpga_only
```

## Uploading

```bash
# Upload both ESP32 firmware and FPGA bitstream
pio run -t upload
```

## Usage

1. Connect to serial monitor: `pio device monitor`
2. Observe GPIO1 toggling every second (HIGH/LOW messages)
3. All 8 PMOD pins will follow GPIO1 state

## Pin Assignments

### ESP32 to FPGA

- ESP32 GPIO1 → FPGA gpio1_in (pin A9)

### FPGA PMOD Outputs

- pmod_out[0]: pin N9 (PMOD_IOA0)
- pmod_out[1]: pin R9 (PMOD_IOA1)
- pmod_out[2]: pin N8 (PMOD_IOA2)
- pmod_out[3]: pin L9 (PMOD_IOA3)
- pmod_out[4]: pin L8 (PMOD_IOB0)
- pmod_out[5]: pin M6 (PMOD_IOB1)
- pmod_out[6]: pin P7 (PMOD_IOB2)
- pmod_out[7]: pin R7 (PMOD_IOB3)

## Customization

### Modify FPGA Design

Edit Verilog files in `fpga/src/` - they will be automatically discovered and added to the build.

### Add Constraints

Add `.cst` files to `fpga/constraints/` - they will be automatically included.
