Kickerkasse Hardware Agent – Installationspaket
================================================

Inhalt:
  agent.py                    – Hardware-Agent (Flask, Port 8765)
  install_agent_service.py    – Installiert Agent als systemd-Service
  kickerkasse_bootstrapper.py – Einmaliger Installer-Helfer (Port 8766)
  setup_wizard.py             – Grafischer Setup-Assistent (PySide6)
  Kickerkasse-Install.desktop – Desktop-Starter für den Setup-Assistenten

Voraussetzungen:
  - Linux (z. B. Nobara, Fedora, Debian/Ubuntu)
  - Python 3.9+
  - USB-Kassenschublade (BT-100U) angeschlossen
  - Falls die PWA über Domain/öffentliche URL läuft: Origin freigeben über
    KICKERKASSE_AGENT_ALLOWED_ORIGINS (z. B. in der Service-Unit)
  - Optional: KICKERKASSE_AGENT_ALLOW_ALL_ORIGINS=1 nur als Notlösung setzen
    (Sicherheitsrisiko: erlaubt Zugriffe von beliebigen Websites)

Installation (einmalig auf dem Kassen-PC):
------------------------------------------

Empfohlene Methode – grafischer Assistent:

  1. Doppelklick auf „Kickerkasse-Install.desktop" im Dateimanager
     ODER im Terminal ausführen:
       python3 setup_wizard.py

  2. Dem Assistenten folgen: Systemprüfung → Root-Rechte → Installation → Hardware-Test.

  3. Nach Abschluss läuft der Agent automatisch als systemd-Service und
     startet bei jedem Booten neu.

Alternative – Terminal (ohne grafischen Assistenten):

  sudo python3 install_agent_service.py

Status prüfen:
    systemctl status kickerkasse-agent
    curl http://127.0.0.1:8765/status

Schublade manuell öffnen:
    curl -X POST http://127.0.0.1:8765/openDrawer
