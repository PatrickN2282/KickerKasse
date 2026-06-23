#!/usr/bin/env python3
"""
Systemd installer for the Kickerkasse hardware agent.
Designed for common systemd-based Linux distributions.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


SERVICE_NAME = "kickerkasse-agent"
SERVICE_UNIT_PATH = Path("/etc/systemd/system") / f"{SERVICE_NAME}.service"
TARGET_DIR = Path("/usr/local/lib") / SERVICE_NAME
TARGET_AGENT_PATH = TARGET_DIR / "agent.py"
SOURCE_AGENT_PATH = Path(__file__).resolve().parent / "agent.py"
PYTHON_EXECUTABLE = Path(sys.executable)


def _run(*args: str) -> None:
    subprocess.run(args, check=True)


def _ensure_root() -> None:
    if os.geteuid() != 0:
        raise PermissionError("Dieses Skript benötigt Root-Rechte. Bitte mit sudo ausführen.")


def _ensure_requirements() -> None:
    if shutil.which("systemctl") is None:
        raise RuntimeError("systemctl wurde nicht gefunden. Dieses Skript benötigt ein systemd-basiertes System.")
    if not SOURCE_AGENT_PATH.exists():
        raise FileNotFoundError(f"agent.py wurde nicht gefunden: {SOURCE_AGENT_PATH}")


def _build_service_unit() -> str:
    return f"""[Unit]
Description=Kickerkasse Hardware Agent
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart={PYTHON_EXECUTABLE} {TARGET_AGENT_PATH}
Restart=on-failure
RestartSec=2
User=root
Group=root
WorkingDirectory={TARGET_DIR}
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
"""


def install() -> None:
    _ensure_root()
    _ensure_requirements()

    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE_AGENT_PATH, TARGET_AGENT_PATH)
    os.chmod(TARGET_AGENT_PATH, 0o755)

    SERVICE_UNIT_PATH.write_text(_build_service_unit(), encoding="utf-8")

    _run("systemctl", "daemon-reload")
    _run("systemctl", "enable", f"{SERVICE_NAME}.service")
    _run("systemctl", "restart", f"{SERVICE_NAME}.service")


if __name__ == "__main__":
    try:
        install()
        print("✅ Kickerkasse Hardware-Agent wurde installiert und gestartet.")
    except Exception as exc:
        print(f"❌ Installation fehlgeschlagen: {exc}", file=sys.stderr)
        sys.exit(1)
