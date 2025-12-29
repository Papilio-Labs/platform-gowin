# RGB LED Blink Example

Control the onboard WS2812B RGB LED on the Papilio RetroCade board.

## Hardware

- **Board**: Papilio RetroCade
- **FPGA**: Gowin GW2A-LV18PG256C8/I7
- **LED**: WS2812B addressable RGB LED on pin P9
- **Clock**: 27MHz from ESP32 GPIO

## Description

This example demonstrates:
- WS2812B RGB LED protocol implementation
- Precise timing control (T0H, T0L, T1H, T1L)
- State machine design for serial LED communication
- GRB color format handling

The LED displays a dim green color. You can modify the `GREEN_COLOR` parameter in `ws2812b.v` to change colors:
- Format: `24'hGGRRBB` (Green, Red, Blue)
- Example colors:
  - Green: `24'h050000`
  - Red: `24'h000500`
  - Blue: `24'h000005`
  - Purple: `24'h000505`
  - Cyan: `24'h050005`
  - Yellow: `24'h050500`

**Note**: Keep brightness values low (≤0x10) to avoid excessive current draw.

## Building

```bash
pio run
```

## Uploading

```bash
# Configure COM port in platformio.ini first
pio run -t upload
```

Or manually with pesptool:
```bash
pesptool --port COM4 write_flash 0x100000 .pio/build/papilio_retrocade/fpga_bitstream.bin
```

## Files

- `fpga/src/blink_led.v` - Top module connecting clock/reset to WS2812B controller
- `fpga/src/ws2812b.v` - WS2812B LED driver with timing state machine
- `fpga/constraints/pins.cst` - Pin assignments for Papilio RetroCade
- `fpga/rgb_led.gprj` - Gowin project configuration

## Timing Details

WS2812B requires precise timing (±150ns tolerance):
- **T0H**: 0.35us (9 cycles @ 27MHz) - '0' bit high time
- **T0L**: 0.8us (22 cycles @ 27MHz) - '0' bit low time  
- **T1H**: 0.7us (19 cycles @ 27MHz) - '1' bit high time
- **T1L**: 0.6us (16 cycles @ 27MHz) - '1' bit low time
- **RES**: >50us (1350 cycles @ 27MHz) - Reset/latch time

## Modifying Colors

Edit `ws2812b.v` and change the color parameter:

```verilog
parameter [23:0] GREEN_COLOR = 24'h050000; // Change this value
```

Then rebuild and upload to see the new color.
