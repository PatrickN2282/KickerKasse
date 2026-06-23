#!/usr/bin/env python3
"""
Kickerkasse Hardware Connector Setup
Selbstinstallierend: Prüft und installiert PySide6 automatisch in lokalem venv.
"""
import sys
import os
import subprocess
import platform
import shutil
import glob

# ═══════════════════════════════════════════════════════════════════════
# AUTO-DEPENDENCY INSTALLER (Phase 1)
# ═══════════════════════════════════════════════════════════════════════
VENV_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".kickerkasse_venv")
REQUIREMENTS = [
    "PySide6>=6.5.0",
    "pyserial>=3.5",
    "Flask>=2.3.0",
    "requests>=2.31.0"
]
DRAWER_PULSE = b'\x1b\x70\x00\x19\xfa'

def ensure_dependencies():
    """Prüft und installiert Abhängigkeiten automatisch in lokalem venv."""
    venv_python = os.path.join(VENV_DIR, "bin", "python3")

    if not os.path.exists(venv_python):
        print("🔧 Erstelle isolierte Python-Umgebung...")
        try:
            subprocess.run([sys.executable, "-m", "venv", VENV_DIR], check=True)
        except subprocess.CalledProcessError:
            print("❌ Fehler: python3-venv nicht installiert.")
            sys.exit(1)

    try:
        subprocess.run([venv_python, "-c", "import PySide6"],
                      check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("📦 Installiere Abhängigkeiten (erster Start, dauert ca. 1-2 Minuten)...")
        pip = os.path.join(VENV_DIR, "bin", "pip")
        subprocess.run([pip, "install", "--upgrade", "pip"], check=True)
        subprocess.run([pip, "install"] + REQUIREMENTS, check=True)
        print("✅ Abhängigkeiten installiert. Starte Setup...")

    if sys.executable != venv_python:
        os.execv(venv_python, [venv_python] + sys.argv)

if sys.executable != os.path.join(VENV_DIR, "bin", "python3"):
    ensure_dependencies()

# ═══════════════════════════════════════════════════════════════════════
# AB HIER: GUI SETUP WIZARD (läuft garantiert mit PySide6)
# ═══════════════════════════════════════════════════════════════════════
from PySide6.QtWidgets import (QApplication, QWizard, QWizardPage, QLabel,
                                 QVBoxLayout, QPushButton, QProgressBar,
                                 QHBoxLayout, QFrame, QMessageBox)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont

STYLE_SHEET = """
    QWizard { background-color: #f5f6f8; }
    QWizardPage { background-color: #ffffff; }
    QLabel { font-family: 'Segoe UI', 'Ubuntu', sans-serif; color: #2c3e50; }
    QPushButton {
        background-color: #34495e; color: white; border: none;
        padding: 8px 18px; font-size: 11pt; border-radius: 4px; min-width: 100px;
    }
    QPushButton:hover { background-color: #415b76; }
    QPushButton:pressed { background-color: #21303f; }
    QPushButton:disabled { background-color: #bdc3c7; color: #7f8c8d; }
    QProgressBar {
        border: 1px solid #bdc3c7; border-radius: 4px;
        text-align: center; background-color: #ecf0f1; height: 22px; font-weight: bold;
    }
    QProgressBar::chunk { background-color: #2ec4b6; width: 10px; }
"""

class InstallationWorker(QThread):
    progress = Signal(int, str)
    finished = Signal(bool, str)

    def run(self):
        try:
            installer_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "install_agent_service.py")
            self.progress.emit(20, "Prüfe systemd und Installationsdateien...")
            if not os.path.exists(installer_script):
                raise RuntimeError("Installationsskript install_agent_service.py wurde nicht gefunden.")
            self.progress.emit(60, "Installiere Hardware-Agent als systemd-Dienst...")
            subprocess.run([sys.executable, installer_script], check=True)
            self.progress.emit(90, "Verifiziere Service-Status...")
            subprocess.run(["systemctl", "is-active", "--quiet", "kickerkasse-agent.service"], check=True)
            self.progress.emit(100, "Installation abgeschlossen.")
            self.finished.emit(True, "Erfolgreich installiert.")
        except Exception as e:
            self.finished.emit(False, str(e))

class HardwareTestWorker(QThread):
    result = Signal(bool, str)

    def run(self):
        ports = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')
        if not ports:
            self.result.emit(False, "Keine USB-Seriell Hardware (/dev/ttyUSB*) gefunden.")
            return
        port = ports[0]
        try:
            import serial
            ser = serial.Serial(port, 9600, timeout=1)
            ser.write(DRAWER_PULSE)
            ser.flush()
            ser.close()
            self.result.emit(True, f"Hardware an {port} reagiert (Impuls gesendet).")
        except Exception as e:
            self.result.emit(False, f"Fehler beim Zugriff auf {port}: {str(e)}")

class WelcomePage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Willkommen")
        layout = QVBoxLayout()
        title_label = QLabel("Kickerkasse Hardware Connector Setup")
        title_label.setFont(QFont("sans-serif", 16, QFont.Bold))
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        desc_label = QLabel(
            "Dieser Assistent installiert den lokalen Hardware-Agenten für Ihre Kickerkasse.\n"
            "Der Agent stellt eine lokale Brücke zur USB-Kassenschublade (BT-100U) bereit.\n\n"
            "Klicken Sie auf 'Weiter', um die Einrichtung zu starten."
        )
        desc_label.setFont(QFont("sans-serif", 11))
        desc_label.setWordWrap(True)
        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        layout.addStretch()
        self.setLayout(layout)

class SystemCheckPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Systemprüfung")
        self.layout = QVBoxLayout()
        self.status_label = QLabel("Führe Systemprüfungen durch...")
        self.status_label.setFont(QFont("sans-serif", 11, QFont.Bold))
        self.layout.addWidget(self.status_label)
        self.setLayout(self.layout)

    def initializePage(self):
        dist = platform.system()
        py_version = platform.python_version()
        has_serial = False
        try:
            import serial
            has_serial = True
        except ImportError:
            pass

        is_linux = (dist == "Linux")
        self.add_check_result("Betriebssystem: Linux", is_linux)
        self.add_check_result(f"Python Version: {py_version} (>= 3.0)", True)
        self.add_check_result("USB Serial Treiber (pyserial)", has_serial)

        if is_linux and has_serial:
            self.status_label.setText("✓ Alle Systemanforderungen erfüllt.")
            self.status_label.setStyleSheet("color: #27ae60;")
        else:
            self.status_label.setText("✗ Systemprüfung fehlgeschlagen. Bitte Abhängigkeiten prüfen.")
            self.status_label.setStyleSheet("color: #c0392b;")

    def add_check_result(self, text, success):
        icon = "✓" if success else "✗"
        color = "#27ae60" if success else "#c0392b"
        label = QLabel(f"{icon} {text}")
        label.setFont(QFont("sans-serif", 11))
        label.setStyleSheet(f"color: {color}; margin-left: 15px;")
        self.layout.addWidget(label)

class PrivilegesPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Rechteprüfung")
        self.layout = QVBoxLayout()
        self.info_label = QLabel()
        self.info_label.setFont(QFont("sans-serif", 11))
        self.info_label.setWordWrap(True)
        self.layout.addWidget(self.info_label)

        self.elevate_btn = QPushButton("Als Administrator (root) autorisieren")
        self.elevate_btn.clicked.connect(self.request_privileges)
        self.layout.addWidget(self.elevate_btn)
        self.setLayout(self.layout)

    def initializePage(self):
        if os.geteuid() == 0:
            self.info_label.setText("✓ Root-Berechtigungen sind aktiv. Sie können fortfahren.")
            self.info_label.setStyleSheet("color: #27ae60; font-weight: bold;")
            self.elevate_btn.setVisible(False)
        else:
            self.info_label.setText(
                "Für die Installation von systemd Services und Kopiervorgänge in Systemordner "
                "werden Root-Rechte benötigt.\n\nBitte klicken Sie auf den Button, um sich zu authentifizieren."
            )
            self.info_label.setStyleSheet("color: #c0392b;")
            self.elevate_btn.setVisible(True)

    def isComplete(self):
        return os.geteuid() == 0

    def request_privileges(self):
        """Erhöht Rechte mit pkexec unter Beibehaltung des Displays."""
        script_path = os.path.abspath(sys.argv[0])

        # WICHTIG: DISPLAY und XAUTHORITY an pkexec übergeben!
        env = os.environ.copy()
        display = env.get("DISPLAY", ":0")
        xauthority = env.get("XAUTHORITY", "")

        # Baue pkexec-Befehl mit Umgebungsvariablen
        cmd = [
            "pkexec",
            "env",
            f"DISPLAY={display}",
            f"XAUTHORITY={xauthority}" if xauthority else "",
            sys.executable,
            script_path
        ]
        # Leere Strings entfernen
        cmd = [c for c in cmd if c]

        try:
            result = subprocess.run(cmd, check=True)
            sys.exit(0)
        except subprocess.CalledProcessError as e:
            self.info_label.setText(
                f"✗ Autorisierung fehlgeschlagen (Code {e.returncode}).\n\n"
                "Alternativ können Sie das Setup im Terminal starten:\n"
                f"sudo {sys.executable} {script_path}"
            )
            self.info_label.setStyleSheet("color: #c0392b;")

class InstallationPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Installation läuft")
        layout = QVBoxLayout()
        self.status_label = QLabel("Bereite Kopier- und Konfigurationsvorgänge vor...")
        self.status_label.setFont(QFont("sans-serif", 11))
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)

        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)
        layout.addStretch()
        self.setLayout(layout)

        self.is_installed = False
        self.worker = InstallationWorker()
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.installation_finished)

    def initializePage(self):
        if os.geteuid() == 0:
            self.worker.start()
        else:
            self.status_label.setText("Fehler: Keine ausreichenden Rechte zur Installation.")

    def update_progress(self, val, msg):
        self.progress_bar.setValue(val)
        self.status_label.setText(msg)

    def installation_finished(self, success, msg):
        self.is_installed = success
        if success:
            self.status_label.setText("✓ Installation der System-Dateien erfolgreich abgeschlossen.")
            self.status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        else:
            self.status_label.setText(f"✗ Fehler während der Installation: {msg}")
            self.status_label.setStyleSheet("color: #c0392b; font-weight: bold;")
        self.completeChanged.emit()

    def isComplete(self):
        return self.is_installed

class HardwareTestPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Hardware Integrationstest")
        layout = QVBoxLayout()
        desc = QLabel(
            "Der Installer sendet nun ein elektronisches Testsignal (ESC/POS-Impuls) an die serielle Schnittstelle "
            "(/dev/ttyUSB*), um die automatische Kassenöffnung direkt zu validieren."
        )
        desc.setWordWrap(True)
        desc.setFont(QFont("sans-serif", 11))

        self.test_btn = QPushButton("Hardware-Impuls jetzt testen")
        self.test_btn.clicked.connect(self.run_hardware_test)

        self.result_box = QFrame()
        self.result_box.setFrameShape(QFrame.StyledPanel)
        self.result_layout = QVBoxLayout()
        self.result_label = QLabel("Warte auf Testdurchführung...")
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setFont(QFont("sans-serif", 11, QFont.Bold))
        self.result_layout.addWidget(self.result_label)
        self.result_box.setLayout(self.result_layout)
        self.set_result_style("neutral")

        layout.addWidget(desc)
        layout.addWidget(self.test_btn)
        layout.addWidget(self.result_box)
        layout.addStretch()
        self.setLayout(layout)

        self.test_worker = HardwareTestWorker()
        self.test_worker.result.connect(self.handle_test_result)

    def run_hardware_test(self):
        self.result_label.setText("Sende Impuls an Kassenschubladen-Relais...")
        self.test_btn.setEnabled(False)
        self.test_worker.start()

    def handle_test_result(self, success, message):
        self.test_btn.setEnabled(True)
        self.result_label.setText(message)
        self.set_result_style("success" if success else "fail")

    def set_result_style(self, mode):
        if mode == "success":
            self.result_box.setStyleSheet("background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 4px;")
            self.result_label.setStyleSheet("color: #155724;")
        elif mode == "fail":
            self.result_box.setStyleSheet("background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 4px;")
            self.result_label.setStyleSheet("color: #721c24;")
        else:
            self.result_box.setStyleSheet("background-color: #e2e3e5; border: 1px solid #ced4da; border-radius: 4px;")
            self.result_label.setStyleSheet("color: #383d41;")

    def isComplete(self):
        return True

class ConclusionPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Installation abgeschlossen")
        layout = QVBoxLayout()
        success_title = QLabel("Kickerkasse Hardware Agent einsatzbereit!")
        success_title.setFont(QFont("sans-serif", 14, QFont.Bold))
        success_title.setStyleSheet("color: #27ae60; margin-bottom: 10px;")

        endpoint_info = QLabel(
            "Der lokale REST-Endpoint wurde erfolgreich eingerichtet und via systemd gestartet:\n\n"
            "▶ URL: http://127.0.0.1:8765/status\n\n"
            "Ihre Web-PWA (Kickerkasse) kann ab sofort lokale HTTP-POST-Requests an "
            "http://127.0.0.1:8765/openDrawer senden, um die Kassenschublade anzusteuern."
        )
        endpoint_info.setWordWrap(True)
        endpoint_info.setFont(QFont("sans-serif", 11))

        layout.addWidget(success_title)
        layout.addWidget(endpoint_info)
        layout.addStretch()
        self.setLayout(layout)

class SetupWizard(QWizard):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kickerkasse Hardware Connector - Setup")
        self.resize(640, 480)
        self.setStyleSheet(STYLE_SHEET)

        self.addPage(WelcomePage(self))
        self.addPage(SystemCheckPage(self))
        self.addPage(PrivilegesPage(self))
        self.addPage(InstallationPage(self))
        self.addPage(HardwareTestPage(self))
        self.addPage(ConclusionPage(self))

        self.setButtonText(QWizard.BackButton, "Zurück")
        self.setButtonText(QWizard.NextButton, "Weiter")
        self.setButtonText(QWizard.CancelButton, "Abbrechen")
        self.setButtonText(QWizard.FinishButton, "Abschließen")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    wizard = SetupWizard()
    wizard.show()
    sys.exit(app.exec())
