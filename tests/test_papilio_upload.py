import hashlib
import json
import runpy
import struct
import tempfile
import unittest
from collections import deque
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
uploader = runpy.run_path(str(ROOT / "builder" / "papilio_upload.py"))
UploadError = uploader["UploadError"]
Console = uploader["Console"]


class FakeSerial:
    def __init__(self, lines):
        self.lines = deque(lines)
        self.sent = bytearray()

    def read_until(self, _):
        return self.lines.popleft() if self.lines else b""

    def write(self, data):
        size = min(1024, len(data))
        self.sent.extend(data[:size])
        return size

    def flush(self):
        pass

    def open(self):
        pass

    def close(self):
        pass


def table():
    data = b"".join(
        struct.pack("<HBBII16sI", 0x50AA, *entry, name.encode(), 0)
        for name, entry in uploader["LAYOUT"].items()
    )
    return data + b"\xeb\xeb" + b"\xff" * 14 + hashlib.md5(data).digest()


class UploadTests(unittest.TestCase):
    def test_layout_checksum_and_changed_factory_are_rejected(self):
        validate = uploader["validate_layout"]
        valid = table()
        validate(valid)
        with self.assertRaisesRegex(UploadError, "checksum mismatch"):
            validate(valid[:-1] + bytes([valid[-1] ^ 1]))
        changed = bytearray(valid)
        changed[3 * 32 + 4] ^= 1
        with self.assertRaisesRegex(UploadError, "Unsupported partition"):
            validate(bytes(changed))

    def test_factory_identity_required(self):
        data = bytearray(512)
        data[0] = 0xE9
        struct.pack_into("<I", data, 32, 0xABCD5432)
        data[80:102] = b"papilio_esp_bootloader\0"
        uploader["validate_factory"](bytes(data))
        data[80] = ord("x")
        with self.assertRaisesRegex(UploadError, "not the Papilio"):
            uploader["validate_factory"](bytes(data))

    def test_application_preflight_rejects_merged_and_wrong_chip_images(self):
        data = bytearray(0x9000)
        data[0] = 0xE9
        struct.pack_into("<H", data, 12, 9)
        struct.pack_into("<I", data, 32, 0xABCD5432)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "firmware.bin"
            path.write_bytes(data)
            self.assertEqual(uploader["validate_image"](path, "esp32"), bytes(data))
            data[0x8000:0x8002] = b"\xaa\x50"
            path.write_bytes(data)
            with self.assertRaisesRegex(UploadError, "Merged firmware"):
                uploader["validate_image"](path, "esp32")
            path.write_bytes(b"\xe9")
            with self.assertRaisesRegex(UploadError, "raw ESP32 application"):
                uploader["validate_image"](path, "esp32")

    def test_console_handles_partial_lines_and_partial_writes(self):
        with patch.object(uploader["serial"], "Serial",
                          return_value=FakeSerial([b"PROGRESS 40", b"96\r\n"])):
            console = Console("test")
        console.write(b"a" * 4096)
        self.assertEqual(console.port.sent, b"a" * 4096)
        self.assertEqual(
            console.wait(lambda line: line == "PROGRESS 4096", 1, "ack"),
            "PROGRESS 4096",
        )

    def test_error_while_waiting_for_ack_is_not_success(self):
        with patch.object(uploader["serial"], "Serial",
                          return_value=FakeSerial([b"FPGA_FLASH_ERROR timeout\r\n"])):
            console = Console("test")
        with self.assertRaisesRegex(UploadError, "Board reported"):
            console.wait(lambda line: line == "PROGRESS 4096", 1, "ack")

    def test_disconnect_and_missing_completion_fail(self):
        fake = FakeSerial([])
        with patch.object(uploader["serial"], "Serial", return_value=fake):
            console = Console("test")
        with self.assertRaisesRegex(UploadError, "unconfirmed"):
            console.wait(lambda _: False, 0, "FPGA_FLASH_OK")
        with patch.object(fake, "read_until",
                          side_effect=uploader["serial"].SerialException("disconnected")):
            with self.assertRaises(uploader["serial"].SerialException):
                console.wait(lambda _: False, 1, "FPGA_FLASH_OK")

    def test_serial_fpga_chunks_and_explicit_completion(self):
        fake = FakeSerial([
            b"alive -- running from 'factory'\n", b"READY\n",
            b"PROGRESS 4096\n", b"PROGRESS 5000\n", b"FPGA_FLASH_OK\n",
        ])
        with patch.object(uploader["serial"], "Serial", return_value=fake):
            uploader["upload_serial"]("test", b"x" * 5000, "fpga", False)
        self.assertEqual(fake.sent, b"FPGA_FLASH_BEGIN flash 5000\n" + b"x" * 5000)

    def test_multiple_boards_do_not_auto_select_first(self):
        ports = [
            SimpleNamespace(vid=0x303A, pid=0x1001, device=f"COM{i}",
                            description="Interface 0", location="")
            for i in (10, 12)
        ]
        with patch.object(uploader["list_ports"], "comports", return_value=ports):
            with self.assertRaisesRegex(UploadError, "unambiguous"):
                uploader["resolve_port"](None)

    def test_unsupported_recovery_never_erases_metadata(self):
        recovery = uploader["enter_loader"]
        fake = FakeSerial([])
        calls = []

        def run(tool, port, before, after, *args):
            calls.append(args[0])
            Path(args[-1]).write_bytes(b"\xff" * 4096)

        with tempfile.TemporaryDirectory() as directory:
            tool = Path(directory) / "esptool.py"
            tool.touch()
            with patch.object(uploader["serial"], "Serial", return_value=fake), \
                 patch.object(Console, "wait", side_effect=uploader["UploadTimeout"]("absent")), \
                 patch.dict(recovery.__globals__, {"run_esptool": run}):
                with self.assertRaisesRegex(UploadError, "Unsupported partition"):
                    recovery("test", tool, Path(directory))
        self.assertEqual(calls, ["read_flash"])

    def test_http_unknown_role_prevents_write(self):
        upload = uploader["upload_http"]
        calls = []

        def request(base, route, data=None):
            calls.append(route)
            return "Unknown firmware"

        with patch.dict(upload.__globals__, {"http_request": request}):
            with self.assertRaisesRegex(UploadError, "Unknown network firmware"):
                upload("board", 3232, b"image", "fpga", True)
        self.assertEqual(calls, ["/"])

    def test_http_app_target_precedes_upload_and_response_is_checked(self):
        upload = uploader["upload_http"]
        calls = []

        def request(base, route, data=None):
            calls.append((route, data))
            return {"/": "Papilio ESP Bootloader", "/update-target": "ota_1",
                    "/update": "unexpected"}[route]

        with patch.dict(upload.__globals__, {"http_request": request}):
            with self.assertRaisesRegex(UploadError, "Unexpected upload response"):
                upload("board", 3232, b"image", "esp32", False)
        self.assertEqual(calls, [("/", None), ("/update-target", None), ("/update", b"image")])

    def test_both_platformio_environments_use_shared_uploader(self):
        configure = runpy.run_path(str(ROOT / "builder" / "papilio_upload_hook.py"))[
            "configure_upload"
        ]
        commands = []

        class Env:
            def get(self, name, default):
                return default

            def GetProjectOption(self, name, default):
                return {"upload_protocol": "custom", "upload_port": "COM10"}.get(name, default)

            def PioPlatform(self):
                return SimpleNamespace(get_package_dir=lambda _: "managed tool")

            def subst(self, value):
                return {"$PYTHONEXE": "python", "$BUILD_DIR": "build dir"}[value]

            def Replace(self, **kwargs):
                self.action = kwargs["UPLOADCMD"]

        env = Env()
        with patch.object(configure.__globals__["subprocess"], "call",
                          side_effect=lambda command: commands.append(command) or 0):
            action = configure(env, "esp32", ROOT / "builder")
            self.assertEqual(action(["firmware.bin"], [], env), 0)
        self.assertIn("--device", commands[0])
        self.assertIn("esp32", commands[0])
        self.assertIn("COM10", commands[0])
        self.assertIn(str(ROOT / "builder" / "papilio_upload.py"), commands[0])
        manifest = json.loads((ROOT / "package.json").read_text())
        self.assertEqual(manifest["name"], "tool-papilio-upload")


if __name__ == "__main__":
    unittest.main()
