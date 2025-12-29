"""
FPGA Builder Helper Functions

Provides SCons-compatible functions for building Gowin FPGA bitstreams.
"""

Import("env")
import os
import sys
import subprocess
import shutil
from pathlib import Path
import xml.etree.ElementTree as ET

def find_gowin_toolchain(env):
    """Locate Gowin toolchain installation."""
    # Check environment variable first
    gowin_home = os.environ.get("GOWIN_HOME")
    if gowin_home and os.path.exists(gowin_home):
        return Path(gowin_home)
    
    # Check board config (may not exist)
    try:
        gowin_path = env.BoardConfig().get("build.gowin_path")
        if gowin_path and os.path.exists(gowin_path):
            return Path(gowin_path)
    except KeyError:
        pass
    
    # Check common installation paths
    common_paths = [
        Path("C:/Gowin"),
        Path("C:/Gowin_V1.9.9"),
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
    """Recursively scan FPGA directory for source files."""
    sources = {
        'verilog': [],
        'vhdl': [],
        'constraints': []
    }
    
    fpga_path = Path(fpga_dir)
    if not fpga_path.exists():
        return sources
    
    # Scan for HDL source files
    src_dir = fpga_path / "src"
    if src_dir.exists():
        # Verilog/SystemVerilog files
        for ext in ['.v', '.sv', '.vh', '.svh']:
            sources['verilog'].extend(src_dir.rglob(f"*{ext}"))
        # VHDL files
        for ext in ['.vhd', '.vhdl']:
            sources['vhdl'].extend(src_dir.rglob(f"*{ext}"))
    
    # Scan for constraint files
    constraints_dir = fpga_path / "constraints"
    if constraints_dir.exists():
        sources['constraints'].extend(constraints_dir.rglob("*.cst"))
    
    return sources

def update_gprj_file(gprj_path, sources, fpga_dir):
    """Update .gprj XML file with discovered source files."""
    if not os.path.exists(gprj_path):
        print(f"Warning: Project file not found: {gprj_path}")
        return False
    
    try:
        tree = ET.parse(gprj_path)
        root = tree.getroot()
        
        filelist = root.find('FileList')
        if filelist is None:
            filelist = ET.SubElement(root, 'FileList')
        
        # Remove existing auto-generated entries
        for file_elem in list(filelist.findall('File')):
            path = file_elem.get('path', '')
            if any(ext in path for ext in ['.v', '.sv', '.vhd', '.vhdl', '.cst', '.sdc']):
                if 'src/' in path or 'constraints/' in path:
                    filelist.remove(file_elem)
        
        fpga_path = Path(fpga_dir)
        gprj_parent = Path(gprj_path).parent
        
        # Add Verilog source files
        for verilog_file in sorted(sources['verilog']):
            file_elem = ET.SubElement(filelist, 'File')
            rel_path = verilog_file.relative_to(gprj_parent)
            file_elem.set('path', str(rel_path).replace('\\', '/'))
            file_elem.set('type', 'file.verilog')
            file_elem.set('enable', '1')
        
        # Add VHDL source files
        for vhdl_file in sorted(sources['vhdl']):
            file_elem = ET.SubElement(filelist, 'File')
            rel_path = vhdl_file.relative_to(gprj_parent)
            file_elem.set('path', str(rel_path).replace('\\', '/'))
            file_elem.set('type', 'file.vhdl')
            file_elem.set('enable', '1')
        
        # Add constraint files
        for cst_file in sorted(sources['constraints']):
            file_elem = ET.SubElement(filelist, 'File')
            rel_path = cst_file.relative_to(gprj_parent)
            file_elem.set('path', str(rel_path).replace('\\', '/'))
            file_elem.set('type', 'file.cst')
            file_elem.set('enable', '1')
        
        tree.write(gprj_path, encoding='utf-8', xml_declaration=True)
        return True
        
    except Exception as e:
        print(f"Error updating .gprj file: {e}")
        return False

def build_fpga_action(target, source, env):
    """SCons action for building FPGA bitstream."""
    print("=" * 70)
    print("Building FPGA Gateware...")
    print("=" * 70)
    
    project_dir = Path(env.get("PROJECT_DIR"))
    fpga_dir = project_dir / "fpga"
    
    # Get project file
    gprj_file = env.BoardConfig().get("build.fpga_project", "fpga/project.gprj")
    gprj_path = project_dir / gprj_file
    
    if not gprj_path.exists():
        print(f"Warning: FPGA project file not found: {gprj_path}")
        print("Skipping FPGA build.")
        return 0
    
    # Find Gowin toolchain
    gowin_home = find_gowin_toolchain(env)
    if not gowin_home:
        print("Warning: Gowin toolchain not found!")
        print("Set GOWIN_HOME environment variable or board_build.gowin_path")
        print("Skipping FPGA build.")
        return 0
    
    gw_sh = find_gw_sh(gowin_home)
    if not gw_sh:
        print(f"Warning: gw_sh not found in {gowin_home}")
        print("Skipping FPGA build.")
        return 0
    
    # Scan and update sources
    print("Scanning for FPGA source files...")
    sources = scan_fpga_sources(fpga_dir)
    print(f"  Found {len(sources['verilog'])} Verilog/SystemVerilog file(s)")
    print(f"  Found {len(sources['vhdl'])} VHDL file(s)")
    print(f"  Found {len(sources['constraints'])} constraint file(s)")
    
    print(f"Updating project file: {gprj_path}")
    update_gprj_file(gprj_path, sources, fpga_dir)
    
    # Create Tcl script for gw_sh
    tcl_script = fpga_dir / "build_script.tcl"
    with open(tcl_script, 'w') as f:
        f.write(f"""# Auto-generated Tcl script for gw_sh
# Open project
open_project {gprj_path.name}

# Run synthesis
run syn

# Run place and route
run pnr


# Close project
exit
"""

)
    
    # Build FPGA bitstream using Tcl script
    print("Starting FPGA synthesis and place & route...")
    result = subprocess.run(
        [str(gw_sh), str(tcl_script)],
        cwd=str(fpga_dir),
        capture_output=True,
        text=True,
        timeout=600
    )
    
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    
    if result.returncode != 0:
        print(f"FPGA build failed with exit code {result.returncode}")
        return result.returncode
    
    # Find generated bitstream
    impl_dir = fpga_dir / "impl" / "pnr"
    bitstream_candidates = list(impl_dir.glob("*.bin"))
    
    if not bitstream_candidates:
        print("Error: No .bin bitstream found after build")
        return 1
    
    bitstream = bitstream_candidates[0]
    print(f"✓ FPGA bitstream generated: {bitstream}")
    
    # Copy to build directory
    build_dir = Path(env.subst("$BUILD_DIR"))
    dest = build_dir / "fpga_bitstream.bin"
    shutil.copy2(bitstream, dest)
    print(f"✓ Bitstream copied to {dest}")
    
    print("=" * 70)
    print("✓ FPGA Build Complete!")
    print("=" * 70)
    
    return 0

# Register the FPGA build action with the environment
env["FPGA_BUILD_ACTION"] = build_fpga_action
