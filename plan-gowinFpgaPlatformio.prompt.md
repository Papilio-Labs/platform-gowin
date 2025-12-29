## Plan: Add Gowin FPGA Toolchain Support to PlatformIO

Supporting the Gowin Educational IDE toolchain in PlatformIO with dual-target builds (ESP32S3 + FPGA) using a single environment with post-build scripts. Users can open and edit the Gowin `.gprj` project file to add IP cores, while the build script automatically syncs Verilog sources and constraint files before building. Multiple upload protocols (pesptool, openFPGALoader, Gowin Programmer) are supported via platformio.ini configuration.

### Steps

1. **Create directory structure** with [src/](src/) for ESP32 code, [fpga/src/](fpga/src/) for Verilog, [fpga/constraints/](fpga/constraints/) for `.cst` files, [fpga/project.gprj](fpga/project.gprj) template with GW5A-25A device config, and [scripts/](scripts/) for build automation.

2. **Implement post-build FPGA script** in [scripts/build_fpga.py](scripts/build_fpga.py) using `xml.etree.ElementTree` to parse `.gprj`, recursively scan [fpga/src/](fpga/src/) and [fpga/constraints/](fpga/constraints/) for `.v`/`.sv`/`.cst` files, update XML `<FileList>` section while preserving IP cores and user settings, invoke `gw_sh project.gprj` to build, and copy generated `.bin` to build directory.

3. **Configure platformio.ini** for `esp32-s3-devkitc-1` with `extra_scripts = post:scripts/build_fpga.py`, `board_build.fpga_project = fpga/project.gprj`, `board_build.gowin_path` for toolchain location override, and optional `[env:esp32_only]`/`[env:fpga_only]` environments for independent testing.

4. **Implement upload protocol dispatcher** in [scripts/upload_dual.py](scripts/upload_dual.py) that uploads ESP32 firmware via esptool, then checks upload protocol config and dispatches to pesptool (`--port $PORT --address 0x100000 bitstream.bin`), openFPGALoader (`-b tangnano9k -f bitstream.bin`), or Gowin Programmer (`gwprog -d GW5A-25A -f bitstream.bin`).

5. **Create example project** with ESP32 [src/main.cpp](src/main.cpp) with SPI/GPIO FPGA interface code, FPGA [fpga/src/top.v](fpga/src/top.v) LED blinky, [fpga/constraints/pins.cst](fpga/constraints/pins.cst) for Papilio RetroCade pinout, and [fpga/project.gprj](fpga/project.gprj) template that users can open directly in Gowin IDE to add IP cores.

### Further Considerations

1. **Upload protocol configuration**: Should use standard `upload_protocol` with custom values, or separate `board_build.fpga_upload_protocol` to independently control ESP32 vs FPGA upload methods? This can be decided during implementation based on PlatformIO's configuration parsing behavior.
