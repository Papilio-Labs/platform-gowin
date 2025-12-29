"""
HDL Framework for Pure FPGA Projects

Provides build configuration for HDL (Verilog/SystemVerilog/VHDL) FPGA projects.
Supports mixed-language designs with both Verilog and VHDL source files.
"""

from os.path import join
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

# Build the FPGA bitstream
fpga_bitstream = env.Alias(
    "buildprog",
    join("$BUILD_DIR", "$PROGNAME$PROGSUFFIX"),
    env["FPGA_BUILD_ACTION"]
)

# Set as default target
env.Default(fpga_bitstream)
