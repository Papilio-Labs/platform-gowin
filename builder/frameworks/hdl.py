"""
HDL Framework for Pure FPGA Projects

Provides build configuration for HDL (Verilog/SystemVerilog/VHDL) FPGA projects.
Supports mixed-language designs with both Verilog and VHDL source files.
"""

from os.path import join
from pathlib import Path
from SCons.Script import DefaultEnvironment

env = DefaultEnvironment()
platform = env.PioPlatform()
board = env.BoardConfig()

# Configure environment for FPGA build
env.Replace(
    PROGNAME="fpga_bitstream",
    PROGSUFFIX=".bin"
)

# Get FPGA configuration from board
fpga_project = board.get("build.fpga_project", "fpga/project.gprj")
fpga_device = board.get("build.device", "GW5A-25A")
fpga_family = board.get("build.fpga_family", "GW5A")

# Set build flags
env.Append(
    CPPDEFINES=[
        ("FPGA_DEVICE", '\\"%s\\"' % fpga_device),
        ("FPGA_FAMILY", '\\"%s\\"' % fpga_family)
    ]
)

# Get FPGA source files for dependency tracking
fpga_sources = env["GET_FPGA_SOURCES"](env)

# Build the FPGA bitstream using the FPGA build action
fpga_bitstream = env.Command(
    join("$BUILD_DIR", "$PROGNAME$PROGSUFFIX"),
    fpga_sources,  # Track FPGA sources as dependencies
    env["FPGA_BUILD_ACTION"]
)


# Create alias and set as default
env.Alias("buildprog", fpga_bitstream)
env.Default(fpga_bitstream)
