#!/usr/bin/env python3
import sys
import os
import logging
import glob
from urllib.parse import urlparse
from flask import Flask, jsonify, request
import serial

# Protokollierung in Logdatei (falls Schreibrechte vorhanden) und Standard-Output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("/var/log/kickerkasse-agent.log", mode='a', encoding='utf-8') if os.access("/var/log", os.W_OK) else logging.NullHandler()
    ]
)

app = Flask(__name__)
# ESC/POS: ESC (0x1B), "p" (0x70), Pin 2 (0x00), on-time (0x19), off-time (0xFA)
DRAWER_PULSE = b'\x1b\x70\x00\x19\xfa'
DEFAULT_ALLOWED_ORIGINS = {
    "http://localhost:9690",
    "http://127.0.0.1:9690",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
}
ALLOW_ALL_ORIGINS = os.environ.get("KICKERKASSE_AGENT_ALLOW_ALL_ORIGINS", "0").lower() in {"1", "true", "yes"}


def get_allowed_origins():
    configured = os.environ.get("KICKERKASSE_AGENT_ALLOWED_ORIGINS", "")
    parsed = set()
    for origin in configured.split(","):
        candidate = origin.strip()
        if not candidate:
            continue
        parsed_url = urlparse(candidate)
        if parsed_url.scheme in {"http", "https"} and parsed_url.netloc:
            parsed.add(candidate)
    return parsed | DEFAULT_ALLOWED_ORIGINS


@app.after_request
def add_cors_headers(response):
    origin = request.headers.get("Origin")
    if not origin:
        return response

    parsed_origin = urlparse(origin)
    has_valid_origin = parsed_origin.scheme in {"http", "https"} and bool(parsed_origin.netloc)
    is_allowed_origin = (
        origin in get_allowed_origins()
        or (ALLOW_ALL_ORIGINS and has_valid_origin)
    )
    if is_allowed_origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Vary"] = "Origin"
        response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    return response

def find_bt100u_port():
    """Dynamische Ermittlung des virtuellen COM-Ports für das USB-Interface."""
    ports = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')
    return ports[0] if ports else None

@app.route('/status', methods=['GET'])
def get_status():
    """Gibt den Verbindungsstatus und Gerätedaten strukturiert als JSON zurück."""
    port = find_bt100u_port()
    if port and os.path.exists(port):
        return jsonify({
            "status": "connected",
            "device": port,
            "description": "BT-100U USB Cash Drawer Adapter"
        }), 200

    return jsonify({
        "status": "disconnected",
        "device": None,
        "error": "Kein kompatibler USB-Seriell-Adapter gefunden."
    }), 404

@app.route('/openDrawer', methods=['POST'])
def open_drawer():
    """Triggert das Öffnen der Schublade durch Absenden eines Schaltimpulses."""
    port = find_bt100u_port()
    if not port:
        return jsonify({"status": "error", "message": "Hardware nicht angeschlossen"}), 404
        
    try:
        # ESC/POS-Impulsfolge für Kassenschubladenöffner (Pin 2, 25/250 ms)
        ser = serial.Serial(port, baudrate=9600, timeout=1)
        ser.write(DRAWER_PULSE)
        ser.flush()
        ser.close()
        logging.info(f"Kassenschublade über Schnittstelle {port} ausgelöst.")
        return jsonify({
            "status": "success",
            "message": f"Schaltimpuls erfolgreich an {port} übermittelt."
        }), 200
    except Exception as e:
        logging.error(f"Fehler bei Hardware-Ansteuerung auf {port}: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Serieller Schnittstellenfehler: {str(e)}"
        }), 500

if __name__ == '__main__':
    # Bindung strikt an localhost (127.0.0.1) zur Absicherung vor unbefugtem Netzwerkzugriff
    app.run(host='127.0.0.1', port=8765, debug=False)