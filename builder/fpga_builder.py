"""
FPGA Builder Helper Functions

Provides SCons-compatible functions for building Gowin FPGA bitstreams.
Integrates with Papilio Automatic Library Builder for auto-generated code.
"""

Import("env")
import os
import sys
import subprocess
import shutil
from pathlib import Path
import xml.etree.ElementTree as ET

# Import Papilio builder
import sys
_debug_log = open("c:/temp/papilio_debug.log", "w")
_debug_log.write("Starting fpga_builder.py\n")
_debug_log.flush()

try:
    from . import papilio_builder
    PAPILIO_BUILDER_AVAILABLE = True
    _debug_log.write("SUCCESS: Relative import worked\n")
    _debug_log.flush()
except ImportError as e:
    _debug_log.write(f"FAILED: Relative import: {e}\n")
    _debug_log.flush()
    try:
        import papilio_builder
        PAPILIO_BUILDER_AVAILABLE = True
        _debug_log.write("SUCCESS: Absolute import worked\n")
        _debug_log.flush()
    except ImportError as e2:
        _debug_log.write(f"FAILED: Absolute import: {e2}\n")
        _debug_log.flush()
        PAPILIO_BUILDER_AVAILABLE = False

def find_gowin_toolchain(env):
    """Locate Gowin toolchain installation."""
    # Check environment variable first
    gowin_home = os.environ.get("GOWIN_HOME")
    if gowin_home and os.path.exists(gowin_home):
        gw_sh = find_gw_sh(Path(gowin_home))
        if gw_sh:
            return Path(gowin_home)
    
    # Check board config (may not exist)
    try:
        gowin_path = env.BoardConfig().get("build.gowin_path")
        if gowin_path and os.path.exists(gowin_path):
            gw_sh = find_gw_sh(Path(gowin_path))
            if gw_sh:
                return Path(gowin_path)
    except KeyError:
        pass
    
    # Check common installation paths and their subdirectories
    common_paths = [
        Path("C:/Gowin"),
        Path("/opt/gowin"),
        Path("/usr/local/gowin"),
        Path.home() / "Gowin",
    ]
    
    for base_path in common_paths:
        if not base_path.exists():
            continue
            
        # First check if gw_sh is directly in this path
        gw_sh = find_gw_sh(base_path)
        if gw_sh:
            return base_path
        
        # Search for versioned subdirectories (e.g., Gowin_V1.9.11.03_Education_x64)
        try:
            for subdir in base_path.iterdir():
                if subdir.is_dir() and subdir.name.startswith("Gowin"):
                    gw_sh = find_gw_sh(subdir)
                    if gw_sh:
                        return subdir
        except (PermissionError, OSError):
            continue
    
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


def update_gprj_file(
    gprj_path,
    sources,
    fpga_dir,
    library_hdl_files=None,
    board_constraint_files=None,
    library_constraint_files=None,
):
    """
    Update .gprj XML file with discovered source files.
    
    Args:
        gprj_path: Path to the .gprj file
        sources: Dict of source file lists from scan_fpga_sources
        fpga_dir: FPGA directory path
        library_hdl_files: Optional list of HDL files from Papilio libraries
    """
    if not os.path.exists(gprj_path):
        print(f"Warning: Project file not found: {gprj_path}")
        return False
    
    try:
        tree = ET.parse(gprj_path)
        root = tree.getroot()
        
        # Update Device element with correct format from board config if env is available
        device_elem = root.find('Device')
        if device_elem is not None and hasattr(update_gprj_file, '_env'):
            env = update_gprj_file._env
            device_name = env.BoardConfig().get("build.device", "GW2A-18C")
            device_full = env.BoardConfig().get("build.fpga_device_full", "GW2A-LV18PG256C8/I7")
            device_code = env.BoardConfig().get("build.device_code", "gw2a18c-011")
            
            device_elem.set('name', device_name)
            device_elem.set('pn', device_full)
            device_elem.text = device_code
        
        filelist = root.find('FileList')
        if filelist is None:
            filelist = ET.SubElement(root, 'FileList')
        
        def _format_path(target_path: Path) -> str:
            """Return a project-relative path string for the .gprj file."""
            try:
                rel_path = os.path.relpath(target_path, gprj_parent)
            except ValueError:
                rel_path = str(target_path)
            return rel_path.replace('\\', '/')

        # Remove all existing file entries (we'll rebuild deterministically)
        for file_elem in list(filelist.findall('File')):
            filelist.remove(file_elem)
        
        fpga_path = Path(fpga_dir)
        gprj_parent = Path(gprj_path).parent
        
        added_paths: Set[str] = set()

        def add_file_entry(path: Path, file_type: str):
            rel = _format_path(Path(path))
            if rel in added_paths:
                return
            file_elem = ET.SubElement(filelist, 'File')
            file_elem.set('path', rel)
            file_elem.set('type', file_type)
            file_elem.set('enable', '1')
            added_paths.add(rel)

        # Add Verilog source files
        for verilog_file in sorted(sources['verilog']):
            add_file_entry(verilog_file, 'file.verilog')
        
        # Add VHDL source files
        for vhdl_file in sorted(sources['vhdl']):
            add_file_entry(vhdl_file, 'file.vhdl')
        
        # Add constraint files (project-level + board-level + library-level)
        extra_constraints: List[Path] = []
        if board_constraint_files:
            extra_constraints.extend(board_constraint_files)
        if library_constraint_files:
            extra_constraints.extend(library_constraint_files)
        for cst_file in sorted(sources['constraints'] + extra_constraints):
            add_file_entry(cst_file, 'file.cst')
        
        # Add Papilio library HDL files
        if library_hdl_files:
            for hdl_file in sorted(library_hdl_files, key=str):
                hdl_path = Path(hdl_file)
                ext = hdl_path.suffix.lower()
                file_type = 'file.vhdl' if ext in ['.vhd', '.vhdl'] else 'file.verilog'
                add_file_entry(hdl_path, file_type)
        
        tree.write(gprj_path, encoding='utf-8', xml_declaration=True)
        return True
        
    except Exception as e:
        print(f"Error updating .gprj file: {e}")
        return False

def get_fpga_sources(env):
    """Get all FPGA source files for dependency tracking."""
    project_dir = Path(env.get("PROJECT_DIR"))
    fpga_dir = project_dir / "fpga"
    
    # Get project file
    gprj_file = env.BoardConfig().get("build.fpga_project", "fpga/project.gprj")
    gprj_path = project_dir / gprj_file
    
    all_sources = []
    
    if gprj_path.exists():
        all_sources.append(str(gprj_path))
        
        # Scan for source files
        sources = scan_fpga_sources(fpga_dir)
        all_sources.extend([str(f) for f in sources['verilog']])
        all_sources.extend([str(f) for f in sources['vhdl']])
        all_sources.extend([str(f) for f in sources['constraints']])
    
    return all_sources


def resolve_board_constraint_files(env, project_dir: Path) -> List[Path]:
    """Resolve board-level constraint files defined by the board configuration."""
    files = env.BoardConfig().get("build.fpga_constraint_files", [])
    if isinstance(files, str):
        files = [files]
    resolved: List[Path] = []
    platform_entry = Path(env.PioPlatform().get_dir())
    platform_root = platform_entry if platform_entry.is_dir() else platform_entry.parent
    for entry in files:
        if not entry:
            continue
        path = Path(entry)
        candidates = []
        if path.is_absolute():
            candidates.append(path)
        else:
            candidates.append(project_dir / entry)
            candidates.append(platform_root / entry)
        found = None
        for candidate in candidates:
            if candidate.exists():
                found = candidate.resolve()
                break
        if found:
            resolved.append(found)
        else:
            print(f"Warning: Board constraint file not found: {entry}")
    return resolved


def run_papilio_builder(env, project_dir, board_id: Optional[str] = None):
    """
    Run the Papilio automatic library builder.
    
    Returns the builder instance (or None when unavailable).
    """
    # Debug: Write to file to confirm this function is called
    debug_file = Path(project_dir) / "papilio_debug.txt"
    debug_file.write_text(f"run_papilio_builder called\nPAPILIO_BUILDER_AVAILABLE = {PAPILIO_BUILDER_AVAILABLE}\n")
    
    if not PAPILIO_BUILDER_AVAILABLE:
        print("Note: Papilio automatic library builder not available")
        return None
    
    verbose = env.BoardConfig().get("build.papilio_verbose", "0") in ("1", "true", "True")
    
    print("="* 70)
    print("Running Papilio Automatic Library Builder...")
    print("=" * 70)
    
    # Check if auto-builder is enabled
    auto_builder = env.BoardConfig().get("build.papilio_auto_builder", "1")
    if auto_builder not in ("1", "true", "True"):
        if verbose:
            print("Papilio auto-builder disabled via board config")
        return None
    
    # Get library configuration
    try:
        lib_deps = env.GetProjectOption("lib_deps", [])
        if isinstance(lib_deps, str):
            lib_deps = [lib_deps]
    except:
        lib_deps = []
    
    try:
        lib_extra_dirs = env.GetProjectOption("lib_extra_dirs", [])
        if isinstance(lib_extra_dirs, str):
            lib_extra_dirs = [lib_extra_dirs]
        lib_extra_dirs = [Path(d) for d in lib_extra_dirs]
    except:
        lib_extra_dirs = []
    
    # Find FPGA top module and ESP32 main
    fpga_top = project_dir / "fpga" / "src" / "top.v"
    esp32_main = project_dir / "src" / "main.cpp"
    
    # Run the builder
    builder = papilio_builder.PapilioBuilder(project_dir, verbose=verbose)
    success = builder.run(
        lib_deps=lib_deps,
        lib_extra_dirs=lib_extra_dirs,
        fpga_top=fpga_top if fpga_top.exists() else None,
        esp32_main=esp32_main if esp32_main.exists() else None,
        board_id=board_id
    )
    
    if not success:
        print("WARNING: Papilio builder reported errors, continuing with build...")
    
    return builder


def build_fpga_action(target, source, env):
    """SCons action for building FPGA bitstream."""
    print("=" * 70)
    print("Building FPGA Gateware...")
    print("=" * 70)
    
    project_dir = Path(env.get("PROJECT_DIR"))
    fpga_dir = project_dir / "fpga"
    
    board_id = env.BoardConfig().get("build.papilio_board")
    # Run Papilio automatic library builder
    builder = run_papilio_builder(env, project_dir, board_id)
    library_hdl_files: List[Path] = []
    library_constraint_files: List[Path] = []
    if builder:
        library_hdl_files = builder.get_library_hdl_files()
        library_constraint_files = builder.get_library_constraint_files()
    
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
    if library_hdl_files:
        print(f"  Found {len(library_hdl_files)} Papilio library HDL file(s)")
    board_constraint_files = resolve_board_constraint_files(env, project_dir)
    if board_constraint_files:
        print(f"  Including {len(board_constraint_files)} board constraint file(s)")
    if library_constraint_files:
        print(f"  Including {len(library_constraint_files)} library constraint file(s)")
    
    print(f"Updating project file: {gprj_path}")
    # Pass env to update_gprj_file via function attribute for Device element update
    update_gprj_file._env = env
    update_gprj_file(
        gprj_path,
        sources,
        fpga_dir,
        library_hdl_files,
        board_constraint_files,
        library_constraint_files,
    )
    
    # Register all source files as dependencies for this build
    all_sources = sources['verilog'] + sources['vhdl'] + sources['constraints']
    all_sources.extend(board_constraint_files)
    all_sources.extend(library_constraint_files)
    all_sources.extend(library_hdl_files)  # Add library HDL files
    all_sources.append(gprj_path)  # Also depend on the project file
    # Convert Path objects to strings for SCons
    all_sources_str = [str(s) for s in all_sources]
    env.Depends(target, all_sources_str)
    
    # Get top module name from board config
    top_module = env.BoardConfig().get("build.fpga_top_module", "top")
    
    # Get dual-purpose pin configuration options
    use_sspi_as_gpio = env.BoardConfig().get("build.use_sspi_as_gpio", "0")
    use_mspi_as_gpio = env.BoardConfig().get("build.use_mspi_as_gpio", "0")
    use_jtag_as_gpio = env.BoardConfig().get("build.use_jtag_as_gpio", "0")
    use_ready_as_gpio = env.BoardConfig().get("build.use_ready_as_gpio", "0")
    use_done_as_gpio = env.BoardConfig().get("build.use_done_as_gpio", "0")
    
    # Get multi-boot configuration options
    multi_boot = env.BoardConfig().get("build.multi_boot", "0")
    spi_flash_address = env.BoardConfig().get("build.spi_flash_address", "")
    
    # Create impl directory if it doesn't exist
    impl_dir = fpga_dir / "impl"
    impl_dir.mkdir(exist_ok=True)
    
    # Create Tcl script for gw_sh in the FPGA root (matches reference projects)
    tcl_script = fpga_dir / "build_script.tcl"
    relative_gprj = os.path.relpath(gprj_path, fpga_dir).replace('\\', '/')
    with open(tcl_script, 'w') as f:
        f.write(f"""# Auto-generated Tcl script for gw_sh
# Open project
open_project {relative_gprj}

# Set top module explicitly
set_option -top_module {top_module}
""")
        
        # Add dual-purpose pin configuration options if enabled
        if use_sspi_as_gpio in ("1", "true", "True", "yes", "Yes"):
            f.write("\n# Use SSPI pins as regular I/O\n")
            f.write("set_option -use_sspi_as_gpio 1\n")
        
        if use_mspi_as_gpio in ("1", "true", "True", "yes", "Yes"):
            f.write("\n# Use MSPI pins as regular I/O\n")
            f.write("set_option -use_mspi_as_gpio 1\n")
        
        if use_jtag_as_gpio in ("1", "true", "True", "yes", "Yes"):
            f.write("\n# Use JTAG pins as regular I/O\n")
            f.write("set_option -use_jtag_as_gpio 1\n")
        
        if use_ready_as_gpio in ("1", "true", "True", "yes", "Yes"):
            f.write("\n# Use READY pin as regular I/O\n")
            f.write("set_option -use_ready_as_gpio 1\n")
        
        if use_done_as_gpio in ("1", "true", "True", "yes", "Yes"):
            f.write("\n# Use DONE pin as regular I/O\n")
            f.write("set_option -use_done_as_gpio 1\n")
        
        # Add multi-boot configuration if enabled
        if multi_boot in ("1", "true", "True", "yes", "Yes"):
            f.write("\n# Enable Multi Boot\n")
            f.write("set_option -multi_boot 1\n")
            
            # Set SPI flash address if provided
            if spi_flash_address:
                # Ensure address has 0x prefix if it's a hex value
                addr = spi_flash_address.strip()
                if not addr.startswith("0x") and not addr.startswith("0X"):
                    addr = "0x" + addr
                f.write(f"set_option -spi_flash_addr {addr}\n")
        
        f.write("""
# Run all (synthesis, place and route, bitstream generation)
run all

# Close project
exit
""")
    
    # Build FPGA bitstream using Tcl script
    print("Starting FPGA synthesis and place & route...")
    result = subprocess.run(
        [str(gw_sh), str(tcl_script)],
        cwd=str(fpga_dir),
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',  # Replace unencodable characters
        timeout=600
    )
    
    if result.stdout:
        # Print output, replacing characters that can't be displayed
        try:
            print(result.stdout)
        except UnicodeEncodeError:
            print(result.stdout.encode('ascii', 'replace').decode('ascii'))
    if result.stderr:
        try:
            print(result.stderr, file=sys.stderr)
        except UnicodeEncodeError:
            print(result.stderr.encode('ascii', 'replace').decode('ascii'), file=sys.stderr)
    
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
    # Ensure the copied file is writable (remove read-only attribute)
    os.chmod(dest, 0o666)
    print(f"✓ Bitstream copied to {dest}")
    
    print("=" * 70)
    print("✓ FPGA Build Complete!")
    print("=" * 70)
    
    return 0

# Register the FPGA build action and source getter with the environment
env["FPGA_BUILD_ACTION"] = build_fpga_action
env["GET_FPGA_SOURCES"] = get_fpga_sources
