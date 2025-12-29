#!/usr/bin/env python3
"""
FPGA Build Script for PlatformIO + Gowin Toolchain
Automatically syncs Verilog sources and constraints to .gprj project file,
then invokes Gowin EDA tools to build the FPGA bitstream.
"""

Import("env")
import os
import sys
import subprocess
import shutil
from pathlib import Path
import xml.etree.ElementTree as ET

def find_gowin_toolchain():
    """
    Locate Gowin toolchain installation.
    Checks common installation paths and environment variables.
    """
    # Check environment variable first
    gowin_home = os.environ.get("GOWIN_HOME")
    if gowin_home and os.path.exists(gowin_home):
        return Path(gowin_home)
    
    # Check platformio.ini config
    gowin_path = env.GetProjectOption("board_build.gowin_path", None)
    if gowin_path and os.path.exists(gowin_path):
        return Path(gowin_path)
    
    # Check common installation paths
    common_paths = [
        Path("C:/Gowin"),
        Path("C:/Gowin_V1.9.9"),
        Path("C:/Gowin_V1.9.8"),
        Path("/opt/gowin"),
        Path("/usr/local/gowin"),
        Path.home() / "Gowin",
    ]
    
    for path in common_paths:
        if path.exists():
            return path
    
    return None

def find_gw_sh(gowin_home):
    """Find gw_sh executable in Gowin installation."""
    if not gowin_home:
        return None
    
    # Windows
    gw_sh_win = gowin_home / "IDE" / "bin" / "gw_sh.exe"
    if gw_sh_win.exists():
        return gw_sh_win
    
    # Linux/Mac
    gw_sh_unix = gowin_home / "IDE" / "bin" / "gw_sh"
    if gw_sh_unix.exists():
        return gw_sh_unix
    
    return None

def scan_fpga_sources(fpga_dir):
    """
    Recursively scan FPGA directory for source files.
    Returns dict with 'verilog' and 'constraints' file lists.
    """
    sources = {
        'verilog': [],
        'constraints': []
    }
    
    fpga_path = Path(fpga_dir)
    if not fpga_path.exists():
        return sources
    
    # Scan for Verilog files
    src_dir = fpga_path / "src"
    if src_dir.exists():
        for ext in ['.v', '.sv', '.vh', '.svh']:
            sources['verilog'].extend(src_dir.rglob(f"*{ext}"))
    
    # Scan for constraint files
    constraints_dir = fpga_path / "constraints"
    if constraints_dir.exists():
        sources['constraints'].extend(constraints_dir.rglob("*.cst"))
    
    return sources

def update_gprj_file(gprj_path, sources, fpga_dir):
    """
    Update .gprj XML file with discovered source files.
    Preserves user-added IP cores and other settings.
    """
    if not os.path.exists(gprj_path):
        print(f"Warning: Project file not found: {gprj_path}")
        return False
    
    try:
        # Parse XML with proper encoding
        tree = ET.parse(gprj_path)
        root = tree.getroot()
        
        # Find or create FileList section
        filelist = root.find('FileList')
        if filelist is None:
            filelist = ET.SubElement(root, 'FileList')
        
        # Remove existing auto-generated entries (marked with comment)
        # Keep user-added IP cores and files
        for file_elem in list(filelist.findall('File')):
            path = file_elem.get('path', '')
            # Remove if it's a standard source/constraint file
            if any(ext in path for ext in ['.v', '.sv', '.cst', '.sdc']):
                # Check if it's auto-managed (from src/ or constraints/)
                if 'src/' in path or 'constraints/' in path:
                    filelist.remove(file_elem)
        
        fpga_path = Path(fpga_dir)
        
        # Add Verilog source files
        for verilog_file in sorted(sources['verilog']):
            file_elem = ET.SubElement(filelist, 'File')
            # Use relative path from project file location
            rel_path = verilog_file.relative_to(fpga_path.parent)
            file_elem.set('path', str(rel_path).replace('\\', '/'))
            file_elem.set('type', 'file.verilog')
            file_elem.set('enable', '1')
        
        # Add constraint files
        for cst_file in sorted(sources['constraints']):
            file_elem = ET.SubElement(filelist, 'File')
            rel_path = cst_file.relative_to(fpga_path.parent)
            file_elem.set('path', str(rel_path).replace('\\', '/'))
            file_elem.set('type', 'file.cst')
            file_elem.set('enable', '1')
        
        # Write back to file
        tree.write(gprj_path, encoding='utf-8', xml_declaration=True)
        return True
        
    except Exception as e:
        print(f"Error updating .gprj file: {e}")
        return False

def build_fpga_bitstream(gw_sh_path, gprj_path, fpga_dir):
    """
    Invoke Gowin toolchain to build FPGA bitstream.
    """
    print("=" * 70)
    print("Building FPGA Gateware...")
    print("=" * 70)
    
    # Build command
    cmd = [str(gw_sh_path), str(gprj_path)]
    
    print(f"Executing: {' '.join(cmd)}")
    print(f"Working directory: {fpga_dir}")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(fpga_dir),
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        # Print output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        
        if result.returncode != 0:
            print(f"✗ FPGA build failed with exit code {result.returncode}")
            return None
        
        # Find generated bitstream
        impl_dir = Path(fpga_dir) / "impl" / "pnr"
        bitstream_candidates = list(impl_dir.glob("*.bin"))
        
        if not bitstream_candidates:
            print("✗ No .bin bitstream found after build")
            return None
        
        bitstream = bitstream_candidates[0]
        print(f"✓ FPGA bitstream generated: {bitstream}")
        return bitstream
        
    except subprocess.TimeoutExpired:
        print("✗ FPGA build timed out after 10 minutes")
        return None
    except Exception as e:
        print(f"✗ FPGA build error: {e}")
        return None

def copy_bitstream_to_build(bitstream_path, env):
    """
    Copy generated bitstream to PlatformIO build directory.
    """
    if not bitstream_path or not os.path.exists(bitstream_path):
        return None
    
    build_dir = Path(env.subst("$BUILD_DIR"))
    dest = build_dir / "fpga_bitstream.bin"
    
    try:
        shutil.copy2(bitstream_path, dest)
        print(f"✓ Bitstream copied to {dest}")
        return dest
    except Exception as e:
        print(f"Warning: Could not copy bitstream: {e}")
        return None

def build_fpga_post_action(source, target, env):
    """
    Post-build action called after ESP32 firmware is built.
    """
    print("\n" + "=" * 70)
    print("Post-Build: FPGA Gateware Synthesis")
    print("=" * 70)
    
    # Get project configuration
    project_dir = Path(env.get("PROJECT_DIR"))
    fpga_dir = project_dir / "fpga"
    
    # Get project file path from config or use default
    gprj_file = env.GetProjectOption("board_build.fpga_project", "fpga/project.gprj")
    gprj_path = project_dir / gprj_file
    
    if not gprj_path.exists():
        print(f"✗ FPGA project file not found: {gprj_path}")
        print("  Skipping FPGA build.")
        return
    
    # Find Gowin toolchain
    gowin_home = find_gowin_toolchain()
    if not gowin_home:
        print("✗ Gowin toolchain not found!")
        print("  Set GOWIN_HOME environment variable or board_build.gowin_path in platformio.ini")
        print("  Skipping FPGA build.")
        return
    
    print(f"✓ Gowin toolchain found: {gowin_home}")
    
    # Find gw_sh executable
    gw_sh = find_gw_sh(gowin_home)
    if not gw_sh:
        print(f"✗ gw_sh not found in {gowin_home}")
        print("  Skipping FPGA build.")
        return
    
    print(f"✓ gw_sh found: {gw_sh}")
    
    # Scan for FPGA sources
    print("\nScanning for FPGA source files...")
    sources = scan_fpga_sources(fpga_dir)
    print(f"  Found {len(sources['verilog'])} Verilog file(s)")
    print(f"  Found {len(sources['constraints'])} constraint file(s)")
    
    # Update project file
    print(f"\nUpdating project file: {gprj_path}")
    if not update_gprj_file(gprj_path, sources, fpga_dir):
        print("  Warning: Could not update project file, continuing anyway...")
    else:
        print("  ✓ Project file updated")
    
    # Build FPGA bitstream
    print("\nStarting FPGA synthesis and place & route...")
    bitstream = build_fpga_bitstream(gw_sh, gprj_path, fpga_dir)
    
    if bitstream:
        # Copy to build directory
        copied = copy_bitstream_to_build(bitstream, env)
        if copied:
            # Store path for upload script
            env["FPGA_BITSTREAM"] = str(copied)
        
        print("\n" + "=" * 70)
        print("✓ FPGA Build Complete!")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print("✗ FPGA Build Failed")
        print("=" * 70)
        # Don't fail the entire build, just warn
        print("  Warning: FPGA build failed, but ESP32 firmware was built successfully.")

# Register post-build action
# This runs after the ESP32 .elf file is created
env.AddPostAction("$BUILD_DIR/${PROGNAME}.elf", build_fpga_post_action)

print("FPGA build script loaded - will build FPGA gateware after ESP32 firmware")
