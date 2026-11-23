"""PlatformIO configuration shared by FPGA and ESP application uploads."""

import subprocess
import sys
from pathlib import Path


def configure_upload(env, device, uploader_dir):
    def enabled(env, option):
        value = env.GetProjectOption(option, "no")
        if value not in ("yes", "no"):
            raise ValueError(f"{option} must be yes or no")
        return value == "yes"

    def upload(source, target, env):
        protocol = env.GetProjectOption("upload_protocol", "")
        transport = (
            env.GetProjectOption("custom_papilio_transport", "serial")
            if protocol == "custom" else
            {"papilio_serial": "serial", "papilio_ota": "ota"}[protocol]
        )
        if transport not in ("serial", "ota"):
            raise ValueError("custom_papilio_transport must be serial or ota")
        managed_tool = env.PioPlatform().get_package_dir("tool-esptoolpy")
        if not managed_tool:
            raise RuntimeError("PlatformIO tool-esptoolpy is not installed")
        command = [
            env.subst("$PYTHONEXE") or sys.executable,
            str(Path(uploader_dir) / "papilio_upload.py"),
            "--device", device, "--transport", transport,
            "--file", str(source[0]),
            "--esptool", str(Path(managed_tool) / "esptool.py"),
            "--backup-dir", str(Path(env.subst("$BUILD_DIR")) / "papilio-backups"),
        ]
        port = env.GetProjectOption("custom_papilio_usb_port", "") or env.get(
            "UPLOAD_PORT", ""
        ) or env.GetProjectOption("upload_port", "")
        if port:
            command.extend(["--port", port])
        if transport == "ota":
            host = env.GetProjectOption("custom_papilio_host", "")
            if not host:
                raise ValueError("papilio_ota requires custom_papilio_host")
            command.extend([
                "--host", host, "--http-port",
                str(env.GetProjectOption("custom_papilio_http_port", "3232")),
            ])
            if enabled(env, "custom_papilio_enter_via_usb"):
                command.append("--enter-via-usb")
        if enabled(env, "custom_papilio_stay_in_loader"):
            command.append("--stay-in-loader")
        return subprocess.call(command)

    env.Replace(UPLOADCMD=upload)
    return upload
