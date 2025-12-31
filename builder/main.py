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

if "hdl" in frameworks:
    # Pure FPGA build
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
    # Download pesptool.exe on Windows if not already available
    import sys
    import os
    from os.path import join, isfile, dirname
    
    pesptool_cmd = "pesptool"
    
    if sys.platform.startswith("win"):
        # Store in platform's packages directory
        platform_dir = dirname(env.PioPlatform().get_dir())
        pesptool_cache_dir = join(platform_dir, ".cache", "pesptool")
        pesptool_exe = join(pesptool_cache_dir, "pesptool.exe")
        
        if not isfile(pesptool_exe):
            # Download pesptool.exe from GitHub releases
            import urllib.request
            import hashlib
            
            os.makedirs(pesptool_cache_dir, exist_ok=True)
            url = "https://github.com/Papilio-Labs/papilio-loader-mcp/releases/download/v0.1.0/pesptool.exe"
            expected_sha256 = "db0ef34bfa24eb3142f30ca58b6bda5c2f14d88d284095fa5e799283771aeed5"
            
            print("Downloading pesptool.exe (20.8 MB)...")
            temp_file = pesptool_exe + ".tmp"
            
            try:
                urllib.request.urlretrieve(url, temp_file)
                
                # Verify SHA256
                sha256_hash = hashlib.sha256()
                with open(temp_file, "rb") as f:
                    for byte_block in iter(lambda: f.read(4096), b""):
                        sha256_hash.update(byte_block)
                
                if sha256_hash.hexdigest().lower() == expected_sha256.lower():
                    os.rename(temp_file, pesptool_exe)
                    print("pesptool.exe downloaded and verified successfully!")
                else:
                    os.remove(temp_file)
                    sys.stderr.write("Error: Downloaded file hash mismatch. Using PATH instead.\n")
                    pesptool_cmd = "pesptool"
            except Exception as e:
                if isfile(temp_file):
                    os.remove(temp_file)
                sys.stderr.write(f"Error downloading pesptool.exe: {e}\n")
                sys.stderr.write("Falling back to PATH. Install via: pip install git+https://github.com/Papilio-Labs/pesptool.git\n")
                pesptool_cmd = "pesptool"
        
        if isfile(pesptool_exe):
            pesptool_cmd = pesptool_exe
    
    # Build flags list - only add --port if explicitly set
    flags = []
    upload_port = env.get("UPLOAD_PORT")
    if upload_port:
        flags.extend(["--port", upload_port])
    flags.extend([
        "write-flash",
        "0x100000"  # FPGA flash address
    ])
    
    env.Replace(
        UPLOADER=pesptool_cmd,
        UPLOADERFLAGS=flags
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
