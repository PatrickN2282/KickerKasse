#!/usr/bin/env python3
import sys
import os
import logging
import glob
import hmac
import tempfile
import threading
from pathlib import Path
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
DRAWER_DEVICE_ENV = {
    "main": "KICKERKASSE_MAIN_DRAWER_DEVICE",
    "small_parts": "KICKERKASSE_SMALL_PARTS_DRAWER_DEVICE",
}
DRAWER_LABELS = {
    "main": "Hauptkassenschublade",
    "small_parts": "Kleinteile-Lager",
}
SERIAL_LOCK = threading.Lock()
CONFIG_TOKEN_ENV = "KICKERKASSE_AGENT_CONFIG_TOKEN"
DEFAULT_CONFIG_PATH = "/etc/default/kickerkasse-agent"


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


def validate_request_origin():
    """Reject browser requests from origins that were not paired locally."""
    origin = (request.headers.get("Origin") or "").strip()
    if not origin:
        # Non-browser localhost clients do not send an Origin header.
        return None

    parsed_origin = urlparse(origin)
    has_valid_origin = parsed_origin.scheme in {"http", "https"} and bool(parsed_origin.netloc)
    if origin in get_allowed_origins() or (ALLOW_ALL_ORIGINS and has_valid_origin):
        return None

    return jsonify({
        "status": "error",
        "message": "Dieser Browser ist nicht mit dem lokalen Hardware-Agenten verbunden",
    }), 403


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
        response.headers["Access-Control-Allow-Headers"] = (
            "Content-Type,Authorization,X-Kickerkasse-Config-Token"
        )
        response.headers["Access-Control-Allow-Private-Network"] = "true"
    return response


def discover_adapter_ports():
    """Return stable serial paths first and never list one adapter twice."""
    candidates = (
        sorted(glob.glob('/dev/serial/by-id/*'))
        + sorted(glob.glob('/dev/serial/by-path/*'))
        + sorted(glob.glob('/dev/ttyUSB*'))
        + sorted(glob.glob('/dev/ttyACM*'))
    )
    ports = []
    seen_devices = set()
    for candidate in candidates:
        if not os.path.exists(candidate):
            continue
        resolved = os.path.realpath(candidate)
        if resolved in seen_devices:
            continue
        seen_devices.add(resolved)
        ports.append(candidate)
    return ports


def normalize_drawer_target(target):
    normalized = (target or "main").strip().lower().replace('-', '_')
    aliases = {
        "primary": "main",
        "cash": "main",
        "lager": "small_parts",
        "storage": "small_parts",
        "smallparts": "small_parts",
    }
    normalized = aliases.get(normalized, normalized)
    return normalized if normalized in DRAWER_DEVICE_ENV else None


def resolve_drawer_port(target):
    """Resolve a logical drawer to a configured or deterministic adapter path."""
    normalized = normalize_drawer_target(target)
    if not normalized:
        return None, "Unbekanntes Schubladenziel"

    configured = (os.environ.get(DRAWER_DEVICE_ENV[normalized]) or "").strip()
    if configured:
        if os.path.exists(configured):
            return configured, None
        return None, f"Konfigurierter Adapter ist nicht verfügbar: {configured}"

    ports = discover_adapter_ports()
    other_target = "small_parts" if normalized == "main" else "main"
    other_configured = (os.environ.get(DRAWER_DEVICE_ENV[other_target]) or "").strip()
    if other_configured and os.path.exists(other_configured):
        other_resolved = os.path.realpath(other_configured)
        ports = [port for port in ports if os.path.realpath(port) != other_resolved]
        index = 0
    else:
        index = 0 if normalized == "main" else 1
    if len(ports) <= index:
        return None, f"Kein USB-Adapter für {DRAWER_LABELS[normalized]} gefunden"
    return ports[index], None


def get_drawer_status(target):
    port, error = resolve_drawer_port(target)
    return {
        "target": target,
        "label": DRAWER_LABELS[target],
        "status": "connected" if port else "disconnected",
        "device": port,
        "configured_by": "environment" if os.environ.get(DRAWER_DEVICE_ENV[target]) else "automatic",
        "environment_variable": DRAWER_DEVICE_ENV[target],
        "error": error,
    }


def get_config_path():
    return Path(os.environ.get("KICKERKASSE_AGENT_CONFIG_PATH", DEFAULT_CONFIG_PATH))


def validate_config_token():
    """Return an error response when the local configuration token is missing or invalid."""
    expected = (os.environ.get(CONFIG_TOKEN_ENV) or "").strip()
    supplied = (request.headers.get("X-Kickerkasse-Config-Token") or "").strip()
    if not expected:
        return jsonify({
            "status": "error",
            "message": "Kein lokaler Konfigurationscode eingerichtet. Hardware-Agent aktualisieren.",
        }), 503
    if not supplied or not hmac.compare_digest(supplied, expected):
        return jsonify({
            "status": "error",
            "message": "Lokaler Konfigurationscode ist ungültig",
        }), 403
    return None


def send_drawer_pulse(port, label):
    """Send one serialized ESC/POS drawer pulse to an already validated device path."""
    with SERIAL_LOCK:
        with serial.Serial(port, baudrate=9600, timeout=1) as ser:
            ser.write(DRAWER_PULSE)
            ser.flush()
    logging.info("%s über Schnittstelle %s ausgelöst.", label, port)


def persist_drawer_mapping(main_device, small_parts_device):
    """Atomically update only the two drawer variables in the root-owned environment file."""
    persist_environment_updates({
        DRAWER_DEVICE_ENV["main"]: main_device,
        DRAWER_DEVICE_ENV["small_parts"]: small_parts_device,
    })
    os.environ[DRAWER_DEVICE_ENV["main"]] = main_device
    os.environ[DRAWER_DEVICE_ENV["small_parts"]] = small_parts_device


def persist_environment_updates(replacements):
    """Atomically update selected variables while preserving the remaining agent config."""
    config_path = get_config_path()
    existing_lines = []
    if config_path.exists():
        existing_lines = config_path.read_text(encoding="utf-8").splitlines()

    replaced = set()
    updated_lines = []
    for line in existing_lines:
        stripped = line.strip()
        matched_key = next(
            (key for key in replacements if stripped.startswith(f"{key}=")),
            None,
        )
        if matched_key:
            if matched_key not in replaced:
                updated_lines.append(f"{matched_key}={replacements[matched_key]}")
                replaced.add(matched_key)
            continue
        updated_lines.append(line)

    for key, value in replacements.items():
        if key not in replaced:
            updated_lines.append(f"{key}={value}")

    config_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_name = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=str(config_path.parent),
            prefix=f".{config_path.name}.",
            delete=False,
        ) as temporary_file:
            temporary_name = temporary_file.name
            temporary_file.write("\n".join(updated_lines) + "\n")
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        os.chmod(temporary_name, 0o600)
        os.replace(temporary_name, config_path)
    finally:
        if temporary_name and os.path.exists(temporary_name):
            os.unlink(temporary_name)



def pair_current_origin():
    """Authorize the calling PWA origin after validating the client-local setup code."""
    expected = (os.environ.get(CONFIG_TOKEN_ENV) or "").strip()
    supplied = str(request.form.get("config_token") or "").strip()
    origin = (request.headers.get("Origin") or "").strip()
    parsed_origin = urlparse(origin)
    if not expected:
        return jsonify({
            "status": "error",
            "message": "Kein lokaler Konfigurationscode eingerichtet. Hardware-Agent aktualisieren.",
        }), 503
    if not supplied or not hmac.compare_digest(supplied, expected):
        return jsonify({"status": "error", "message": "Lokaler Konfigurationscode ist ungültig"}), 403
    if parsed_origin.scheme not in {"http", "https"} or not parsed_origin.netloc:
        return jsonify({"status": "error", "message": "Browser-Origin ist ungültig"}), 400

    allowed_origins = get_allowed_origins()
    allowed_origins.add(origin)
    configured_origins = sorted(allowed_origins - DEFAULT_ALLOWED_ORIGINS)
    configured_value = ",".join(configured_origins)
    try:
        persist_environment_updates({"KICKERKASSE_AGENT_ALLOWED_ORIGINS": configured_value})
    except OSError as exc:
        logging.error("Browser-Origin konnte nicht gespeichert werden: %s", exc)
        return jsonify({
            "status": "error",
            "message": f"Browser-Freigabe konnte nicht gespeichert werden: {exc}",
        }), 500
    os.environ["KICKERKASSE_AGENT_ALLOWED_ORIGINS"] = configured_value
    logging.info("PWA-Origin für lokalen Hardwarezugriff freigegeben: %s", origin)
    return jsonify({
        "status": "success",
        "origin": origin,
        "message": "Dieser Browser wurde für den lokalen Hardware-Agenten freigegeben.",
    }), 200

@app.route('/status', methods=['GET'])
def get_status():
    """Return both logical drawer assignments while keeping legacy fields."""
    drawers = {
        target: get_drawer_status(target)
        for target in DRAWER_DEVICE_ENV
    }
    main = drawers["main"]
    payload = {
        "status": main["status"],
        "device": main["device"],
        "description": "Kickerkasse USB Cash Drawer Adapter",
        "capabilities": ["multi_drawer", "drawer_configuration"],
        "configuration_protected": bool(os.environ.get(CONFIG_TOKEN_ENV)),
        "available_devices": discover_adapter_ports(),
        "drawers": drawers,
    }
    if main["status"] == "connected":
        return jsonify(payload), 200
    payload["error"] = main["error"]
    return jsonify(payload), 404


@app.route('/pair', methods=['POST', 'OPTIONS'])
def pair_browser():
    # Bewusst als einfacher Formular-POST ohne Preflight: Vor dem Pairing darf der
    # externe PWA-Origin noch nicht generell in den CORS-Antworten auftauchen. Ein
    # folgenloser OPTIONS-Handshake wird für Browser mit Local-Network-Schutz erlaubt;
    # der anschließende POST bleibt durch den lokalen Installationscode geschützt.
    if request.method == 'OPTIONS':
        origin = (request.headers.get("Origin") or "").strip()
        parsed_origin = urlparse(origin)
        if parsed_origin.scheme not in {"http", "https"} or not parsed_origin.netloc:
            return ('', 400)
        response = app.make_response(('', 204))
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Methods"] = "POST,OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        response.headers["Access-Control-Allow-Private-Network"] = "true"
        response.headers["Vary"] = "Origin"
        return response
    return pair_current_origin()


@app.route('/testDevice', methods=['POST', 'OPTIONS'])
def test_device():
    """Pulse one discovered adapter without changing its logical assignment."""
    if request.method == 'OPTIONS':
        return ('', 204)
    auth_error = validate_config_token()
    if auth_error:
        return auth_error
    if not request.is_json:
        return jsonify({"status": "error", "message": "JSON-Anfrage erforderlich"}), 415

    requested_device = str((request.get_json(silent=True) or {}).get("device") or "").strip()
    available_devices = discover_adapter_ports()
    if requested_device not in available_devices:
        return jsonify({
            "status": "error",
            "message": "Der ausgewählte Adapter ist nicht mehr verfügbar",
        }), 400
    try:
        send_drawer_pulse(requested_device, "Adaptertest")
        return jsonify({
            "status": "success",
            "device": requested_device,
            "message": f"Testimpuls erfolgreich an {requested_device} gesendet.",
        }), 200
    except Exception as exc:
        logging.error("Adaptertest auf %s fehlgeschlagen: %s", requested_device, exc)
        return jsonify({
            "status": "error",
            "message": f"Serieller Schnittstellenfehler: {exc}",
        }), 500


@app.route('/configuration', methods=['POST', 'OPTIONS'])
def save_configuration():
    """Persist a verified two-drawer mapping locally on the cash-register client."""
    if request.method == 'OPTIONS':
        return ('', 204)
    auth_error = validate_config_token()
    if auth_error:
        return auth_error
    if not request.is_json:
        return jsonify({"status": "error", "message": "JSON-Anfrage erforderlich"}), 415

    payload = request.get_json(silent=True) or {}
    main_device = str(payload.get("main_device") or "").strip()
    small_parts_device = str(payload.get("small_parts_device") or "").strip()
    available_devices = discover_adapter_ports()
    unavailable = [
        device for device in (main_device, small_parts_device)
        if not device or device not in available_devices
    ]
    if unavailable:
        return jsonify({
            "status": "error",
            "message": "Beide ausgewählten Adapter müssen aktuell angeschlossen sein",
        }), 400
    if os.path.realpath(main_device) == os.path.realpath(small_parts_device):
        return jsonify({
            "status": "error",
            "message": "Hauptschublade und Kleinteile-Lager benötigen verschiedene Adapter",
        }), 409

    try:
        persist_drawer_mapping(main_device, small_parts_device)
        return jsonify({
            "status": "success",
            "message": "Adapterzuordnung lokal gespeichert und sofort aktiviert.",
            "drawers": {
                "main": get_drawer_status("main"),
                "small_parts": get_drawer_status("small_parts"),
            },
        }), 200
    except OSError as exc:
        logging.error("Adapterzuordnung konnte nicht gespeichert werden: %s", exc)
        return jsonify({
            "status": "error",
            "message": f"Lokale Konfiguration konnte nicht gespeichert werden: {exc}",
        }), 500


@app.route('/openDrawer', defaults={'target': 'main'}, methods=['POST', 'OPTIONS'])
@app.route('/openDrawer/<target>', methods=['POST', 'OPTIONS'])
def open_drawer(target):
    """Trigger one explicitly addressed drawer; legacy endpoint targets main."""
    if request.method == 'OPTIONS':
        return ('', 204)

    origin_error = validate_request_origin()
    if origin_error:
        return origin_error

    normalized = normalize_drawer_target(target)
    if not normalized:
        return jsonify({"status": "error", "message": "Unbekanntes Schubladenziel"}), 400

    port, resolve_error = resolve_drawer_port(normalized)
    if not port:
        return jsonify({
            "status": "error",
            "target": normalized,
            "message": resolve_error or "Hardware nicht angeschlossen",
        }), 404

    other_target = "small_parts" if normalized == "main" else "main"
    other_port, _ = resolve_drawer_port(other_target)
    if other_port and os.path.realpath(other_port) == os.path.realpath(port):
        return jsonify({
            "status": "error",
            "target": normalized,
            "message": "Hauptschublade und Kleinteile-Lager dürfen nicht denselben Adapter verwenden",
        }), 409
        
    try:
        # ESC/POS-Impulsfolge für Kassenschubladenöffner (Pin 2, 25/250 ms)
        send_drawer_pulse(port, DRAWER_LABELS[normalized])
        return jsonify({
            "status": "success",
            "target": normalized,
            "device": port,
            "message": f"Schaltimpuls für {DRAWER_LABELS[normalized]} erfolgreich an {port} übermittelt."
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
