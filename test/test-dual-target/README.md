# Dual-Target Test Project

Tests the platform's Arduino framework with ESP32 + FPGA dual-target builds.

## What This Tests

✅ Arduino framework integration  
✅ ESP32-S3 compilation and upload  
✅ FPGA build triggered after ESP32 build  
✅ Dual-target build workflow (MCU + FPGA)  
✅ SPI communication between ESP32 and FPGA  
✅ Post-action FPGA bitstream generation  
✅ Platform handles both src/ and fpga/ directories  

## Design Description

**ESP32 (src/main.cpp):**
- Initializes SPI as master
- Sends incrementing test pattern to FPGA
- Reads back echo response
- Reports via Serial (115200 baud)

**FPGA (fpga/src/fpga_spi_slave.v):**
- SPI slave peripheral
- Echoes received data back to ESP32
- Displays lower 4 bits on PMOD connector

## Running the Test

```bash
# Build both ESP32 and FPGA
pio run

# Upload ESP32 firmware (FPGA bitstream auto-uploaded to flash)
pio run -t upload

# Monitor serial output
pio device monitor
```

## Expected Output

### Build Output:
```
Building in release mode
Compiling .pio/build/papilio_retrocade/src/main.cpp.o
Linking .pio/build/papilio_retrocade/firmware.elf
Building .pio/build/papilio_retrocade/firmware.bin
RAM:   [==        ]  18.5%
Flash: [===       ]  27.3%

Building FPGA Gateware...
Scanning for FPGA source files...
  Found 1 Verilog/SystemVerilog file(s)
  Found 1 constraint file(s)
Updating project file: fpga/test_dual.gprj
✓ FPGA bitstream generated: impl/pnr/test_dual.bin
```

### Serial Monitor Output:
```
=== Papilio RetroCade - ESP32 + FPGA Test ===
FPGA SPI Interface initialized
  CS:   GPIO10
  CLK:  GPIO12
  MOSI: GPIO11
  MISO: GPIO13
Sent: 0x00 -> Received: 0x00
Sent: 0x01 -> Received: 0x01
Sent: 0x02 -> Received: 0x02
...
```

## Success Criteria

- ✅ ESP32 firmware compiles successfully
- ✅ FPGA bitstream builds automatically after ESP32
- ✅ Upload includes both ESP32 firmware and FPGA bitstream
- ✅ Serial output shows incrementing pattern
- ✅ Received data matches sent data (echo test passes)
- ✅ PMOD LEDs display changing pattern (if connected)

## Hardware Setup (Optional)

1. **Basic Test:** Just upload and check serial output
2. **Visual Test:** Connect LEDs to PMOD (pins N9, R9, N8, L9)
3. **Logic Analyzer:** Monitor SPI signals to verify communication

## Troubleshooting

### "FPGA build not triggered"

Verify platformio.ini has:
```ini
board_build.fpga_project = fpga/test_dual.gprj
```

### "SPI no response"

Check that:
- FPGA bitstream was programmed (check upload log)
- SPI pins match constraints file
- ESP32 GPIO numbers correct for your board revision

### "Upload fails"

Try:
```bash
# ESP32 only
pio run -t upload

# Then manually upload FPGA
pio run -t uploadfpga
```
