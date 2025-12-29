# Platform Testing

This directory contains test projects for validating the platform functionality.

## Test Projects

### test-hdl-pure

Tests pure FPGA builds with the `hdl` framework.

**What it tests:**
- Platform installation from local directory
- HDL framework activation
- Verilog file detection
- VHDL file detection (mixed-language)
- .gprj project file generation
- Pin constraint handling
- Gowin toolchain integration
- FPGA build process

### test-dual-target

Tests dual-target builds with ESP32 + FPGA.

**What it tests:**
- Arduino framework with FPGA post-action
- ESP32 firmware compilation
- FPGA synthesis after ESP32 build
- Upload protocol configuration
- SPI communication setup

## Running Tests

### Prerequisites

1. Install PlatformIO Core:
   ```bash
   pip install platformio
   ```

2. Install Gowin EDA toolchain and set GOWIN_HOME environment variable

3. For upload tests, connect hardware

### Local Platform Testing

Test with the local platform before pushing to GitHub:

```bash
# Test pure FPGA build
cd test/test-hdl-pure
pio run

# Test dual-target build
cd test/test-dual-target
pio run
```

### GitHub Platform Testing

Test after pushing to verify remote installation works:

```bash
# Modify platformio.ini to use GitHub URL:
# platform = https://github.com/Papilio-Labs/platform-gowin.git

pio run
```

## Expected Results

### Successful Build

✅ Platform installs from local/remote source
✅ Board configuration loads correctly
✅ HDL files are detected
✅ .gprj file is updated
✅ Gowin synthesis completes
✅ Bitstream (.bin) is generated
✅ Upload protocols are configured

### Build Output

Look for these indicators:
```
Building FPGA Gateware...
Scanning for FPGA source files...
  Found X Verilog/SystemVerilog file(s)
  Found X VHDL file(s)
  Found X constraint file(s)
Updating project file: fpga/project.gprj
Starting FPGA synthesis and place & route...
✓ FPGA bitstream generated: impl/pnr/project.bin
```

## Troubleshooting

### Platform Not Found

If you get "Unknown development platform 'gowin'":
- Check platform path in platformio.ini
- Verify platform.json exists in platform root
- Try: `pio pkg install --global --platform file://path/to/platform-gowin`

### Gowin Toolchain Not Found

If synthesis fails with "Gowin toolchain not found":
- Set GOWIN_HOME environment variable
- Or add to platformio.ini: `board_build.gowin_path = C:/Gowin_V1.9.9`

### Pin Constraint Warnings

If you see "Pin not assigned" warnings:
- Copy appropriate CST template from misc/cst/
- Verify pin names match your HDL module ports
- Check device and package match your board

## CI/CD Integration

These tests can be integrated into GitHub Actions:

```yaml
- name: Test HDL Framework
  run: |
    cd test/test-hdl-pure
    pio run --verbose
```

Note: Requires Gowin toolchain installation in CI environment.

## Adding New Tests

To add a new test project:

1. Create directory: `test/test-yourfeature/`
2. Add platformio.ini with platform reference
3. Add test HDL/Arduino code
4. Document what the test validates
5. Update this README

## Test Coverage

Current test coverage:

- [x] Platform installation (local)
- [x] Platform installation (GitHub)
- [x] HDL framework (pure FPGA)
- [x] Arduino framework (dual-target)
- [x] Verilog support
- [x] VHDL support
- [x] Mixed Verilog/VHDL
- [x] Pin constraints
- [ ] Upload with pesptool
- [ ] Upload with openFPGALoader
- [ ] Multiple board definitions
- [ ] Custom board creation
