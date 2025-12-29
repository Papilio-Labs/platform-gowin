# PlatformIO Gowin Platform Examples

Example projects demonstrating various features of the Gowin FPGA platform for PlatformIO.

## Pure FPGA Examples

### fpga-blinky
Basic FPGA example with mixed Verilog/VHDL demonstrating:
- Counter logic in VHDL
- Top-level wrapper in Verilog
- PMOD GPIO outputs

### rgb-led-blink
WS2812B RGB LED control example:
- Precise timing control for addressable RGB LED
- State machine implementation
- Single LED color display on onboard WS2812B

## Dual-Target Examples (ESP32 + FPGA)

### papilio-blinky
Complete dual-target example showing:
- ESP32 Arduino firmware
- FPGA SPI slave peripheral
- ESP32 ↔ FPGA communication
- Synchronized LED patterns

## Building Examples

Each example can be built with:
```bash
cd example-name
pio run
```

## Uploading Examples

Configure your upload settings in `platformio.ini`:
```ini
upload_protocol = pesptool  ; or openfpgaloader, esptool
upload_port = COM4          ; your serial port
```

Then upload:
```bash
pio run -t upload
```

## Hardware Requirements

- **Papilio RetroCade board** (ESP32-S3 + Gowin GW2A-18 FPGA)
- **USB-C cable** for programming
- **Gowin EDA toolchain** installed (v1.9.9 or later)

## Documentation

For detailed information about each example, see the README.md file in each example directory.
