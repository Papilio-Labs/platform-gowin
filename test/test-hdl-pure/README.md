# Pure HDL Test Project

Tests the platform's pure FPGA build capabilities.

## What This Tests

✅ Platform installation from local directory  
✅ HDL framework activation  
✅ Verilog file compilation (.v)  
✅ VHDL file compilation (.vhd)  
✅ Mixed Verilog/VHDL design (Verilog top instantiating VHDL component)  
✅ Pin constraint file handling (.cst)  
✅ Gowin project file (.gprj) auto-update  
✅ FPGA synthesis and bitstream generation  

## Design Description

Simple design with:
- **test_top.v** (Verilog): Top-level module
- **vhdl_counter.vhd** (VHDL): 32-bit counter component
- Mixed-language instantiation (Verilog instantiates VHDL)
- Outputs counter MSBs to PMOD connector

## Running the Test

```bash
# Build only (no hardware required)
pio run

# Build and upload (requires connected hardware)
pio run -t upload
```

## Expected Output

```
Building FPGA Gateware...
Scanning for FPGA source files...
  Found 1 Verilog/SystemVerilog file(s)
  Found 1 VHDL file(s)
  Found 1 constraint file(s)
Updating project file: fpga/test_project.gprj
Starting FPGA synthesis and place & route...
✓ FPGA bitstream generated: impl/pnr/test_project.bin
```

## Success Criteria

- ✅ Platform installs correctly
- ✅ Both Verilog and VHDL files are detected
- ✅ .gprj file is updated with both file types
- ✅ Synthesis completes without errors
- ✅ Bitstream (.bin) is generated in build directory

## Troubleshooting

### "Gowin toolchain not found"

Set GOWIN_HOME or add to platformio.ini:
```ini
board_build.gowin_path = C:/Gowin_V1.9.9
```

### "Unknown platform 'gowin'"

Verify platform installation:
```bash
pio pkg list -g
```

Should show `platform-gowin @ file://...`

### Synthesis Errors

Check that:
- Top module name matches .gprj setting (test_top)
- Device specification matches board (GW2AR-18)
- Pin names match between HDL and .cst file
