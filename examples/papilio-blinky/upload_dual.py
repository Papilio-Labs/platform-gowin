#!/usr/bin/env python3
"""
Dual Upload Script for PlatformIO + ESP32S3 + FPGA
Uploads ESP32 firmware via esptool, then uploads FPGA bitstream
via pesptool (default) or alternative upload protocols.
"""

import os
import sys
import subprocess
from pathlib import Path
import argparse

def check_tool_available(tool_name):
    """Check if a tool is available in PATH."""
    try:
        result = subprocess.run(
            [tool_name, "--version"],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False

def upload_esp32_firmware(firmware_path, port, baud=921600):
    """
    Upload ESP32 firmware using esptool.
    """
    print("\n" + "=" * 70)
    print("Uploading ESP32 Firmware...")
    print("=" * 70)
    print(f"Firmware: {firmware_path}")
    print(f"Port: {port}")
    print(f"Baud: {baud}")
    print()
    
    if not os.path.exists(firmware_path):
        raise FileNotFoundError(f"ESP32 firmware not found: {firmware_path}")
    
    cmd = [
        "esptool.py",
        "--chip", "esp32s3",
        "--port", port,
        "--baud", str(baud),
        "write_flash",
        "-z",
        "0x0", firmware_path
    ]
    
    print(f"Command: {' '.join(cmd)}\n")
    
    result = subprocess.run(cmd)
    
    if result.returncode != 0:
        raise Exception(f"ESP32 upload failed with exit code {result.returncode}")
    
    print("\n✓ ESP32 firmware uploaded successfully")
    return True

def upload_fpga_pesptool(bitstream_path, port, address="0x100000"):
    """
    Upload FPGA bitstream using pesptool via ESP32S3 SPI bridge.
    """
    print("\n" + "=" * 70)
    print("Uploading FPGA Bitstream (pesptool)...")
    print("=" * 70)
    print(f"Bitstream: {bitstream_path}")
    print(f"Port: {port}")
    print(f"Flash Address: {address}")
    print()
    
    if not os.path.exists(bitstream_path):
        raise FileNotFoundError(f"FPGA bitstream not found: {bitstream_path}")
    
    # Check if pesptool is available
    if not check_tool_available("pesptool"):
        raise Exception("pesptool not found. Install via: pip install git+https://github.com/Papilio-Labs/pesptool.git")
    
    cmd = [
        "pesptool",
        "--port", port,
        "write_flash",
        address,
        bitstream_path
    ]
    
    print(f"Command: {' '.join(cmd)}\n")
    
    result = subprocess.run(cmd)
    
    if result.returncode != 0:
        raise Exception(f"FPGA upload failed with exit code {result.returncode}")
    
    print("\n✓ FPGA bitstream uploaded successfully (pesptool)")
    return True

def upload_fpga_openfpgaloader(bitstream_path, board="tangnano9k"):
    """
    Upload FPGA bitstream using openFPGALoader (alternative method).
    """
    print("\n" + "=" * 70)
    print("Uploading FPGA Bitstream (openFPGALoader)...")
    print("=" * 70)
    print(f"Bitstream: {bitstream_path}")
    print(f"Board: {board}")
    print()
    
    if not os.path.exists(bitstream_path):
        raise FileNotFoundError(f"FPGA bitstream not found: {bitstream_path}")
    
    # Check if openFPGALoader is available
    if not check_tool_available("openFPGALoader"):
        raise Exception("openFPGALoader not found. Install from: https://github.com/trabucayre/openFPGALoader")
    
    cmd = [
        "openFPGALoader",
        "-b", board,
        "-f", bitstream_path
    ]
    
    print(f"Command: {' '.join(cmd)}\n")
    
    result = subprocess.run(cmd)
    
    if result.returncode != 0:
        raise Exception(f"FPGA upload failed with exit code {result.returncode}")
    
    print("\n✓ FPGA bitstream uploaded successfully (openFPGALoader)")
    return True

def upload_fpga_gowin_programmer(bitstream_path, device="GW5A-25A"):
    """
    Upload FPGA bitstream using Gowin Programmer (proprietary).
    """
    print("\n" + "=" * 70)
    print("Uploading FPGA Bitstream (Gowin Programmer)...")
    print("=" * 70)
    print(f"Bitstream: {bitstream_path}")
    print(f"Device: {device}")
    print()
    
    if not os.path.exists(bitstream_path):
        raise FileNotFoundError(f"FPGA bitstream not found: {bitstream_path}")
    
    # Try gwprog command
    if not check_tool_available("gwprog"):
        raise Exception("Gowin Programmer (gwprog) not found. Ensure Gowin EDA is installed and in PATH.")
    
    cmd = [
        "gwprog",
        "-d", device,
        "-f", bitstream_path
    ]
    
    print(f"Command: {' '.join(cmd)}\n")
    
    result = subprocess.run(cmd)
    
    if result.returncode != 0:
        raise Exception(f"FPGA upload failed with exit code {result.returncode}")
    
    print("\n✓ FPGA bitstream uploaded successfully (Gowin Programmer)")
    return True

def main():
    parser = argparse.ArgumentParser(
        description="Dual-target upload for ESP32 + FPGA",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # ESP32 arguments
    parser.add_argument("--esp32-firmware", 
                       help="Path to ESP32 firmware .bin file")
    parser.add_argument("--esp32-port", 
                       default="COM3" if os.name == "nt" else "/dev/ttyUSB0",
                       help="Serial port for ESP32 (default: COM3 on Windows, /dev/ttyUSB0 on Linux)")
    parser.add_argument("--esp32-baud", 
                       type=int, 
                       default=921600,
                       help="Baud rate for ESP32 upload (default: 921600)")
    parser.add_argument("--skip-esp32", 
                       action="store_true",
                       help="Skip ESP32 firmware upload")
    
    # FPGA arguments
    parser.add_argument("--fpga-bitstream",
                       help="Path to FPGA bitstream .bin file")
    parser.add_argument("--fpga-protocol",
                       choices=["pesptool", "openfpgaloader", "gowin"],
                       default="pesptool",
                       help="FPGA upload protocol (default: pesptool)")
    parser.add_argument("--fpga-port",
                       help="Serial port for FPGA upload (defaults to esp32-port)")
    parser.add_argument("--fpga-address",
                       default="0x100000",
                       help="Flash address for FPGA bitstream (default: 0x100000)")
    parser.add_argument("--fpga-board",
                       default="tangnano9k",
                       help="Board type for openFPGALoader (default: tangnano9k)")
    parser.add_argument("--fpga-device",
                       default="GW5A-25A",
                       help="Device type for Gowin Programmer (default: GW5A-25A)")
    parser.add_argument("--skip-fpga",
                       action="store_true",
                       help="Skip FPGA bitstream upload")
    
    args = parser.parse_args()
    
    # Set FPGA port to ESP32 port if not specified
    if not args.fpga_port:
        args.fpga_port = args.esp32_port
    
    try:
        # Upload ESP32 firmware
        if not args.skip_esp32:
            if not args.esp32_firmware:
                print("Error: --esp32-firmware is required unless --skip-esp32 is set")
                return 1
            upload_esp32_firmware(args.esp32_firmware, args.esp32_port, args.esp32_baud)
        else:
            print("\n⊘ Skipping ESP32 firmware upload (--skip-esp32)")
        
        # Upload FPGA bitstream
        if not args.skip_fpga:
            if not args.fpga_bitstream:
                print("Error: --fpga-bitstream is required unless --skip-fpga is set")
                return 1
            
            if args.fpga_protocol == "pesptool":
                upload_fpga_pesptool(args.fpga_bitstream, args.fpga_port, args.fpga_address)
            elif args.fpga_protocol == "openfpgaloader":
                upload_fpga_openfpgaloader(args.fpga_bitstream, args.fpga_board)
            elif args.fpga_protocol == "gowin":
                upload_fpga_gowin_programmer(args.fpga_bitstream, args.fpga_device)
        else:
            print("\n⊘ Skipping FPGA bitstream upload (--skip-fpga)")
        
        # Success
        print("\n" + "=" * 70)
        print("✓ Upload Complete!")
        print("=" * 70)
        return 0
        
    except Exception as e:
        print(f"\n✗ Upload failed: {e}", file=sys.stderr)
        print("=" * 70)
        return 1

if __name__ == "__main__":
    sys.exit(main())
