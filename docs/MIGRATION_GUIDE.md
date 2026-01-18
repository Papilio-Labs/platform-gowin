# Migration Guide - Automatic Library Integration

Guide for converting existing projects and libraries to use the automatic library integration system.

## Table of Contents

1. [Overview](#overview)
2. [Migrating Projects](#migrating-projects)
3. [Migrating Libraries](#migrating-libraries)
4. [Backward Compatibility](#backward-compatibility)
5. [Rollback Procedures](#rollback-procedures)
6. [Common Migration Scenarios](#common-migration-scenarios)
7. [Troubleshooting](#troubleshooting)

## Overview

### What's Changing?

**Before (Manual):**
- Edit `.gprj` files manually to add HDL sources
- Copy constraint files to project
- Manually track library versions
- No standardized integration

**After (Automatic):**
- Add library to `lib_deps` in platformio.ini
- Gateware and constraints auto-discovered
- Version management via PlatformIO
- Consistent integration patterns

### Migration Benefits

- **Less Manual Work** - No `.gprj` editing
- **Version Control** - Track dependencies explicitly
- **Board Portability** - Libraries provide constraints per board
- **Updates** - Easy library version updates
- **Consistency** - Standard patterns across projects

### Compatibility

**Automatic integration is:**
- ✅ **Fully backward compatible** - Old projects continue working
- ✅ **Opt-in** - Migrate at your own pace
- ✅ **Reversible** - Can revert to manual management

## Migrating Projects

### Project Structure Comparison

**Old Structure (Manual):**
```
my_project/
├── platformio.ini
├── fpga/
│   ├── project.gprj          # Contains ALL HDL files
│   ├── src/
│   │   ├── top.v
│   │   ├── wb_bridge.v       # Library code copied here
│   │   ├── wb_register.v     # Library code copied here
│   │   └── fifo.v            # Library code copied here
│   └── constraints/
│       └── pins.cst          # All constraints mixed together
└── src/
    ├── main.cpp
    └── WishboneSPI.cpp       # Library code copied here
```

**New Structure (Automatic):**
```
my_project/
├── platformio.ini            # Lists lib_deps
├── fpga/
│   ├── project.gprj          # Only project files
│   ├── src/
│   │   └── top.v             # Only your code
│   └── constraints/
│       └── pins.cst          # Only your constraints
└── src/
    └── main.cpp              # Only your code
```

Library code lives in libraries, auto-included during build.

### Step-by-Step Migration

#### Step 1: Identify Library Code

Determine which files came from libraries:

```bash
# List files in fpga/src/
ls fpga/src/

# Common library files:
# - pwb_spi_wb_bridge.v (papilio_wishbone_bus)
# - wb_register_block.v (papilio_wb_register)
# - wb_bram.v (papilio_wb_bram)
# - fifo_sync.v (papilio_wishbone_bus)
# - ws2812b_driver.v (papilio_wishbone_rgb_led)
```

#### Step 2: Add Library Dependencies

Edit `platformio.ini`:

```ini
[env:myproject]
platform = gowin
board = papilio_retrocade
framework = arduino

# Add library dependencies
lib_deps = 
    papilio_wishbone_bus      # Provides wb_bridge, fifo
    papilio_wb_register       # Provides wb_register_block
    papilio_wb_bram           # Provides wb_bram
```

#### Step 3: Remove Library Files from Project

```bash
# Backup first!
cp -r fpga/src fpga/src.backup

# Remove library files (keep only your top.v)
rm fpga/src/pwb_spi_wb_bridge.v
rm fpga/src/wb_register_block.v
rm fpga/src/wb_bram.v
rm fpga/src/fifo_sync.v
```

#### Step 4: Extract Library Constraints

**Old `fpga/constraints/pins.cst`:**
```
# Your project pins
IO_LOC "led_out" 10;
IO_PORT "led_out" IO_TYPE=LVCMOS33;

# SPI pins (from library)
IO_LOC "spi_sclk" 42;
IO_PORT "spi_sclk" IO_TYPE=LVCMOS33;
IO_LOC "spi_mosi" 43;
IO_PORT "spi_mosi" IO_TYPE=LVCMOS33;
# ... etc
```

**New `fpga/constraints/pins.cst`:**
```
# Only your project-specific pins
IO_LOC "led_out" 10;
IO_PORT "led_out" IO_TYPE=LVCMOS33;

# SPI pins now provided by papilio_wishbone_bus library
```

#### Step 5: Clean and Rebuild

```bash
# Clean old build
pio run -t clean

# Build with automatic integration
pio run

# Verify library gateware discovered
# Look for "Library gateware discovered:" in output
```

#### Step 6: Test on Hardware

```bash
# Upload and verify functionality
pio run -t upload
pio device monitor

# All features should work identically
```

### Migration Checklist

- [ ] Backed up project
- [ ] Identified library files
- [ ] Added `lib_deps` to platformio.ini
- [ ] Removed library `.v` files from `fpga/src/`
- [ ] Extracted library constraints
- [ ] Removed copied library `.cpp/.h` from `src/`
- [ ] Clean build succeeds
- [ ] Hardware upload works
- [ ] All features functional
- [ ] Committed changes

### Example Migration

**Before:**

`platformio.ini`:
```ini
[env:myproject]
platform = gowin
board = papilio_retrocade
framework = arduino
```

`fpga/src/` contents:
- top.v (yours)
- pwb_spi_wb_bridge.v (library)
- wb_register_block.v (library)

**After:**

`platformio.ini`:
```ini
[env:myproject]
platform = gowin
board = papilio_retrocade
framework = arduino

lib_deps = 
    papilio_wishbone_bus
    papilio_wb_register
```

`fpga/src/` contents:
- top.v (yours only)

**Result:** Same functionality, cleaner structure, automatic updates.

## Migrating Libraries

### Library Structure Migration

#### Old Library Structure (Non-standard)

```
my_library/
├── library.json          # Basic metadata only
├── README.md
├── src/
│   ├── MyLibrary.h
│   └── MyLibrary.cpp
└── hdl/                  # Non-standard location
    ├── module.v
    └── pins.cst          # No board-specific files
```

#### New Library Structure (Papilio-compatible)

```
papilio_my_library/
├── library.json          # Enhanced with papilio metadata
├── README.md
├── AI_SKILL.md           # New: AI assistant instructions
├── src/
│   ├── PapilioMyLibrary.h     # Renamed with Papilio prefix
│   ├── PapilioMyLibrary.cpp
│   ├── PapilioMyLibraryOS.h   # New: CLI interface
│   └── PapilioMyLibraryOS.cpp
├── gateware/             # Renamed from hdl/
│   ├── README.md
│   ├── my_module.v
│   └── constraints/      # New: board-specific files
│       ├── papilio_retrocade.cst
│       └── papilio_synth.cst
├── tests/                # New: testing infrastructure
│   ├── sim/
│   └── hw/
└── examples/
    └── MyLibraryExample/
        └── MyLibraryExample.ino
```

### Step-by-Step Library Migration

#### Step 1: Rename and Restructure

```bash
# Rename library
mv my_library papilio_my_library
cd papilio_my_library

# Rename firmware files
mv src/MyLibrary.h src/PapilioMyLibrary.h
mv src/MyLibrary.cpp src/PapilioMyLibrary.cpp

# Rename gateware directory
mv hdl gateware

# Create board-specific constraints directory
mkdir -p gateware/constraints
```

#### Step 2: Update library.json

Add `papilio` metadata section:

```json
{
  "name": "papilio_my_library",
  "version": "1.0.0",
  
  "papilio": {
    "gateware": {
      "modules": [
        {
          "name": "my_module",
          "file": "gateware/my_module.v",
          "description": "Module description",
          "parameters": {
            "BASE_ADDR": {
              "type": "integer",
              "default": "16'h0000",
              "description": "Wishbone base address"
            }
          }
        }
      ],
      "constraints": [
        {
          "board": "papilio_retrocade",
          "file": "gateware/constraints/papilio_retrocade.cst"
        }
      ]
    },
    
    "wishbone": {
      "data_width": 32,
      "addr_width": 16,
      "supports_burst": false
    },
    
    "esp32": {
      "class": "PapilioMyLibrary",
      "header": "PapilioMyLibrary.h",
      "dependencies": ["WishboneSPI"]
    }
  },
  
  "export": {
    "include": [
      "src/*.h",
      "src/*.cpp",
      "gateware/*.v",
      "gateware/constraints/*.cst",
      "README.md"
    ]
  }
}
```

#### Step 3: Create Board-Specific Constraints

Split monolithic constraint file:

**Old `gateware/pins.cst`:**
```
IO_LOC "external_pin" 23;
```

**New `gateware/constraints/papilio_retrocade.cst`:**
```
# Papilio RetroCade Constraint File
# Library: papilio_my_library

IO_LOC "external_pin" 23;
IO_PORT "external_pin" IO_TYPE=LVCMOS33;
```

**New `gateware/constraints/papilio_synth.cst`:**
```
# Papilio Synth Constraint File
# Library: papilio_my_library

IO_LOC "external_pin" 42;  # Different pin on Synth
IO_PORT "external_pin" IO_TYPE=LVCMOS33;
```

#### Step 4: Update Class Names

**Old `src/MyLibrary.h`:**
```cpp
class MyLibrary {
    // ...
};
```

**New `src/PapilioMyLibrary.h`:**
```cpp
class PapilioMyLibrary {
    // Same API, new name
};
```

#### Step 5: Add CLI Interface (Optional)

Create `src/PapilioMyLibraryOS.h` and `src/PapilioMyLibraryOS.cpp` following the patterns in the Developer Guide.

#### Step 6: Add Documentation

- Update `README.md` with new structure
- Create `AI_SKILL.md` with register maps
- Document all supported boards

#### Step 7: Test Migration

```bash
# Test library can be discovered
pio pkg install --library file://.

# Test in example project
cd ../test_project
# Add to lib_deps
pio run

# Verify gateware discovered
# Verify constraints loaded
# Test on hardware
```

### Library Migration Checklist

- [ ] Renamed to `papilio_<name>`
- [ ] Moved HDL to `gateware/`
- [ ] Created board-specific constraint files
- [ ] Added `papilio` metadata to library.json
- [ ] Updated export includes
- [ ] Renamed classes with `Papilio` prefix
- [ ] Added CLI interface (optional)
- [ ] Created `AI_SKILL.md`
- [ ] Updated documentation
- [ ] Tagged new version
- [ ] Tested with automatic integration

## Backward Compatibility

### Old Projects Still Work

Projects using manual integration **continue to work**:

```
# Old project - still works fine
fpga/
├── project.gprj          # Manually lists all files
├── src/
│   ├── top.v
│   └── library_code.v    # Copied library files
└── constraints/
    └── pins.cst          # All constraints together
```

No migration required unless you want benefits of automatic system.

### Mixed Mode Support

Can use **both** approaches simultaneously:

```ini
[env:mixed]
lib_deps = 
    papilio_wishbone_bus   # Automatic integration
    
# Also have manual files in fpga/src/
# Both work together
```

Project files take precedence over library files if names conflict.

### Gradual Migration

Migrate one library at a time:

**Phase 1:** Keep most files, migrate one library
```
lib_deps = 
    papilio_wishbone_bus   # Migrated to automatic
# Still have other libraries copied manually
```

**Phase 2:** Migrate second library
```
lib_deps = 
    papilio_wishbone_bus
    papilio_wb_register    # Second library migrated
```

**Phase 3:** Complete migration
```
lib_deps = 
    papilio_wishbone_bus
    papilio_wb_register
    papilio_wb_bram        # All migrated
```

### API Compatibility

**Library APIs remain stable:**

```cpp
// Old code - still works
#include <PapilioWbRegister.h>

PapilioWbRegister regs(0x0000);
regs.begin();
regs.write(0, 0x12345678);
```

**Only change:** Include paths now resolve from library instead of local copy.

## Rollback Procedures

### If Migration Fails

**Quick rollback:**

```bash
# Restore backup
rm -rf fpga/src
cp -r fpga/src.backup fpga/src

# Remove lib_deps
# Edit platformio.ini, comment out lib_deps

# Clean and rebuild
pio run -t clean
pio run
```

**Detailed rollback steps:**

1. **Restore source files:**
   ```bash
   git checkout HEAD -- fpga/src/
   ```

2. **Restore constraints:**
   ```bash
   git checkout HEAD -- fpga/constraints/
   ```

3. **Remove lib_deps:**
   ```ini
   # platformio.ini
   # lib_deps =   # Commented out
   ```

4. **Rebuild:**
   ```bash
   pio run -t clean
   pio run
   ```

### Version Pinning

If you need specific library version:

```ini
lib_deps = 
    papilio_wishbone_bus@0.1.0  # Pin to specific version
```

Prevents automatic updates if new version has issues.

### Local Library Override

Keep local modified copy:

```bash
# Copy library locally
cp -r .pio/libdeps/esp32/papilio_wishbone_bus libs/

# Use local copy
```

`platformio.ini`:
```ini
lib_extra_dirs = 
    libs    # Check here first

lib_deps = 
    papilio_wishbone_bus  # Uses local copy from libs/
```

## Common Migration Scenarios

### Scenario 1: Simple Wishbone Project

**Before:**
- Manual Wishbone files in project
- Single constraint file
- No CLI

**Migration:**
1. Add `papilio_wishbone_bus` to lib_deps
2. Remove `pwb_spi_wb_bridge.v` from fpga/src/
3. Keep your top.v
4. Remove SPI constraints (provided by library)
5. Build and test

**Time:** 10 minutes

### Scenario 2: Complex Multi-Module Project

**Before:**
- Multiple copied libraries
- Mixed constraints
- Some customized library code

**Migration:**
1. Identify which files are standard (migrate)
2. Keep customized files in project
3. Add standard libraries to lib_deps
4. Remove only non-customized library files
5. Test incrementally

**Time:** 30-60 minutes

### Scenario 3: Custom Board

**Before:**
- Custom board, not Papilio
- Custom pin assignments
- Using Papilio libraries

**Migration:**
1. Add libraries to lib_deps
2. **Keep all project constraints** (no board-specific library constraints)
3. Library gateware auto-discovered
4. Your constraints override anything from libraries
5. Test carefully

**Time:** 20 minutes

### Scenario 4: Library with Local Modifications

**Before:**
- Copied library code
- Made local modifications
- Don't want to lose changes

**Migration:**

**Option A:** Keep modifications in project (recommended)
```
fpga/src/
├── top.v
└── my_modified_module.v  # Keep your modified version
```

Add unmodified libraries to lib_deps. Your modified version takes precedence.

**Option B:** Create custom library
1. Fork library repository
2. Apply modifications
3. Publish to your GitHub
4. Use your fork:
```ini
lib_deps = 
    https://github.com/yourname/papilio_wishbone_bus.git
```

**Time:** Variable

### Scenario 5: Private/Proprietary Code

**Before:**
- Mix of open and proprietary modules
- Can't publish everything

**Migration:**
1. Separate public (Papilio libraries) from private (your IP)
2. Add public libraries to lib_deps
3. Keep proprietary code in project
4. Use lib_extra_dirs for internal libraries

**Time:** 15 minutes

## Troubleshooting

### Build Fails After Migration

**Symptom:** Synthesis errors after adding lib_deps

**Causes:**
1. Module name conflicts
2. Missing required libraries
3. Parameter mismatches

**Solutions:**

```bash
# Enable verbose output
pio run -v

# Look for:
# - "Library gateware discovered:" lists
# - Synthesis errors about modules
# - Missing module warnings

# Common fixes:
# 1. Add missing dependency
lib_deps = 
    papilio_wishbone_bus
    papilio_wb_register  # Add if missing

# 2. Resolve name conflict - rename your module
# If you have local "wb_register_block.v" and library has same:
mv fpga/src/wb_register_block.v fpga/src/my_register_block.v
# Update instantiations in top.v

# 3. Check parameter values
# Library modules have specific parameter types
wb_register_block #(
    .BASE_ADDR(16'h0000),  # Must be 16-bit literal
    .DATA_WIDTH(32)         # Must be integer
) regs (
    // ...
);
```

### Constraints Not Applied

**Symptom:** Pin assignment errors for library signals

**Causes:**
1. Wrong board name in library
2. Missing constraint file
3. Signal name mismatch

**Solutions:**

```bash
# Check board name
grep "board =" platformio.ini
# Should match library constraint file name

# Verify constraint files exist
ls .pio/libdeps/*/gateware/constraints/

# Check signal names match between .v and .cst
grep "IO_LOC" fpga/constraints/*.cst
grep "output\|input" fpga/src/top.v

# Override library constraint in your project
# fpga/constraints/pins.cst
IO_LOC "spi_sclk" 42;  # Overrides library default
```

### Library Version Conflicts

**Symptom:** Incompatible library versions

**Solution:**

```ini
# Pin compatible versions
lib_deps = 
    papilio_wishbone_bus@0.1.0
    papilio_os@0.2.0
```

### Performance Regression

**Symptom:** Build slower after migration

**Causes:**
1. Too many libraries
2. Unnecessary dependencies

**Solutions:**

```ini
# Remove unused libraries
lib_deps = 
    papilio_wishbone_bus
    # papilio_wb_bram  # Comment out if not used
```

### Can't Find Module After Migration

**Symptom:** `MODULE 'xyz' not found`

**Cause:** Library not in lib_deps

**Solution:**

```bash
# Check which library provides module
grep -r "module xyz" .pio/libdeps/*/gateware/

# Add to lib_deps
lib_deps = 
    papilio_<library_name>
```

## Getting Help

### Resources

- **User Guide** - Complete usage documentation
- **Developer Guide** - Creating compatible libraries
- **Examples** - Working migrated projects
- **Community** - Discord, GitHub discussions

### Support Channels

1. **Check documentation first** - Most questions answered here
2. **Search GitHub issues** - May already be reported
3. **Ask on Discord** - Community can help
4. **Open GitHub issue** - For bugs or feature requests

### Reporting Issues

Include:
- platformio.ini configuration
- Build output (`pio run -v`)
- Library versions (`pio pkg list`)
- Error messages
- What you expected vs what happened

---

**Version:** 1.0.0  
**Last Updated:** January 2026  
**Platform:** Gowin FPGA Platform for PlatformIO
