"""
Gowin FPGA Builder for PlatformIO

SCons-based build script for Gowin FPGA projects.
Supports both pure FPGA projects and dual-target projects (MCU + FPGA).
"""

from os.path import join
from SCons.Script import (AlwaysBuild, Builder, Default, DefaultEnvironment)

env = DefaultEnvironment()
platform = env.PioPlatform()
board = env.BoardConfig()

# Import FPGA build functions from scripts
env.SConscript(join(platform.get_dir(), "builder", "fpga_builder.py"), exports="env")

# Get framework
frameworks = env.get("PIOFRAMEWORK", [])

if "arduino" in frameworks:
    # Dual-target build: Arduino (ESP32) + FPGA
    # First build the ESP32 firmware using Arduino framework
    env.SConscript(
        join(platform.get_package_dir("framework-arduinoespressif32"), "tools", "platformio-build.py")
    )
    
    # Then add FPGA build as post-action
    firmware = env.get("PIOMAINPROG")
    env.AddPostAction(firmware, env.VerboseAction(env["FPGA_BUILD_ACTION"], "Building FPGA gateware..."))
    
elif "hdl" in frameworks or "verilog" in frameworks:
    # Pure FPGA build (hdl is the new name, verilog is kept for backwards compatibility)
    env.SConscript(join(platform.get_dir(), "builder", "frameworks", "hdl.py"), exports="env")
    
else:
    # Default to hdl framework for FPGA-only boards
    env.SConscript(join(platform.get_dir(), "builder", "frameworks", "hdl.py"), exports="env")

# Configure upload based on protocol
upload_protocol = env.subst("$UPLOAD_PROTOCOL")
upload_actions = []

# Default uploader (will be replaced based on protocol)
env.Replace(
    UPLOADER="",
    UPLOADCMD="$UPLOADER $UPLOADERFLAGS $SOURCE"
)

if upload_protocol == "pesptool":
    env.Replace(
        UPLOADER="pesptool",
        UPLOADERFLAGS=[
            "--port", "$UPLOAD_PORT",
            "write_flash",
            "0x100000"  # FPGA flash address
        ]
    )
    upload_actions = [
        env.VerboseAction("$UPLOADCMD", "Uploading FPGA bitstream via pesptool...")
    ]
    
elif upload_protocol == "openfpgaloader":
    board_type = board.get("build.fpga_board_type", "tangnano9k")
    env.Replace(
        UPLOADER="openFPGALoader",
        UPLOADERFLAGS=[
            "-b", board_type,
            "-f"
        ]
    )
    upload_actions = [
        env.VerboseAction("$UPLOADCMD", "Uploading FPGA bitstream via openFPGALoader...")
    ]
    
elif upload_protocol == "gowin":
    device = board.get("build.fpga_device_full", "GW5A-25A")
    env.Replace(
        UPLOADER="gwprog",
        UPLOADERFLAGS=[
            "-d", device,
            "-f"
        ]
    )
    upload_actions = [
        env.VerboseAction("$UPLOADCMD", "Uploading FPGA bitstream via Gowin Programmer...")
    ]
    
elif upload_protocol == "esptool":
    # For dual-target boards, ESP32 upload only
    # FPGA upload must be done separately
    env.Replace(
        UPLOADER="esptool.py",
        UPLOADERFLAGS=[
            "--chip", "esp32s3",
            "--port", "$UPLOAD_PORT",
            "--baud", "$UPLOAD_SPEED",
            "write_flash",
            "-z",
            "0x0"
        ]
    )
    upload_actions = [
        env.VerboseAction("$UPLOADCMD", "Uploading ESP32 firmware...")
    ]

# Create upload target
AlwaysBuild(env.Alias("upload", "$BUILD_DIR/${PROGNAME}.bin", upload_actions))
