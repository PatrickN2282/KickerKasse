#!/usr/bin/env python3
"""
Systemd installer for the Kickerkasse hardware agent.
Designed for common systemd-based Linux distributions.

Änderungen (siehe Roadmap-UX-Sicherheit.md, Punkt 8 "Hardware-Service Installationsskript"):
  - Prüft die vorhandene Python-Version gegen die dokumentierte Mindestanforderung (README_installer.txt: 3.9+).
  - Legt eine isolierte virtuelle Umgebung an und installiert fehlende Laufzeit-Abhängigkeiten
    (flask, pyserial) automatisch, statt eine manuelle Vorbereitung des Systems vorauszusetzen.
  - Strukturiertes Logging in eine Logdatei zusätzlich zur Konsolenausgabe.
  - Klare, für Vereinsmitglieder ohne IT-Hintergrund verständliche Statusmeldungen je Schritt.
  - Sauberes Fehlerhandling: jeder Schritt liefert eine konkrete, umsetzbare Fehlermeldung statt
    eines rohen Tracebacks.
"""
from __future__ import annotations

import logging
import os
import glob
import secrets
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

MIN_PYTHON_VERSION = (3, 9)
SERVICE_NAME = "kickerkasse-agent"
SERVICE_UNIT_PATH = Path("/etc/systemd/system") / f"{SERVICE_NAME}.service"
SERVICE_ENV_PATH = Path("/etc/default") / SERVICE_NAME
TARGET_DIR = Path("/usr/local/lib") / SERVICE_NAME
TARGET_AGENT_PATH = TARGET_DIR / "agent.py"
TARGET_VENV_DIR = TARGET_DIR / "venv"
TARGET_VENV_PYTHON = TARGET_VENV_DIR / "bin" / "python3"
SOURCE_AGENT_PATH = Path(__file__).resolve().parent / "agent.py"
LOG_PATH = Path("/var/log") / f"{SERVICE_NAME}-install.log"
# Laufzeit-Abhängigkeiten von agent.py (siehe dortige import-Anweisungen).
REQUIRED_PACKAGES = ["flask", "pyserial"]


def _setup_logging() -> logging.Logger:
    logger = logging.getLogger("kickerkasse-install")
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(LOG_PATH, mode="a", encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except OSError:
        # Kein Schreibzugriff auf /var/log – Installation läuft trotzdem weiter,
        # nur ohne persistentes Installationsprotokoll.
        logger.warning("Konnte Installationsprotokoll nicht unter %s anlegen (keine Schreibrechte).", LOG_PATH)

    return logger


log = _setup_logging()


class InstallError(Exception):
    """Fehlerfall mit einer für Endanwender verständlichen Meldung."""


def _run(*args: str, **kwargs) -> subprocess.CompletedProcess:
    log.info("Führe aus: %s", " ".join(args))
    return subprocess.run(args, check=True, **kwargs)


def _step(message: str) -> None:
    log.info("→ %s", message)


def _ensure_root() -> None:
    _step("Prüfe Administratorrechte...")
    if os.geteuid() != 0:
        raise InstallError(
            "Dieses Skript benötigt Root-Rechte. Bitte erneut mit 'sudo python3 install_agent_service.py' ausführen."
        )
    log.info("Root-Rechte vorhanden.")


def _ensure_python_version() -> None:
    _step("Prüfe installierte Python-Version...")
    current = sys.version_info[:2]
    if current < MIN_PYTHON_VERSION:
        raise InstallError(
            f"Python {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]} oder neuer wird benötigt, "
            f"gefunden wurde Python {current[0]}.{current[1]}. Bitte Python aktualisieren "
            "(z. B. 'sudo dnf install python3' bzw. 'sudo apt install python3') und erneut ausführen."
        )
    log.info("Python %s.%s gefunden (Mindestanforderung erfüllt).", current[0], current[1])


def _ensure_system_requirements() -> None:
    _step("Prüfe Systemvoraussetzungen (systemd, agent.py)...")
    if shutil.which("systemctl") is None:
        raise InstallError(
            "Der Befehl 'systemctl' wurde nicht gefunden. Dieses Skript benötigt ein "
            "systemd-basiertes Linux (z. B. Fedora, Nobara, Debian, Ubuntu)."
        )
    if not SOURCE_AGENT_PATH.exists():
        raise InstallError(f"agent.py wurde nicht gefunden: {SOURCE_AGENT_PATH}")
    log.info("Systemvoraussetzungen erfüllt.")


def _ensure_venv_module() -> None:
    try:
        import venv  # noqa: F401
    except ImportError as exc:
        raise InstallError(
            "Das Python-Modul 'venv' fehlt. Bitte auf Debian/Ubuntu 'sudo apt install python3-venv' "
            "nachinstallieren und das Skript erneut ausführen."
        ) from exc


def _create_virtualenv() -> None:
    _step("Lege isolierte Python-Umgebung für den Hardware-Agent an...")
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    if not TARGET_VENV_PYTHON.exists():
        try:
            _run(sys.executable, "-m", "venv", str(TARGET_VENV_DIR))
        except subprocess.CalledProcessError as exc:
            raise InstallError(
                "Die virtuelle Python-Umgebung konnte nicht angelegt werden. Prüfen Sie, ob genug "
                "Speicherplatz verfügbar ist und ob 'python3-venv' installiert ist."
            ) from exc
    else:
        log.info("Virtuelle Umgebung existiert bereits, wird wiederverwendet.")


def _install_dependencies() -> None:
    _step(f"Installiere/prüfe benötigte Python-Pakete: {', '.join(REQUIRED_PACKAGES)}...")
    try:
        _run(str(TARGET_VENV_PYTHON), "-m", "pip", "install", "--quiet", "--upgrade", "pip")
        _run(str(TARGET_VENV_PYTHON), "-m", "pip", "install", "--quiet", *REQUIRED_PACKAGES)
    except subprocess.CalledProcessError as exc:
        raise InstallError(
            "Die benötigten Python-Pakete (flask, pyserial) konnten nicht installiert werden. "
            "Prüfen Sie die Internetverbindung des Kassen-PCs und versuchen Sie es erneut."
        ) from exc
    log.info("Alle benötigten Pakete sind installiert.")


def _build_service_unit() -> str:
    return f"""[Unit]
Description=Kickerkasse Hardware Agent
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
EnvironmentFile=-{SERVICE_ENV_PATH}
ExecStart={TARGET_VENV_PYTHON} {TARGET_AGENT_PATH}
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


def _discover_adapter_paths() -> list[str]:
    candidates = (
        sorted(glob.glob('/dev/serial/by-id/*'))
        + sorted(glob.glob('/dev/serial/by-path/*'))
        + sorted(glob.glob('/dev/ttyUSB*'))
        + sorted(glob.glob('/dev/ttyACM*'))
    )
    result = []
    seen = set()
    for candidate in candidates:
        resolved = os.path.realpath(candidate)
        if resolved in seen:
            continue
        seen.add(resolved)
        result.append(candidate)
    return result


def _ensure_service_environment() -> str:
    """Preserve mappings, ensure a local configuration token and return that token."""
    if SERVICE_ENV_PATH.exists():
        existing = SERVICE_ENV_PATH.read_text(encoding="utf-8")
        lines = existing.splitlines()
        token_prefix = "KICKERKASSE_AGENT_CONFIG_TOKEN="
        token = next(
            (
                line.strip()[len(token_prefix):]
                for line in existing.splitlines()
                if line.strip().startswith(token_prefix)
            ),
            "",
        )
        if not token:
            token = secrets.token_urlsafe(24)
            lines.append(f"{token_prefix}{token}")
        install_origin = (os.environ.get("KICKERKASSE_INSTALL_ALLOWED_ORIGIN") or "").strip()
        parsed_origin = urlparse(install_origin)
        if parsed_origin.scheme not in {"http", "https"} or not parsed_origin.netloc:
            install_origin = ""
        origin_prefix = "KICKERKASSE_AGENT_ALLOWED_ORIGINS="
        if install_origin:
            origin_index = next(
                (index for index, line in enumerate(lines) if line.strip().startswith(origin_prefix)),
                None,
            )
            existing_origins = set()
            if origin_index is not None:
                existing_origins.update(
                    origin.strip()
                    for origin in lines[origin_index].strip()[len(origin_prefix):].split(",")
                    if origin.strip()
                )
            existing_origins.add(install_origin)
            origin_line = f"{origin_prefix}{','.join(sorted(existing_origins))}"
            if origin_index is None:
                lines.append(origin_line)
            else:
                lines[origin_index] = origin_line
        SERVICE_ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
        os.chmod(SERVICE_ENV_PATH, 0o600)
        log.info("Adapterkonfiguration bleibt erhalten: %s", SERVICE_ENV_PATH)
        return token

    adapters = _discover_adapter_paths()
    lines = [
        "# Kickerkasse USB-Adapterzuordnung",
        "# Bevorzugt stabile Pfade aus /dev/serial/by-id verwenden.",
        "# Änderungen über den Adminbereich werden sofort aktiviert.",
    ]
    if adapters:
        lines.append(f"KICKERKASSE_MAIN_DRAWER_DEVICE={adapters[0]}")
    else:
        lines.append("# KICKERKASSE_MAIN_DRAWER_DEVICE=/dev/serial/by-id/...")
    if len(adapters) > 1:
        lines.append(f"KICKERKASSE_SMALL_PARTS_DRAWER_DEVICE={adapters[1]}")
    else:
        lines.append("# KICKERKASSE_SMALL_PARTS_DRAWER_DEVICE=/dev/serial/by-id/...")
    token = secrets.token_urlsafe(24)
    lines.append(f"KICKERKASSE_AGENT_CONFIG_TOKEN={token}")
    install_origin = (os.environ.get("KICKERKASSE_INSTALL_ALLOWED_ORIGIN") or "").strip()
    parsed_origin = urlparse(install_origin)
    if install_origin and parsed_origin.scheme in {"http", "https"} and parsed_origin.netloc:
        lines.append(f"KICKERKASSE_AGENT_ALLOWED_ORIGINS={install_origin}")
    SERVICE_ENV_PATH.parent.mkdir(parents=True, exist_ok=True)
    SERVICE_ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.chmod(SERVICE_ENV_PATH, 0o600)
    log.info("Adapterkonfiguration geschrieben: %s", SERVICE_ENV_PATH)
    return token


def _install_service_files() -> str:
    _step("Kopiere Agent-Dateien und richte den Systemdienst ein...")
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE_AGENT_PATH, TARGET_AGENT_PATH)
    os.chmod(TARGET_AGENT_PATH, 0o755)
    config_token = _ensure_service_environment()
    SERVICE_UNIT_PATH.write_text(_build_service_unit(), encoding="utf-8")
    log.info("Dienstdatei geschrieben: %s", SERVICE_UNIT_PATH)
    return config_token


def _enable_and_start_service() -> None:
    _step("Aktiviere und starte den Kickerkasse-Hardware-Dienst...")
    try:
        _run("systemctl", "daemon-reload")
        _run("systemctl", "enable", f"{SERVICE_NAME}.service")
        _run("systemctl", "restart", f"{SERVICE_NAME}.service")
    except subprocess.CalledProcessError as exc:
        raise InstallError(
            "Der Systemdienst konnte nicht gestartet werden. Führen Sie "
            f"'systemctl status {SERVICE_NAME}.service' aus, um Details zu sehen."
        ) from exc


def install() -> str:
    """Führt die Installation Schritt für Schritt aus.

    Jeder Schritt ist einzeln fehlerbehandelt, damit fehlende Voraussetzungen automatisch
    behoben werden (z. B. fehlende Python-Pakete) und Fehlerfälle sauber mit einer konkreten,
    verständlichen Meldung statt eines rohen Tracebacks beendet werden.
    """
    _step("Starte Installation des Kickerkasse Hardware-Agents...")
    _ensure_root()
    _ensure_python_version()
    _ensure_system_requirements()
    _ensure_venv_module()
    _create_virtualenv()
    _install_dependencies()
    config_token = _install_service_files()
    _enable_and_start_service()
    return config_token


if __name__ == "__main__":
    try:
        config_token = install()
        log.info("✅ Kickerkasse Hardware-Agent wurde erfolgreich installiert und gestartet.")
        print("\nInstallation abgeschlossen. Status prüfen mit:")
        print(f"  systemctl status {SERVICE_NAME}")
        print("\nLokaler Konfigurationscode für Admin → Einstellungen → Erweitert:")
        print(f"  {config_token}")
        print("Der Code bleibt auf diesem Kassen-PC gespeichert und darf nicht weitergegeben werden.")
    except InstallError as exc:
        log.error("❌ Installation fehlgeschlagen: %s", exc)
        print(f"\n❌ Installation fehlgeschlagen: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001 - letzte Sicherheitsnetz für unerwartete Fehler
        log.exception("❌ Unerwarteter Fehler während der Installation")
        print(f"\n❌ Unerwarteter Fehler: {exc}", file=sys.stderr)
        print(f"Details siehe Installationsprotokoll: {LOG_PATH}", file=sys.stderr)
        sys.exit(1)
