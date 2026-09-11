from services import agent


def test_two_adapters_are_assigned_to_distinct_logical_drawers(monkeypatch):
    monkeypatch.delenv("KICKERKASSE_MAIN_DRAWER_DEVICE", raising=False)
    monkeypatch.delenv("KICKERKASSE_SMALL_PARTS_DRAWER_DEVICE", raising=False)
    monkeypatch.setattr(agent, "discover_adapter_ports", lambda: ["/dev/main", "/dev/storage"])

    assert agent.resolve_drawer_port("main") == ("/dev/main", None)
    assert agent.resolve_drawer_port("small_parts") == ("/dev/storage", None)


def test_stable_environment_mapping_takes_precedence(monkeypatch):
    monkeypatch.setenv("KICKERKASSE_SMALL_PARTS_DRAWER_DEVICE", "/dev/serial/by-id/storage")
    monkeypatch.setattr(agent.os.path, "exists", lambda path: path == "/dev/serial/by-id/storage")

    assert agent.resolve_drawer_port("small_parts") == ("/dev/serial/by-id/storage", None)


def test_automatic_storage_assignment_excludes_explicit_main_adapter(monkeypatch):
    monkeypatch.setenv("KICKERKASSE_MAIN_DRAWER_DEVICE", "/dev/adapter-b")
    monkeypatch.delenv("KICKERKASSE_SMALL_PARTS_DRAWER_DEVICE", raising=False)
    monkeypatch.setattr(agent.os.path, "exists", lambda path: path in {"/dev/adapter-a", "/dev/adapter-b"})
    monkeypatch.setattr(agent.os.path, "realpath", lambda path: path)
    monkeypatch.setattr(agent, "discover_adapter_ports", lambda: ["/dev/adapter-a", "/dev/adapter-b"])

    assert agent.resolve_drawer_port("small_parts") == ("/dev/adapter-a", None)


def test_legacy_and_small_parts_endpoints_address_different_ports(monkeypatch):
    opened_ports = []

    class FakeSerial:
        def __init__(self, port, **_kwargs):
            self.port = port

        def __enter__(self):
            opened_ports.append(self.port)
            return self

        def __exit__(self, *_args):
            return False

        def write(self, _payload):
            return None

        def flush(self):
            return None

    ports = {"main": "/dev/main", "small_parts": "/dev/storage"}
    monkeypatch.setattr(agent, "resolve_drawer_port", lambda target: (ports[target], None))
    monkeypatch.setattr(agent.os.path, "realpath", lambda path: path)
    monkeypatch.setattr(agent.serial, "Serial", FakeSerial)

    client = agent.app.test_client()
    main_response = client.post("/openDrawer")
    storage_response = client.post("/openDrawer/small_parts")

    assert main_response.status_code == 200
    assert storage_response.status_code == 200
    assert main_response.get_json()["target"] == "main"
    assert storage_response.get_json()["target"] == "small_parts"
    assert opened_ports == ["/dev/main", "/dev/storage"]


def test_drawer_endpoint_rejects_unpaired_browser_origin_before_pulse(monkeypatch):
    pulsed = []
    monkeypatch.delenv("KICKERKASSE_AGENT_ALLOWED_ORIGINS", raising=False)
    monkeypatch.setattr(agent, "ALLOW_ALL_ORIGINS", False)
    monkeypatch.setattr(agent, "resolve_drawer_port", lambda _target: ("/dev/main", None))
    monkeypatch.setattr(agent, "send_drawer_pulse", lambda port, _label: pulsed.append(port))

    response = agent.app.test_client().post(
        "/openDrawer",
        headers={"Origin": "https://unpaired.example.org"},
    )

    assert response.status_code == 403
    assert pulsed == []


def test_drawer_endpoint_accepts_paired_browser_origin(monkeypatch):
    pulsed = []
    monkeypatch.setenv("KICKERKASSE_AGENT_ALLOWED_ORIGINS", "https://kasse.example.org")
    monkeypatch.setattr(agent, "ALLOW_ALL_ORIGINS", False)
    ports = {"main": "/dev/main", "small_parts": "/dev/storage"}
    monkeypatch.setattr(agent, "resolve_drawer_port", lambda target: (ports[target], None))
    monkeypatch.setattr(agent, "send_drawer_pulse", lambda port, _label: pulsed.append(port))

    response = agent.app.test_client().post(
        "/openDrawer",
        headers={"Origin": "https://kasse.example.org"},
    )

    assert response.status_code == 200
    assert response.headers["Access-Control-Allow-Origin"] == "https://kasse.example.org"
    assert pulsed == ["/dev/main"]


def test_device_test_requires_local_configuration_token(monkeypatch):
    monkeypatch.setenv("KICKERKASSE_AGENT_CONFIG_TOKEN", "local-secret")
    monkeypatch.setattr(agent, "discover_adapter_ports", lambda: ["/dev/adapter-a"])

    response = agent.app.test_client().post(
        "/testDevice",
        json={"device": "/dev/adapter-a"},
    )

    assert response.status_code == 403
    assert "ungültig" in response.get_json()["message"]


def test_device_test_only_pulses_selected_discovered_adapter(monkeypatch):
    pulsed = []
    monkeypatch.setenv("KICKERKASSE_AGENT_CONFIG_TOKEN", "local-secret")
    monkeypatch.setattr(agent, "discover_adapter_ports", lambda: ["/dev/adapter-a", "/dev/adapter-b"])
    monkeypatch.setattr(agent, "send_drawer_pulse", lambda port, _label: pulsed.append(port))

    response = agent.app.test_client().post(
        "/testDevice",
        json={"device": "/dev/adapter-b"},
        headers={"X-Kickerkasse-Config-Token": "local-secret"},
    )

    assert response.status_code == 200
    assert pulsed == ["/dev/adapter-b"]


def test_configuration_is_saved_locally_and_activated_immediately(monkeypatch, tmp_path):
    config_path = tmp_path / "kickerkasse-agent"
    config_path.write_text(
        "# existing\n"
        "KICKERKASSE_MAIN_DRAWER_DEVICE=/dev/old\n"
        "KICKERKASSE_AGENT_CONFIG_TOKEN=local-secret\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("KICKERKASSE_AGENT_CONFIG_TOKEN", "local-secret")
    monkeypatch.setenv("KICKERKASSE_AGENT_CONFIG_PATH", str(config_path))
    monkeypatch.setattr(agent, "discover_adapter_ports", lambda: ["/dev/adapter-a", "/dev/adapter-b"])
    monkeypatch.setattr(agent.os.path, "realpath", lambda path: path)

    response = agent.app.test_client().post(
        "/configuration",
        json={
            "main_device": "/dev/adapter-b",
            "small_parts_device": "/dev/adapter-a",
        },
        headers={"X-Kickerkasse-Config-Token": "local-secret"},
    )

    assert response.status_code == 200
    saved = config_path.read_text(encoding="utf-8")
    assert "KICKERKASSE_MAIN_DRAWER_DEVICE=/dev/adapter-b" in saved
    assert "KICKERKASSE_SMALL_PARTS_DRAWER_DEVICE=/dev/adapter-a" in saved
    assert "KICKERKASSE_AGENT_CONFIG_TOKEN=local-secret" in saved
    assert agent.os.environ["KICKERKASSE_MAIN_DRAWER_DEVICE"] == "/dev/adapter-b"
    assert agent.os.environ["KICKERKASSE_SMALL_PARTS_DRAWER_DEVICE"] == "/dev/adapter-a"


def test_configuration_rejects_same_physical_adapter(monkeypatch):
    monkeypatch.setenv("KICKERKASSE_AGENT_CONFIG_TOKEN", "local-secret")
    monkeypatch.setattr(agent, "discover_adapter_ports", lambda: ["/dev/by-id/a", "/dev/ttyUSB0"])
    monkeypatch.setattr(agent.os.path, "realpath", lambda _path: "/dev/ttyUSB0")

    response = agent.app.test_client().post(
        "/configuration",
        json={
            "main_device": "/dev/by-id/a",
            "small_parts_device": "/dev/ttyUSB0",
        },
        headers={"X-Kickerkasse-Config-Token": "local-secret"},
    )

    assert response.status_code == 409


def test_pairing_authorizes_only_current_origin_with_local_token(monkeypatch, tmp_path):
    config_path = tmp_path / "kickerkasse-agent"
    config_path.write_text("KICKERKASSE_AGENT_CONFIG_TOKEN=local-secret\n", encoding="utf-8")
    monkeypatch.setenv("KICKERKASSE_AGENT_CONFIG_TOKEN", "local-secret")
    monkeypatch.setenv("KICKERKASSE_AGENT_CONFIG_PATH", str(config_path))
    monkeypatch.delenv("KICKERKASSE_AGENT_ALLOWED_ORIGINS", raising=False)

    response = agent.app.test_client().post(
        "/pair",
        data={"config_token": "local-secret"},
        headers={"Origin": "https://kasse.example.org"},
    )

    assert response.status_code == 200
    assert response.headers["Access-Control-Allow-Origin"] == "https://kasse.example.org"
    assert "KICKERKASSE_AGENT_ALLOWED_ORIGINS=https://kasse.example.org" in config_path.read_text(encoding="utf-8")
    assert agent.os.environ["KICKERKASSE_AGENT_ALLOWED_ORIGINS"] == "https://kasse.example.org"
