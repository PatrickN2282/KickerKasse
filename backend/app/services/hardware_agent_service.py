from __future__ import annotations

import logging
import os
import shutil
import subprocess
from pathlib import Path

import requests

logger = logging.getLogger(__name__)


class HardwareAgentService:
    SERVICE_NAME = "kickerkasse-agent"
    SERVICE_UNIT = f"{SERVICE_NAME}.service"

    # ARCHITEKTUR-HINWEIS:
    # Diese URLs (127.0.0.1) beziehen sich auf den Kassen-PC, NICHT auf diesen Server.
    # Der Server kann den lokalen Agent des Kassen-PCs NICHT direkt erreichen –
    # 127.0.0.1 wäre hier der Homeserver selbst.
    # Die Schubladen-Steuerung muss daher im Browser des Kassen-PCs per fetch()
    # direkt an den lokalen Agent gerichtet werden.
    AGENT_LOCAL_BASE_URL = "http://127.0.0.1:8765"
    AGENT_STATUS_URL = f"{AGENT_LOCAL_BASE_URL}/status"
    AGENT_OPEN_URL = f"{AGENT_LOCAL_BASE_URL}/openDrawer"

    INSTALL_SCRIPT_PATH = Path(__file__).resolve().parents[2] / "services" / "install_agent_service.py"

    @staticmethod
    def _is_systemd_available() -> bool:
        return shutil.which("systemctl") is not None

    @classmethod
    def _run_systemctl(cls, *args: str) -> tuple[bool, str]:
        if not cls._is_systemd_available():
            return False, "systemctl ist auf diesem System nicht verfügbar"
        try:
            result = subprocess.run(
                ["systemctl", *args],
                check=False,
                capture_output=True,
                text=True,
            )
            output = (result.stdout or result.stderr or "").strip()
            return result.returncode == 0, output
        except Exception:
            logger.exception("systemctl execution failed")
            return False, "systemctl-Aufruf fehlgeschlagen"

    @classmethod
    def get_status(cls) -> dict:
        # Der Server kann den lokalen Agent des Kassen-PCs nicht erreichen.
        # Wir geben dem Frontend die nötigen URLs zurück, damit der Browser
        # des Kassen-PCs den Agent direkt abfragen kann (client_must_query_directly).
        return {
            "service_name": cls.SERVICE_UNIT,
            "agent_local_url": cls.AGENT_LOCAL_BASE_URL,
            "agent_status_url": cls.AGENT_STATUS_URL,
            "agent_open_url": cls.AGENT_OPEN_URL,
            "client_must_query_directly": True,
            "install_script_path": str(cls.INSTALL_SCRIPT_PATH),
            "manual_install_command": f"sudo python3 {cls.INSTALL_SCRIPT_PATH}",
        }

    @classmethod
    def manage_service(cls, action: str) -> tuple[bool, str]:
        allowed_actions = {"start", "stop", "restart", "enable", "disable"}
        normalized = (action or "").strip().lower()
        if normalized not in allowed_actions:
            return False, "Ungültige Service-Aktion"
        return cls._run_systemctl(normalized, cls.SERVICE_UNIT)

    @classmethod
    def run_install_script(cls) -> tuple[bool, str]:
        if os.geteuid() != 0:
            return False, "Installation benötigt Root-Rechte (sudo)"
        if not cls.INSTALL_SCRIPT_PATH.exists():
            return False, "Installationsskript nicht gefunden"
        try:
            result = subprocess.run(
                ["python3", str(cls.INSTALL_SCRIPT_PATH)],
                check=False,
                capture_output=True,
                text=True,
            )
            output = (result.stdout or result.stderr or "").strip()
            return result.returncode == 0, output
        except Exception:
            logger.exception("Failed to execute hardware agent install script")
            return False, "Installationsskript konnte nicht ausgeführt werden"

    @classmethod
    def trigger_drawer_open(cls) -> tuple[bool, str]:
        # WICHTIG: Diese Methode funktioniert nur wenn der Aufruf vom Kassen-PC selbst kommt.
        # Vom Homeserver aus ist 127.0.0.1:8765 nicht erreichbar!
        # Empfehlung: Kassenschublade direkt im Browser-Client per fetch() öffnen,
        # nicht über diesen Server-Endpunkt.
        try:
            response = requests.post(cls.AGENT_OPEN_URL, timeout=2.5)
            payload = {}
            try:
                payload = response.json()
            except Exception:
                payload = {}

            if response.ok:
                return True, payload.get("message") or "Kassenschublade geöffnet"
            return False, payload.get("message") or f"Hardware-Agent antwortete mit Status {response.status_code}"
        except Exception:
            logger.exception("Failed to reach hardware agent drawer endpoint")
            return False, (
                "Hardware-Agent ist nicht erreichbar. "
                "Hinweis: Die Kassenschublade muss direkt vom Browser des Kassen-PCs "
                "angesteuert werden (http://127.0.0.1:8765/openDrawer), "
                "nicht über diesen Server."
            )
