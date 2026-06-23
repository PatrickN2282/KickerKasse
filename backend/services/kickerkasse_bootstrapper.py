#!/usr/bin/env python3
"""
Kickerkasse Installer-Bootstrapper
────────────────────────────────────
Einmalig auf dem Kassen-PC als root starten:

    sudo python3 kickerkasse_bootstrapper.py

Öffnet Port 8766 (nur localhost) und führt bei POST /install
das install_agent_service.py aus. Beendet sich danach selbst.

Der Admin-Bereich der KickerKasse-PWA ruft http://127.0.0.1:8766/install
direkt aus dem Browser des Kassen-PCs auf.
"""

import http.server
import json
import os
import subprocess
import sys
import threading
from pathlib import Path

PORT = 8766
SCRIPT_DIR = Path(__file__).resolve().parent
INSTALL_SCRIPT = SCRIPT_DIR / "install_agent_service.py"

# CORS-Origins die der Browser mitschicken darf
# (PWA läuft auf dem Homeserver, Browser aber auf Kassen-PC)
ALLOWED_ORIGINS = {
    "http://localhost",
    "http://127.0.0.1",
    "null",  # lokale Datei-Aufrufe
}


def _cors_origin(origin: str | None) -> str:
    """Gibt den erlaubten CORS-Origin zurück oder leer."""
    if not origin:
        return "*"
    # Alles erlauben – Bootstrapper läuft nur kurz lokal
    return origin


class BootstrapHandler(http.server.BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        print(f"[Bootstrapper] {fmt % args}")

    def _send_json(self, code: int, payload: dict, origin: str = ""):
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", origin or "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        origin = self.headers.get("Origin", "*")
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        origin = self.headers.get("Origin", "*")
        if self.path == "/health":
            self._send_json(200, {"status": "bootstrapper_ready", "port": PORT}, origin)
        else:
            self._send_json(404, {"error": "Not found"}, origin)

    def do_POST(self):
        origin = self.headers.get("Origin", "*")

        if self.path != "/install":
            self._send_json(404, {"error": "Not found"}, origin)
            return

        if os.geteuid() != 0:
            self._send_json(403, {
                "success": False,
                "error": "Bootstrapper muss als root laufen. Bitte: sudo python3 kickerkasse_bootstrapper.py"
            }, origin)
            return

        if not INSTALL_SCRIPT.exists():
            self._send_json(500, {
                "success": False,
                "error": f"Installationsskript nicht gefunden: {INSTALL_SCRIPT}"
            }, origin)
            return

        print(f"[Bootstrapper] Starte Installation via {INSTALL_SCRIPT} ...")

        try:
            result = subprocess.run(
                [sys.executable, str(INSTALL_SCRIPT)],
                capture_output=True,
                text=True,
                timeout=120,
            )
            output = (result.stdout + result.stderr).strip()
            success = result.returncode == 0

            print(f"[Bootstrapper] Installation {'erfolgreich' if success else 'fehlgeschlagen'} (rc={result.returncode})")
            print(output)

            self._send_json(200 if success else 500, {
                "success": success,
                "output": output,
                "error": None if success else f"Exit-Code {result.returncode}",
            }, origin)

        except subprocess.TimeoutExpired:
            self._send_json(500, {
                "success": False,
                "error": "Timeout – Installation hat mehr als 120 Sekunden gedauert.",
                "output": "",
            }, origin)
        except Exception as exc:
            self._send_json(500, {
                "success": False,
                "error": str(exc),
                "output": "",
            }, origin)

        # Nach erfolgreicher Installation Bootstrapper beenden
        print("[Bootstrapper] Installation abgeschlossen. Bootstrapper beendet sich in 2 Sekunden.")
        threading.Timer(2.0, lambda: os._exit(0)).start()


def main():
    if os.geteuid() != 0:
        print("━" * 60)
        print("  FEHLER: Bitte als root ausführen:")
        print("  sudo python3 kickerkasse_bootstrapper.py")
        print("━" * 60)
        sys.exit(1)

    print("━" * 60)
    print("  Kickerkasse Installer-Bootstrapper")
    print(f"  Lauscht auf http://127.0.0.1:{PORT}")
    print()
    print("  Öffne jetzt den Admin-Bereich der KickerKasse-PWA")
    print("  auf DIESEM PC und klicke 'Agent installieren'.")
    print()
    print("  Abbruch: Strg+C")
    print("━" * 60)

    server = http.server.HTTPServer(("127.0.0.1", PORT), BootstrapHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[Bootstrapper] Abgebrochen.")
        sys.exit(0)


if __name__ == "__main__":
    main()
