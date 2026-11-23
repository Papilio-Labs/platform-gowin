"""Direct uploads to the on-board Papilio ESP bootloader."""

import argparse
import hashlib
import struct
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable, Optional
from uuid import uuid4

import serial
from serial.tools import list_ports


class UploadError(RuntimeError):
    pass


class UploadTimeout(UploadError):
    pass


LAYOUT = {
    "nvs_loader": (1, 2, 0x9000, 0x3000),
    "otadata": (1, 0, 0xC000, 0x2000),
    "nvs": (1, 2, 0xE000, 0x6000),
    "factory": (0, 0, 0x20000, 0xE0000),
    "ota_0": (0, 0x10, 0x100000, 0x180000),
    "ota_1": (0, 0x11, 0x280000, 0x180000),
}


def validate_image(path: Path, device: str) -> bytes:
    data = path.read_bytes()
    limit = 0x200000 if device == "fpga" else 0x180000
    if not data or len(data) > limit:
        raise UploadError(f"{device} image must contain 1..{limit} bytes")
    if device == "esp32" and (
        len(data) < 112 or data[0] != 0xE9
        or struct.unpack_from("<H", data, 12)[0] != 9
        or struct.unpack_from("<I", data, 32)[0] != 0xABCD5432
    ):
        raise UploadError("Expected a raw ESP32 application image, not a merged image")
    if device == "esp32" and len(data) >= 0x9000 and data[0x8000:0x8002] == b"\xaa\x50":
        raise UploadError("Merged firmware is not allowed for normal application uploads")
    return data


def validate_layout(data: bytes) -> None:
    entries = {}
    end = 0
    for offset in range(0, len(data) - 31, 32):
        magic, kind, subtype, address, size, label, _ = struct.unpack_from(
            "<HBBII16sI", data, offset
        )
        if magic != 0x50AA:
            end = offset
            break
        name = label.split(b"\0", 1)[0].decode("ascii")
        if name in entries:
            raise UploadError("Duplicate partition label")
        entries[name] = (kind, subtype, address, size)
    if entries != LAYOUT:
        raise UploadError("Unsupported partition table; refusing to clear OTA selection")
    if data[end:end + 16] != b"\xeb\xeb" + b"\xff" * 14:
        raise UploadError("Partition-table checksum record missing")
    if hashlib.md5(data[:end]).digest() != data[end + 16:end + 32]:
        raise UploadError("Partition-table checksum mismatch")


def validate_factory(data: bytes) -> None:
    if len(data) < 112 or data[0] != 0xE9:
        raise UploadError("Factory image header is invalid")
    if struct.unpack_from("<I", data, 32)[0] != 0xABCD5432:
        raise UploadError("Factory application descriptor is missing")
    if data[80:112].split(b"\0", 1)[0] != b"papilio_esp_bootloader":
        raise UploadError("Factory is not the Papilio ESP bootloader")


def resolve_port(requested: Optional[str]) -> str:
    if requested:
        return requested
    ports = [
        p for p in list_ports.comports()
        if p.vid == 0x303A and p.pid == 0x1001
    ]
    console = [
        p for p in ports
        if "Interface 0" in (p.description or "") or (p.location or "").endswith(".0")
    ]
    candidates = console or ports
    if len(candidates) != 1:
        raise UploadError("Specify upload_port: no unambiguous Papilio console port found")
    return candidates[0].device


class Console:
    def __init__(self, port: str):
        self.port = serial.Serial()
        self.port.port = port
        self.port.baudrate = 115200
        self.port.timeout = 0.2
        self.port.write_timeout = 15
        self.port.dtr = False
        self.port.rts = False
        self.pending = bytearray()

    def __enter__(self):
        self.port.open()
        return self

    def __exit__(self, *_):
        self.port.close()

    def write(self, data: bytes) -> None:
        offset = 0
        while offset < len(data):
            written = self.port.write(data[offset:])
            if not written:
                raise UploadError("Serial write made no progress")
            offset += written
        self.port.flush()

    def wait(self, predicate: Callable[[str], bool], timeout: float, description: str) -> str:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            self.pending.extend(self.port.read_until(b"\n"))
            while b"\n" in self.pending:
                raw, _, rest = self.pending.partition(b"\n")
                self.pending = bytearray(rest)
                line = raw.decode("utf-8", errors="replace").strip()
                if not line:
                    continue
                if any(marker in line for marker in (
                    "FPGA_FLASH_ERROR", "APP_FLASH_ERROR", "RESUME_ERROR",
                    "Guru Meditation", "abort()",
                )):
                    raise UploadError(f"Board reported: {line}")
                if not line.startswith("PROGRESS "):
                    print(line, flush=True)
                if predicate(line):
                    return line
        raise UploadTimeout(f"Timed out waiting for {description}; result is unconfirmed")


def is_loader(line: str) -> bool:
    return ("Papilio ESP Bootloader" in line or
            "alive -- running from 'factory'" in line)


def run_esptool(tool: Path, port: str, before: str, after: str, *args: str) -> None:
    command = [
        sys.executable, str(tool), "--port", port, "--chip", "esp32s3",
        "--before", before, "--after", after, *args,
    ]
    result = subprocess.run(command, timeout=120, check=False)
    if result.returncode:
        raise UploadError(
            "USB ROM recovery failed. Release other serial monitors and try again; "
            "if the port remains unresponsive, press RESET or hold BOOT while reconnecting."
        )


def enter_loader(port: str, tool: Path, backup_dir: Path) -> None:
    with Console(port) as console:
        try:
            console.wait(is_loader, 3, "live factory-loader identity")
            return
        except UploadTimeout:
            print("Loader not confirmed; attempting verified USB factory recovery.", flush=True)
    if not tool.is_file():
        raise UploadError("Managed tool-esptoolpy is missing")
    with tempfile.TemporaryDirectory(prefix="papilio-entry-") as temporary:
        root = Path(temporary)
        table = root / "partitions.bin"
        header = root / "factory-header.bin"
        run_esptool(tool, port, "usb_reset", "no_reset",
                    "read_flash", "0x8000", "0x1000", str(table))
        validate_layout(table.read_bytes())
        run_esptool(tool, port, "no_reset", "no_reset",
                    "read_flash", "0x20000", "0x200", str(header))
        validate_factory(header.read_bytes())
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup = backup_dir / f"otadata-{uuid4().hex}.bin"
        run_esptool(tool, port, "no_reset", "no_reset",
                    "read_flash", "0xc000", "0x2000", str(backup))
        if backup.stat().st_size != 0x2000:
            raise UploadError("OTA selection backup is incomplete")
        print(f"OTA selection backup: {backup}", flush=True)
        print("Clearing OTA selection/rollback records only; factory and app images stay intact.",
              flush=True)
        run_esptool(tool, port, "no_reset", "watchdog_reset",
                    "erase_region", "0xc000", "0x2000")
    deadline = time.monotonic() + 15
    while port not in [p.device for p in list_ports.comports()]:
        if time.monotonic() >= deadline:
            raise UploadError("Board did not reconnect on its console port")
        time.sleep(0.2)
    with Console(port) as console:
        console.wait(is_loader, 15, "live factory-loader identity after recovery")


def wait_app(console: Console) -> None:
    console.wait(
        lambda line: any(
            f"Loaded app from partition at offset {offset}" in line
            for offset in ("0x100000", "0x280000")
        ), 20, "OTA application boot",
    )


def upload_serial(port: str, data: bytes, device: str, resume: bool) -> None:
    with Console(port) as console:
        console.wait(is_loader, 15, "factory-loader identity")
        command = (f"FPGA_FLASH_BEGIN flash {len(data)}\n" if device == "fpga"
                   else f"APP_FLASH_BEGIN {len(data)}\n")
        console.write(command.encode("ascii"))
        console.wait(lambda line: line == "READY", 15, "READY")
        start = time.monotonic()
        for offset in range(0, len(data), 4096):
            end = min(offset + 4096, len(data))
            console.write(data[offset:end])
            console.wait(lambda line: line == f"PROGRESS {end}",
                         120 if offset == 0 else 20, f"PROGRESS {end}")
            if end % 65536 == 0 or end == len(data):
                print(f"Uploaded {end}/{len(data)} bytes", flush=True)
        done = "FPGA_FLASH_OK" if device == "fpga" else "APP_FLASH_OK"
        console.wait(lambda line: line == done, 30, done)
        print(f"Upload acknowledged in {time.monotonic() - start:.2f}s", flush=True)
        if device == "esp32":
            wait_app(console)
        elif resume:
            console.write(b"RESUME_APP\n")
            console.wait(lambda line: line == "RESUME_OK", 15, "RESUME_OK")
            wait_app(console)


def http_request(base: str, route: str, data: Optional[bytes] = None) -> str:
    request = urllib.request.Request(
        base + route, data=data,
        headers={"Content-Type": "application/octet-stream"} if data is not None else {},
    )
    try:
        with urllib.request.urlopen(request, timeout=180 if data else 5) as response:
            return response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as error:
        raise UploadError(
            f"HTTP {error.code} at {route}: {error.read().decode('utf-8', errors='replace')}"
        ) from error


def http_base(host: str, port: int) -> str:
    if any(c in host for c in "/\\?#@ \r\n") or not host:
        raise UploadError("Specify a board hostname/IP, without a URL scheme or path")
    if not 1 <= port <= 65535:
        raise UploadError("HTTP port must be in 1..65535")
    return f"http://{host}:{port}"


def upload_http(host: str, port: int, data: bytes, device: str, resume: bool) -> None:
    base = http_base(host, port)
    status = http_request(base, "/")
    if "Papilio ESP Bootloader" not in status:
        if "FPGA Companion" not in status:
            raise UploadError("Unknown network firmware; loader entry cannot be confirmed")
        print(http_request(base, "/goto-loader", b""), flush=True)
        deadline = time.monotonic() + 30
        while True:
            try:
                status = http_request(base, "/")
            except (urllib.error.URLError, TimeoutError) as error:
                print(f"Waiting for loader: {error}", flush=True)
                status = ""
            if "Papilio ESP Bootloader" in status:
                break
            if time.monotonic() >= deadline:
                raise UploadError("Network handoff did not reach the loader")
            time.sleep(1)
    route = "/fpga-update" if device == "fpga" else "/update"
    if device == "esp32":
        print(http_request(base, "/update-target").strip(), flush=True)
    result = http_request(base, route, data)
    expected = "FPGA flash update successful!" if device == "fpga" else "App update successful."
    if expected not in result:
        raise UploadError(f"Unexpected upload response: {result}")
    print(f"Uploaded {len(data)} bytes: {result.strip()}", flush=True)
    if device == "fpga" and resume:
        result = http_request(base, "/resume", b"")
        if not result.startswith("Resuming 'ota_"):
            raise UploadError(f"Unexpected resume response: {result}")
        print(result.strip(), flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--transport", choices=("serial", "ota"), required=True)
    parser.add_argument("--device", choices=("fpga", "esp32"), required=True)
    parser.add_argument("--file", type=Path, required=True)
    parser.add_argument("--port")
    parser.add_argument("--host")
    parser.add_argument("--http-port", type=int, default=3232)
    parser.add_argument("--esptool", type=Path)
    parser.add_argument("--backup-dir", type=Path)
    parser.add_argument("--stay-in-loader", action="store_true")
    parser.add_argument("--enter-via-usb", action="store_true",
                        help="Enter factory over USB before using HTTP")
    args = parser.parse_args()
    try:
        data = validate_image(args.file, args.device)
        if not 1 <= args.http_port <= 65535:
            raise UploadError("HTTP port must be in 1..65535")
        if args.transport == "ota" and not args.host:
            raise UploadError("Network uploads require --host")
        if args.transport == "ota":
            http_base(args.host, args.http_port)
        if args.transport == "serial" or args.enter_via_usb:
            if not args.esptool:
                raise UploadError("USB entry requires a managed --esptool path")
            port = resolve_port(args.port)
            enter_loader(port, args.esptool,
                         args.backup_dir or args.file.parent / "papilio-backups")
        if args.transport == "serial":
            upload_serial(port, data, args.device, not args.stay_in_loader)
        else:
            upload_http(args.host, args.http_port, data, args.device, not args.stay_in_loader)
        return 0
    except (UploadError, OSError, ValueError, serial.SerialException,
            subprocess.TimeoutExpired, urllib.error.URLError) as error:
        print(f"Upload failed: {error}", file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
