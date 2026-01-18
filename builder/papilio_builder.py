"""
Papilio Automatic Library Builder

Discovers Papilio libraries via metadata, generates Wishbone interconnects,
instantiates HDL modules, and creates ESP32 initialization code through
marker-based injection.

Schema Version: 1.0
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import xml.etree.ElementTree as ET


# =============================================================================
# Schema Definitions (Task 1.1)
# =============================================================================

SCHEMA_VERSION = "1.0"

# Required fields in papilio metadata
REQUIRED_GATEWARE_FIELDS = ["modules"]
REQUIRED_MODULE_FIELDS = ["name", "file"]
REQUIRED_WISHBONE_FIELDS = ["type"]  # address_range can be auto-assigned

# Marker definitions (Task 3.1)
class MarkerType(Enum):
    """Types of auto-generation markers."""
    WISHBONE = "WISHBONE"           # Wishbone interconnect (Verilog)
    MODULE_INST = "MODULE_INST"     # Module instantiations (Verilog)
    PORTS = "PORTS"                 # Port declarations (Verilog)
    WIRES = "WIRES"                 # Wire declarations (Verilog)
    INCLUDES = "INCLUDES"           # #include directives (C++)
    GLOBALS = "GLOBALS"             # Global object declarations (C++)
    INIT = "INIT"                   # Initialization code (C++)
    CLI = "CLI"                     # CLI dispatcher (C++)


MARKER_BEGIN_TEMPLATE = "//# PAPILIO_AUTO_{section}_BEGIN"
MARKER_END_TEMPLATE = "//# PAPILIO_AUTO_{section}_END"


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class WishboneConfig:
    """Wishbone slave configuration from library metadata."""
    type: str  # "slave", "master", or "bridge"
    address_range: Optional[str] = None  # e.g., "0x1000-0x10FF" or "auto"
    address_size: int = 256  # Size in bytes for auto-allocation
    data_width: int = 32
    burst_support: bool = False
    
    # Computed after allocation
    base_address: int = 0
    end_address: int = 0


@dataclass
class GatewareModule:
    """HDL module specification from library metadata."""
    name: str
    file: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    ports: Dict[str, str] = field(default_factory=dict)  # port_name -> signal_name
    template: Optional[str] = None  # Instantiation template
    
    # Resolved path after discovery
    resolved_path: Optional[Path] = None


@dataclass
class ESP32Config:
    """ESP32 integration specification from library metadata."""
    class_name: str
    headers: List[str] = field(default_factory=list)
    constructor_args: List[str] = field(default_factory=list)
    init_code: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)


@dataclass
class CLICommand:
    """CLI command specification from library metadata."""
    name: str
    handler: str
    help_text: str
    args: List[str] = field(default_factory=list)


@dataclass
class PapilioLibrary:
    """Complete Papilio library specification."""
    name: str
    version: str
    path: Path
    
    # Gateware configuration
    modules: List[GatewareModule] = field(default_factory=list)
    wishbone: Optional[WishboneConfig] = None
    
    # ESP32 configuration
    esp32: Optional[ESP32Config] = None
    
    # CLI configuration (optional)
    cli_commands: List[CLICommand] = field(default_factory=list)
    
    # Validation state
    is_valid: bool = False
    validation_errors: List[str] = field(default_factory=list)


# =============================================================================
# Schema Validator (Task 1.3)
# =============================================================================

class SchemaValidator:
    """Validates library.json papilio metadata against schema."""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate(self, library_name: str, papilio_data: Dict) -> bool:
        """
        Validate papilio metadata section.
        
        Returns True if valid, False otherwise.
        Errors are accumulated in self.errors.
        """
        self.errors = []
        self.warnings = []
        
        if not papilio_data:
            self.errors.append(f"{library_name}: Missing 'papilio' section in library.json")
            return False
        
        # Check schema version
        version = papilio_data.get("schema_version", "1.0")
        if version != SCHEMA_VERSION:
            self.warnings.append(f"{library_name}: Schema version {version} differs from current {SCHEMA_VERSION}")
        
        # Validate gateware section
        gateware = papilio_data.get("gateware", {})
        if gateware:
            self._validate_gateware(library_name, gateware)
        
        # Validate wishbone section
        wishbone = papilio_data.get("wishbone", {})
        if wishbone:
            self._validate_wishbone(library_name, wishbone)
        
        # Validate esp32 section
        esp32 = papilio_data.get("esp32", {})
        if esp32:
            self._validate_esp32(library_name, esp32)
        
        # Validate cli section (optional)
        cli = papilio_data.get("cli", {})
        if cli:
            self._validate_cli(library_name, cli)
        
        return len(self.errors) == 0
    
    def _validate_gateware(self, lib_name: str, gateware: Dict):
        """Validate gateware section."""
        modules = gateware.get("modules", [])
        if not modules:
            self.errors.append(f"{lib_name}: gateware.modules is required and must not be empty")
            return
        
        for i, module in enumerate(modules):
            if not isinstance(module, dict):
                self.errors.append(f"{lib_name}: gateware.modules[{i}] must be an object")
                continue
            
            for field in REQUIRED_MODULE_FIELDS:
                if field not in module:
                    self.errors.append(f"{lib_name}: gateware.modules[{i}].{field} is required")
    
    def _validate_wishbone(self, lib_name: str, wishbone: Dict):
        """Validate wishbone section."""
        wb_type = wishbone.get("type")
        if not wb_type:
            self.errors.append(f"{lib_name}: wishbone.type is required")
        elif wb_type not in ("slave", "master", "bridge"):
            self.errors.append(f"{lib_name}: wishbone.type must be 'slave', 'master', or 'bridge'")
        
        # Validate address_range format if specified
        addr_range = wishbone.get("address_range")
        if addr_range and addr_range != "auto":
            if not self._validate_address_range(addr_range):
                self.errors.append(f"{lib_name}: wishbone.address_range '{addr_range}' is invalid. Use format '0x1000-0x10FF' or 'auto'")
    
    def _validate_address_range(self, addr_range: str) -> bool:
        """Validate address range format."""
        pattern = r'^0x[0-9A-Fa-f]+-0x[0-9A-Fa-f]+$'
        return bool(re.match(pattern, addr_range))
    
    def _validate_esp32(self, lib_name: str, esp32: Dict):
        """Validate esp32 section."""
        if "class_name" not in esp32:
            self.errors.append(f"{lib_name}: esp32.class_name is required")
        
        headers = esp32.get("headers", [])
        if not isinstance(headers, list):
            self.errors.append(f"{lib_name}: esp32.headers must be an array")
    
    def _validate_cli(self, lib_name: str, cli: Dict):
        """Validate cli section."""
        commands = cli.get("commands", [])
        if not isinstance(commands, list):
            self.errors.append(f"{lib_name}: cli.commands must be an array")
            return
        
        for i, cmd in enumerate(commands):
            if not isinstance(cmd, dict):
                self.errors.append(f"{lib_name}: cli.commands[{i}] must be an object")
                continue
            
            if "name" not in cmd:
                self.errors.append(f"{lib_name}: cli.commands[{i}].name is required")
            if "handler" not in cmd:
                self.errors.append(f"{lib_name}: cli.commands[{i}].handler is required")


# =============================================================================
# Library Discovery (Task 2.1, 2.2)
# =============================================================================

class LibraryDiscovery:
    """Discovers and parses Papilio libraries from PlatformIO project."""
    
    def __init__(self, project_dir: Path, verbose: bool = False):
        self.project_dir = project_dir
        self.verbose = verbose
        self.validator = SchemaValidator()
        self.discovered_libraries: List[PapilioLibrary] = []
    
    def discover(self, lib_deps: List[str], lib_extra_dirs: List[Path]) -> List[PapilioLibrary]:
        """
        Discover all Papilio libraries in the project.
        
        Args:
            lib_deps: List of library names from platformio.ini lib_deps
            lib_extra_dirs: List of additional library directories
            
        Returns:
            List of discovered PapilioLibrary objects
        """
        self.discovered_libraries = []
        
        # Scan lib_extra_dirs for libraries
        for lib_dir in lib_extra_dirs:
            self._scan_library_directory(lib_dir)
        
        # Also scan standard PlatformIO lib locations
        pio_lib_dir = self.project_dir / ".pio" / "libdeps"
        if pio_lib_dir.exists():
            for env_dir in pio_lib_dir.iterdir():
                if env_dir.is_dir():
                    self._scan_library_directory(env_dir)
        
        # Scan project lib directory
        project_lib = self.project_dir / "lib"
        if project_lib.exists():
            self._scan_library_directory(project_lib)
        
        if self.verbose:
            print(f"Discovered {len(self.discovered_libraries)} Papilio libraries")
            for lib in self.discovered_libraries:
                status = "✓" if lib.is_valid else "✗"
                print(f"  {status} {lib.name} @ {lib.path}")
        
        return self.discovered_libraries
    
    def _scan_library_directory(self, lib_dir: Path):
        """Scan a directory for Papilio libraries."""
        if not lib_dir.exists():
            return
        
        for item in lib_dir.iterdir():
            if item.is_dir():
                library_json = item / "library.json"
                if library_json.exists():
                    self._process_library(item, library_json)
    
    def _process_library(self, lib_path: Path, library_json: Path):
        """Process a single library directory."""
        try:
            with open(library_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check if this is a Papilio library
            papilio_data = data.get("papilio")
            if not papilio_data:
                return  # Not a Papilio library, skip silently
            
            # Create library object
            library = PapilioLibrary(
                name=data.get("name", lib_path.name),
                version=data.get("version", "0.0.0"),
                path=lib_path
            )
            
            # Validate metadata
            if self.validator.validate(library.name, papilio_data):
                library.is_valid = True
                self._parse_metadata(library, papilio_data)
            else:
                library.is_valid = False
                library.validation_errors = self.validator.errors.copy()
                if self.verbose:
                    for error in library.validation_errors:
                        print(f"  Warning: {error}")
            
            self.discovered_libraries.append(library)
            
        except json.JSONDecodeError as e:
            if self.verbose:
                print(f"  Error parsing {library_json}: {e}")
        except Exception as e:
            if self.verbose:
                print(f"  Error processing {lib_path}: {e}")
    
    def _parse_metadata(self, library: PapilioLibrary, papilio_data: Dict):
        """Parse validated papilio metadata into library object."""
        # Parse gateware modules
        gateware = papilio_data.get("gateware", {})
        for mod_data in gateware.get("modules", []):
            module = GatewareModule(
                name=mod_data["name"],
                file=mod_data["file"],
                parameters=mod_data.get("parameters", {}),
                ports=mod_data.get("ports", {}),
                template=mod_data.get("template")
            )
            
            # Resolve file path
            module.resolved_path = library.path / mod_data["file"]
            library.modules.append(module)
        
        # Parse wishbone config
        wb_data = papilio_data.get("wishbone", {})
        if wb_data:
            library.wishbone = WishboneConfig(
                type=wb_data.get("type", "slave"),
                address_range=wb_data.get("address_range", "auto"),
                address_size=wb_data.get("address_size", 256),
                data_width=wb_data.get("data_width", 32),
                burst_support=wb_data.get("burst_support", False)
            )
        
        # Parse ESP32 config
        esp32_data = papilio_data.get("esp32", {})
        if esp32_data:
            headers = esp32_data.get("headers", [])
            if isinstance(headers, str):
                headers = [headers]

            constructor_args = esp32_data.get("constructor_args", [])
            if isinstance(constructor_args, str):
                constructor_args = [constructor_args]
            elif not isinstance(constructor_args, list):
                constructor_args = [str(constructor_args)]

            dependencies = esp32_data.get("dependencies", [])
            if isinstance(dependencies, str):
                dependencies = [dependencies]

            library.esp32 = ESP32Config(
                class_name=esp32_data.get("class_name", ""),
                headers=headers,
                constructor_args=constructor_args,
                init_code=esp32_data.get("init_code"),
                dependencies=dependencies
            )
        
        # Parse CLI commands
        cli_data = papilio_data.get("cli", {})
        for cmd_data in cli_data.get("commands", []):
            command = CLICommand(
                name=cmd_data["name"],
                handler=cmd_data["handler"],
                help_text=cmd_data.get("help_text", ""),
                args=cmd_data.get("args", [])
            )
            library.cli_commands.append(command)


# =============================================================================
# Wishbone Address Allocator (Task 4.1, 4.2)
# =============================================================================

class AddressAllocator:
    """Allocates non-overlapping Wishbone addresses to peripherals."""
    
    # Address space layout
    SLOT_BASE = 0x0000      # Slot tier base
    SLOT_SIZE = 0x1000      # 4KB per slot
    MAX_SLOTS = 32          # Maximum slot count
    
    EXTENDED_BASE = 0x2000  # Extended tier base (after slot 0-1)
    LARGE_BASE = 0x10000    # Large tier base
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.allocations: Dict[str, Tuple[int, int]] = {}  # lib_name -> (base, end)
        self.next_auto_slot = 1  # Slot 0 is reserved for system
        self.conflicts: List[str] = []
    
    def allocate(self, libraries: List[PapilioLibrary]) -> bool:
        """
        Allocate addresses for all libraries.
        
        Returns True if successful, False if conflicts detected.
        """
        self.allocations = {}
        self.conflicts = []
        self.next_auto_slot = 1
        
        # First pass: process explicit address assignments
        for lib in libraries:
            if not lib.wishbone or not lib.is_valid:
                continue
            
            addr_range = lib.wishbone.address_range
            if addr_range and addr_range != "auto":
                self._allocate_explicit(lib, addr_range)
        
        # Second pass: auto-allocate remaining libraries
        for lib in libraries:
            if not lib.wishbone or not lib.is_valid:
                continue
            
            addr_range = lib.wishbone.address_range
            if not addr_range or addr_range == "auto":
                self._allocate_auto(lib)
        
        # Check for conflicts
        self._detect_conflicts()
        
        if self.verbose:
            self._print_address_map()
        
        return len(self.conflicts) == 0
    
    def _allocate_explicit(self, lib: PapilioLibrary, addr_range: str):
        """Allocate an explicit address range."""
        match = re.match(r'0x([0-9A-Fa-f]+)-0x([0-9A-Fa-f]+)', addr_range)
        if match:
            base = int(match.group(1), 16)
            end = int(match.group(2), 16)
            
            lib.wishbone.base_address = base
            lib.wishbone.end_address = end
            self.allocations[lib.name] = (base, end)
            
            if self.verbose:
                print(f"  Allocated {lib.name}: 0x{base:04X}-0x{end:04X} (explicit)")
    
    def _allocate_auto(self, lib: PapilioLibrary):
        """Auto-allocate address range for a library."""
        size = lib.wishbone.address_size
        
        # Find next available slot
        while self.next_auto_slot < self.MAX_SLOTS:
            base = self.SLOT_BASE + (self.next_auto_slot * self.SLOT_SIZE)
            end = base + size - 1
            
            # Check if this range conflicts with existing allocations
            conflict = False
            for name, (alloc_base, alloc_end) in self.allocations.items():
                if self._ranges_overlap(base, end, alloc_base, alloc_end):
                    conflict = True
                    break
            
            if not conflict:
                lib.wishbone.base_address = base
                lib.wishbone.end_address = end
                self.allocations[lib.name] = (base, end)
                self.next_auto_slot += 1
                
                if self.verbose:
                    print(f"  Allocated {lib.name}: 0x{base:04X}-0x{end:04X} (auto, slot {self.next_auto_slot - 1})")
                return
            
            self.next_auto_slot += 1
        
        self.conflicts.append(f"{lib.name}: No available address slots")
    
    def _ranges_overlap(self, base1: int, end1: int, base2: int, end2: int) -> bool:
        """Check if two address ranges overlap."""
        return not (end1 < base2 or end2 < base1)
    
    def _detect_conflicts(self):
        """Detect any address conflicts between allocations."""
        alloc_list = list(self.allocations.items())
        
        for i, (name1, (base1, end1)) in enumerate(alloc_list):
            for name2, (base2, end2) in alloc_list[i+1:]:
                if self._ranges_overlap(base1, end1, base2, end2):
                    self.conflicts.append(
                        f"Address conflict: {name1} (0x{base1:04X}-0x{end1:04X}) "
                        f"overlaps with {name2} (0x{base2:04X}-0x{end2:04X})"
                    )
    
    def _print_address_map(self):
        """Print the address allocation map."""
        print("\n  Wishbone Address Map:")
        print("  " + "-" * 50)
        for name, (base, end) in sorted(self.allocations.items(), key=lambda x: x[1][0]):
            size = end - base + 1
            print(f"  0x{base:04X} - 0x{end:04X}  ({size:5d} bytes)  {name}")
        print("  " + "-" * 50)
    
    def generate_address_map_file(self, output_path: Path):
        """Generate human-readable address map file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            f.write("# Papilio Wishbone Address Map\n")
            f.write("# Auto-generated by Papilio Library Builder\n")
            f.write("#\n")
            f.write("# Base       End        Size     Library\n")
            f.write("# " + "-" * 50 + "\n")
            
            for name, (base, end) in sorted(self.allocations.items(), key=lambda x: x[1][0]):
                size = end - base + 1
                f.write(f"  0x{base:04X}     0x{end:04X}     {size:5d}    {name}\n")


# =============================================================================
# Marker-Based Code Injection (Task 3.2, 3.3)
# =============================================================================

class MarkerInjector:
    """Handles marker-based code injection into source files."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
    
    def get_marker_begin(self, section: MarkerType) -> str:
        """Get the begin marker for a section."""
        return MARKER_BEGIN_TEMPLATE.format(section=section.value)
    
    def get_marker_end(self, section: MarkerType) -> str:
        """Get the end marker for a section."""
        return MARKER_END_TEMPLATE.format(section=section.value)
    
    def find_marker_region(self, content: str, section: MarkerType) -> Optional[Tuple[int, int, str]]:
        """
        Find a marker region in content.
        
        Returns (start_idx, end_idx, existing_content) or None if not found.
        """
        begin_marker = self.get_marker_begin(section)
        end_marker = self.get_marker_end(section)
        
        begin_idx = content.find(begin_marker)
        if begin_idx == -1:
            return None
        
        # Find the end of the begin marker line
        begin_line_end = content.find('\n', begin_idx)
        if begin_line_end == -1:
            begin_line_end = len(content)
        
        end_idx = content.find(end_marker, begin_line_end)
        if end_idx == -1:
            return None
        
        # Extract existing content between markers
        existing = content[begin_line_end + 1:end_idx]
        
        return (begin_line_end + 1, end_idx, existing)
    
    def inject_content(self, content: str, section: MarkerType, new_content: str) -> Tuple[str, bool]:
        """
        Inject new content into a marker region.
        
        Returns (new_content, was_modified).
        If markers not found, returns original content unchanged.
        """
        region = self.find_marker_region(content, section)
        
        if region is None:
            if self.verbose:
                print(f"    Warning: {section.value} markers not found, skipping injection")
            return (content, False)
        
        start_idx, end_idx, existing = region
        
        # Build new content with proper formatting
        formatted_content = new_content
        if not formatted_content.endswith('\n'):
            formatted_content += '\n'
        
        # Replace region content
        new_full_content = content[:start_idx] + formatted_content + content[end_idx:]
        
        return (new_full_content, True)
    
    def inject_file(self, file_path: Path, section: MarkerType, new_content: str) -> bool:
        """
        Inject content into a file's marker region.
        
        Returns True if successful, False otherwise.
        """
        if not file_path.exists():
            if self.verbose:
                print(f"    Warning: File not found: {file_path}")
            return False
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            new_content, modified = self.inject_content(content, section, new_content)
            
            if modified:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                if self.verbose:
                    print(f"    Injected {section.value} into {file_path.name}")
            
            return modified
            
        except Exception as e:
            if self.verbose:
                print(f"    Error injecting into {file_path}: {e}")
            return False


# =============================================================================
# FPGA Code Generator (Task 5.1, 5.2, 5.3)
# =============================================================================

class FPGACodeGenerator:
    """Generates Verilog code for FPGA integration."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
    
    def generate_wire_declarations(self, libraries: List[PapilioLibrary]) -> str:
        """Generate wire declarations for all library instances."""
        lines = ["// Auto-generated wire declarations"]
        
        for lib in libraries:
            if not lib.is_valid or not lib.wishbone:
                continue
            
            # Sanitize library name for Verilog identifier
            inst_name = self._to_verilog_id(lib.name)
            data_width = int(lib.wishbone.data_width or 32)
            data_width = max(data_width, 1)
            msb = data_width - 1
            
            lines.append(f"")
            lines.append(f"// {lib.name} signals")
            lines.append(f"wire [{msb}:0] {inst_name}_wb_dat_s2m;")
            lines.append(f"wire        {inst_name}_wb_ack;")
            if lib.wishbone.type == "slave":
                lines.append(f"wire        {inst_name}_wb_sel;")
                lines.append(f"wire        {inst_name}_wb_stb;")
        
        return '\n'.join(lines)
    
    def generate_module_instantiations(self, libraries: List[PapilioLibrary]) -> str:
        """Generate module instantiation code for all libraries."""
        lines = ["// Auto-generated module instantiations"]
        
        for lib in libraries:
            if not lib.is_valid:
                continue
            
            for module in lib.modules:
                inst_code = self._generate_module_instance(lib, module)
                lines.append("")
                lines.append(inst_code)
        
        return '\n'.join(lines)
    
    def _generate_module_instance(self, lib: PapilioLibrary, module: GatewareModule) -> str:
        """Generate instantiation code for a single module."""
        inst_name = self._to_verilog_id(lib.name)
        
        # Use template if provided
        if module.template:
            return self._apply_module_template(lib, inst_name, module.template)
        
        # Generate default instantiation
        lines = [f"// {lib.name} - {module.name}"]
        
        # Build parameter list
        params = []
        for param_name, param_value in module.parameters.items():
            if isinstance(param_value, str):
                params.append(f"    .{param_name}({param_value})")
            else:
                params.append(f"    .{param_name}({param_value})")
        
        if lib.wishbone:
            params.append(f"    .BASE_ADDR(16'h{lib.wishbone.base_address:04X})")
        
        # Build port list
        ports = [
            "    .clk(clk)",
            "    .rst(rst)"
        ]
        
        if lib.wishbone and lib.wishbone.type == "slave":
            ports.extend([
                "    .wb_adr_i(wb_adr)",
                "    .wb_dat_i(wb_dat_m2s)",
                f"    .wb_dat_o({inst_name}_wb_dat_s2m)",
                "    .wb_we_i(wb_we)",
                "    .wb_cyc_i(wb_cyc)",
                "    .wb_stb_i(wb_stb)",
                f"    .wb_ack_o({inst_name}_wb_ack)"
            ])
        
        # Add custom port mappings
        for port_name, signal_name in module.ports.items():
            ports.append(f"    .{port_name}({signal_name})")
        
        # Build instantiation
        if params:
            lines.append(f"{module.name} #(")
            lines.append(',\n'.join(params))
            lines.append(f") {inst_name}_inst (")
        else:
            lines.append(f"{module.name} {inst_name}_inst (")
        
        lines.append(',\n'.join(ports))
        lines.append(");")
        
        return '\n'.join(lines)
    
    def generate_wishbone_interconnect(self, libraries: List[PapilioLibrary]) -> str:
        """Generate Wishbone interconnect logic (address decode + mux)."""
        slave_libs = [lib for lib in libraries if lib.is_valid and lib.wishbone and lib.wishbone.type == "slave"]
        
        if not slave_libs:
            return "// No Wishbone slaves to interconnect"
        
        lines = ["// Auto-generated Wishbone interconnect"]
        lines.append("")
        
        # Generate address decode signals
        lines.append("// Address decode")
        for lib in slave_libs:
            inst_name = self._to_verilog_id(lib.name)
            base = lib.wishbone.base_address
            end = lib.wishbone.end_address
            lines.append(f"assign {inst_name}_wb_sel = (wb_adr >= 16'h{base:04X}) && (wb_adr <= 16'h{end:04X});")
        
        lines.append("")
        
        # Generate strobe gating
        lines.append("// Strobe gating")
        for lib in slave_libs:
            inst_name = self._to_verilog_id(lib.name)
            lines.append(f"assign {inst_name}_wb_stb = wb_stb && {inst_name}_wb_sel;")
        
        lines.append("")
        
        # Generate data mux
        lines.append("// Data multiplexer")
        lines.append("assign wb_dat_s2m = ")
        mux_terms = []
        for lib in slave_libs:
            inst_name = self._to_verilog_id(lib.name)
            mux_terms.append(f"    ({inst_name}_wb_sel ? {inst_name}_wb_dat_s2m : 32'h0)")
        lines.append(" |\n".join(mux_terms) + ";")
        
        lines.append("")
        
        # Generate ACK mux
        lines.append("// ACK multiplexer")
        lines.append("assign wb_ack = ")
        ack_terms = []
        for lib in slave_libs:
            inst_name = self._to_verilog_id(lib.name)
            ack_terms.append(f"    ({inst_name}_wb_sel ? {inst_name}_wb_ack : 1'b0)")
        lines.append(" |\n".join(ack_terms) + ";")
        
        return '\n'.join(lines)
    
    def _to_verilog_id(self, name: str) -> str:
        """Convert a name to a valid Verilog identifier."""
        # Replace non-alphanumeric characters with underscores
        result = re.sub(r'[^a-zA-Z0-9_]', '_', name)
        # Remove leading numbers
        if result and result[0].isdigit():
            result = '_' + result
        return result

    def _apply_module_template(self, lib: PapilioLibrary, inst_name: str, template: str) -> str:
        """Replace known placeholders inside custom module templates."""
        replacements = {
            "${INSTANCE_NAME}": inst_name,
            "${INSTANCE}": inst_name,
        }
        if lib.wishbone:
            replacements["${BASE_ADDR}"] = f"16'h{lib.wishbone.base_address:04X}"
        for placeholder, value in replacements.items():
            template = template.replace(placeholder, value)

        # Legacy compatibility: adjust Wishbone signal names
        template = re.sub(rf"{re.escape(inst_name)}_wb_dat\b", f"{inst_name}_wb_dat_s2m", template)
        template = re.sub(rf"{re.escape(inst_name)}_stb\b", f"{inst_name}_wb_stb", template)
        template = re.sub(rf"{re.escape(inst_name)}_sel\b", f"{inst_name}_wb_sel", template)
        template = template.replace("wb_dat_w", "wb_dat_m2s")
        template = template.replace("wb_dat_r", "wb_dat_s2m")
        return template


# =============================================================================
# ESP32 Code Generator (Task 6.1, 6.2, 6.3)
# =============================================================================

class ESP32CodeGenerator:
    """Generates C++ code for ESP32 integration."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
    
    def generate_includes(self, libraries: List[PapilioLibrary]) -> str:
        """Generate #include directives for all libraries."""
        lines = ["// Auto-generated includes"]
        
        seen_headers = set()
        for lib in libraries:
            if not lib.is_valid or not lib.esp32:
                continue
            
            for header in lib.esp32.headers:
                if header not in seen_headers:
                    lines.append(f'#include <{header}>')
                    seen_headers.add(header)
        
        return '\n'.join(lines)
    
    def generate_globals(self, libraries: List[PapilioLibrary]) -> str:
        """Generate global object declarations."""
        lines = ["// Auto-generated global objects"]
        
        for lib in libraries:
            if not lib.is_valid or not lib.esp32:
                continue
            
            var_name = self._to_cpp_var(lib.name)
            class_name = lib.esp32.class_name
            
            # Build constructor arguments with placeholder substitution
            args_list = []
            for arg in lib.esp32.constructor_args:
                arg_value = str(arg)
                if lib.wishbone:
                    arg_value = arg_value.replace("${BASE_ADDR}", f"0x{lib.wishbone.base_address:04X}")
                arg_value = arg_value.replace("${INSTANCE}", var_name)
                args_list.append(arg_value)
            
            args = ', '.join(args_list)
            
            if args:
                lines.append(f"{class_name} {var_name}({args});")
            else:
                lines.append(f"{class_name} {var_name};")
        
        return '\n'.join(lines)
    
    def generate_init_code(self, libraries: List[PapilioLibrary]) -> str:
        """Generate initialization code for setup()."""
        lines = ["// Auto-generated initialization"]
        
        # Sort by dependencies
        sorted_libs = self._sort_by_dependencies(libraries)
        
        for lib in sorted_libs:
            if not lib.is_valid or not lib.esp32:
                continue
            
            var_name = self._to_cpp_var(lib.name)
            
            # Use custom init code if provided
            if lib.esp32.init_code:
                init_code = lib.esp32.init_code.replace("${VAR}", var_name)
                init_code = init_code.replace("${INSTANCE}", var_name)
                if lib.wishbone:
                    init_code = init_code.replace("${BASE_ADDR}", f"0x{lib.wishbone.base_address:04X}")
                lines.append(init_code)
            else:
                # Default: call begin()
                lines.append(f"{var_name}.begin();")
        
        return '\n'.join(lines)
    
    def generate_cli_dispatcher(self, libraries: List[PapilioLibrary]) -> str:
        """Generate CLI command dispatcher."""
        lines = [
            "// Auto-generated CLI dispatcher",
            "#ifdef PAPILIO_CLI_ENABLED",
            "",
            "void papilio_cli_dispatch(const char* cmd) {"
        ]
        
        for lib in libraries:
            if not lib.is_valid or not lib.cli_commands:
                continue
            
            var_name = self._to_cpp_var(lib.name)
            
            for cmd in lib.cli_commands:
                lines.append(f'    if (strncmp(cmd, "{cmd.name}", {len(cmd.name)}) == 0) {{')
                lines.append(f'        {var_name}.{cmd.handler}(cmd + {len(cmd.name) + 1});')
                lines.append(f'        return;')
                lines.append(f'    }}')
        
        lines.extend([
            '    Serial.println("Unknown command");',
            "}",
            "",
            "#endif // PAPILIO_CLI_ENABLED"
        ])
        
        return '\n'.join(lines)
    
    def _to_cpp_var(self, name: str) -> str:
        """Convert a library name to a C++ variable name."""
        # Convert to camelCase
        parts = re.split(r'[_\-]', name)
        if not parts:
            return name
        
        # First part lowercase, rest title case
        result = parts[0].lower()
        for part in parts[1:]:
            result += part.title()
        
        return result
    
    def _sort_by_dependencies(self, libraries: List[PapilioLibrary]) -> List[PapilioLibrary]:
        """Sort libraries by dependencies (dependencies first)."""
        # Build dependency graph
        lib_map = {lib.name: lib for lib in libraries}
        sorted_libs = []
        visited = set()
        
        def visit(lib_name: str):
            if lib_name in visited:
                return
            visited.add(lib_name)
            
            lib = lib_map.get(lib_name)
            if lib and lib.esp32:
                for dep in lib.esp32.dependencies:
                    if dep in lib_map:
                        visit(dep)
            
            if lib:
                sorted_libs.append(lib)
        
        for lib in libraries:
            visit(lib.name)
        
        return sorted_libs


# =============================================================================
# Main Builder Class (Task 8.1)
# =============================================================================

class PapilioBuilder:
    """
    Main builder class that orchestrates library discovery, code generation,
    and integration.
    """
    
    def __init__(self, project_dir: Path, verbose: bool = False):
        self.project_dir = project_dir
        self.verbose = verbose
        
        # Components
        self.discovery = LibraryDiscovery(project_dir, verbose)
        self.allocator = AddressAllocator(verbose)
        self.injector = MarkerInjector(verbose)
        self.fpga_gen = FPGACodeGenerator(verbose)
        self.esp32_gen = ESP32CodeGenerator(verbose)
        
        # State
        self.libraries: List[PapilioLibrary] = []
        self.errors: List[str] = []
        self.board_id: Optional[str] = None
    
    def run(self, lib_deps: List[str], lib_extra_dirs: List[Path],
            fpga_top: Optional[Path] = None,
            esp32_main: Optional[Path] = None,
            board_id: Optional[str] = None) -> bool:
        """
        Run the automatic library builder.
        
        Args:
            lib_deps: Library dependencies from platformio.ini
            lib_extra_dirs: Additional library directories
            fpga_top: Path to FPGA top module (for injection)
            esp32_main: Path to ESP32 main.cpp (for injection)
            
        Returns:
            True if successful, False if errors occurred
        """
        self.errors = []
        self.board_id = board_id
        
        if self.verbose:
            print("=" * 60)
            print("Papilio Automatic Library Builder")
            print("=" * 60)
        
        # Step 1: Discover libraries
        if self.verbose:
            print("\n[1/5] Discovering Papilio libraries...")
        
        self.libraries = self.discovery.discover(lib_deps, lib_extra_dirs)
        
        valid_libs = [lib for lib in self.libraries if lib.is_valid]
        if not valid_libs:
            if self.verbose:
                print("  No valid Papilio libraries found, skipping auto-generation")
            return True
        
        # Collect validation errors
        for lib in self.libraries:
            if not lib.is_valid:
                self.errors.extend(lib.validation_errors)
        
        # Step 2: Allocate addresses
        if self.verbose:
            print("\n[2/5] Allocating Wishbone addresses...")
        
        if not self.allocator.allocate(valid_libs):
            self.errors.extend(self.allocator.conflicts)
            self._report_errors()
            return False
        
        # Generate address map file
        papilio_dir = self.project_dir / ".papilio"
        self.allocator.generate_address_map_file(papilio_dir / "address_map.txt")
        
        # Step 3: Generate FPGA code
        if fpga_top and fpga_top.exists():
            if self.verbose:
                print(f"\n[3/5] Generating FPGA code for {fpga_top.name}...")
            
            self._inject_fpga_code(fpga_top, valid_libs)
        else:
            if self.verbose:
                print("\n[3/5] Skipping FPGA code generation (no top module found)")
        
        # Step 4: Generate ESP32 code
        if esp32_main and esp32_main.exists():
            if self.verbose:
                print(f"\n[4/5] Generating ESP32 code for {esp32_main.name}...")
            
            self._inject_esp32_code(esp32_main, valid_libs)
        else:
            if self.verbose:
                print("\n[4/5] Skipping ESP32 code generation (no main.cpp found)")
        
        # Step 5: Update .gprj file with library HDL files
        if self.verbose:
            print("\n[5/5] Updating FPGA project file...")
        
        # This will be handled by existing fpga_builder.py
        # We just need to ensure library HDL files are in a scannable location
        
        if self.verbose:
            print("\n" + "=" * 60)
            print("[OK] Papilio Library Builder completed successfully")
            print("=" * 60)
        
        return len(self.errors) == 0
    
    def _inject_fpga_code(self, fpga_top: Path, libraries: List[PapilioLibrary]):
        """Inject generated FPGA code into the top module."""
        # Generate wire declarations
        wires = self.fpga_gen.generate_wire_declarations(libraries)
        self.injector.inject_file(fpga_top, MarkerType.WIRES, wires)
        
        # Generate module instantiations
        instances = self.fpga_gen.generate_module_instantiations(libraries)
        self.injector.inject_file(fpga_top, MarkerType.MODULE_INST, instances)
        
        # Generate Wishbone interconnect
        interconnect = self.fpga_gen.generate_wishbone_interconnect(libraries)
        self.injector.inject_file(fpga_top, MarkerType.WISHBONE, interconnect)
    
    def _inject_esp32_code(self, esp32_main: Path, libraries: List[PapilioLibrary]):
        """Inject generated ESP32 code into main.cpp."""
        # Generate includes
        includes = self.esp32_gen.generate_includes(libraries)
        self.injector.inject_file(esp32_main, MarkerType.INCLUDES, includes)
        
        # Generate global objects
        globals_code = self.esp32_gen.generate_globals(libraries)
        self.injector.inject_file(esp32_main, MarkerType.GLOBALS, globals_code)
        
        # Generate init code
        init = self.esp32_gen.generate_init_code(libraries)
        self.injector.inject_file(esp32_main, MarkerType.INIT, init)
        
        # Generate CLI dispatcher (optional)
        cli = self.esp32_gen.generate_cli_dispatcher(libraries)
        self.injector.inject_file(esp32_main, MarkerType.CLI, cli)
    
    def _report_errors(self):
        """Report all accumulated errors."""
        if self.errors:
            print("\n" + "=" * 60)
            print("Papilio Library Builder - ERRORS")
            print("=" * 60)
            for error in self.errors:
                print(f"  [X] {error}")
            print("=" * 60)
    
    def get_library_hdl_files(self) -> List[Path]:
        """Get all HDL files from discovered libraries for .gprj inclusion."""
        hdl_files: List[Path] = []
        seen: Set[Path] = set()
        
        for lib in self.libraries:
            if not lib.is_valid:
                continue
            
            for module in lib.modules:
                if module.resolved_path and module.resolved_path.exists():
                    path = module.resolved_path.resolve()
                    if path not in seen:
                        hdl_files.append(path)
                        seen.add(path)
            
            gateware_dir = lib.path / "gateware"
            if gateware_dir.exists():
                for extra_file in gateware_dir.rglob("*"):
                    if not extra_file.is_file():
                        continue
                    if "constraints" in extra_file.parts:
                        continue
                    if extra_file.suffix.lower() not in {".v", ".sv", ".vh", ".vhd", ".vhdl"}:
                        continue
                    path = extra_file.resolve()
                    if path not in seen:
                        hdl_files.append(path)
                        seen.add(path)
        
        return hdl_files

    def get_library_constraint_files(self) -> List[Path]:
        """Get board-specific constraint files supplied by libraries."""
        constraint_files: List[Path] = []
        board_id = self.board_id
        if not board_id:
            return constraint_files
        seen: Set[Path] = set()
        for lib in self.libraries:
            constraints_dir = lib.path / "gateware" / "constraints"
            candidate = constraints_dir / f"{board_id}.cst"
            if candidate.exists():
                path = candidate.resolve()
                if path not in seen:
                    constraint_files.append(path)
                    seen.add(path)
        return constraint_files


# =============================================================================
# PlatformIO Integration Hook
# =============================================================================

def papilio_pre_build(env):
    """
    PlatformIO pre-build hook for automatic library integration.
    
    Called before FPGA synthesis to discover libraries and generate code.
    """
    import sys
    from pathlib import Path
    
    project_dir = Path(env.get("PROJECT_DIR"))
    verbose = env.BoardConfig().get("build.papilio_verbose", "0") in ("1", "true", "True")
    
    # Check if auto-builder is enabled
    auto_builder = env.BoardConfig().get("build.papilio_auto_builder", "1")
    if auto_builder not in ("1", "true", "True"):
        if verbose:
            print("Papilio auto-builder disabled via board config")
        return
    
    # Get library configuration
    lib_deps = env.GetProjectOption("lib_deps", [])
    if isinstance(lib_deps, str):
        lib_deps = [lib_deps]
    
    lib_extra_dirs = env.GetProjectOption("lib_extra_dirs", [])
    if isinstance(lib_extra_dirs, str):
        lib_extra_dirs = [lib_extra_dirs]
    lib_extra_dirs = [Path(d) for d in lib_extra_dirs]
    
    # Find FPGA top module and ESP32 main
    fpga_top = project_dir / "fpga" / "src" / "top.v"
    esp32_main = project_dir / "src" / "main.cpp"
    board_id = env.BoardConfig().get("build.papilio_board")
    
    # Run the builder
    builder = PapilioBuilder(project_dir, verbose=verbose)
    success = builder.run(
        lib_deps=lib_deps,
        lib_extra_dirs=lib_extra_dirs,
        fpga_top=fpga_top if fpga_top.exists() else None,
        esp32_main=esp32_main if esp32_main.exists() else None,
        board_id=board_id
    )
    
    if not success:
        sys.exit(1)
    
    # Store library HDL files for .gprj update
    env["PAPILIO_HDL_FILES"] = builder.get_library_hdl_files()


# Export for SCons
if __name__ != "__main__":
    try:
        Import("env")
        # Register pre-build hook
        env.AddPreAction("$BUILD_DIR/${PROGNAME}.bin", papilio_pre_build)
    except:
        pass  # Not running under SCons
