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
  - Python 3.9 oder neuer (wird von install_agent_service.py automatisch geprüft;
    ist die Version zu alt, bricht die Installation mit einer klaren Fehlermeldung ab)
  - Eine oder zwei USB-Kassenschubladen (BT-100U) angeschlossen
  - Falls die PWA über Domain/öffentliche URL läuft: Aktuellen Browser nach der
    Installation im TopAdmin-Bereich mit dem lokalen Konfigurationscode koppeln.
  - Optional: KICKERKASSE_AGENT_ALLOW_ALL_ORIGINS=1 nur als Notlösung setzen
    (Sicherheitsrisiko: erlaubt Zugriffe von beliebigen Websites)

Hinweis zu Abhängigkeiten:
  install_agent_service.py legt automatisch eine eigene, isolierte Python-Umgebung an
  und installiert die vom Agent benötigten Pakete (flask, pyserial) selbstständig.
  Ein manuelles "pip install" ist normalerweise nicht nötig. Voraussetzung ist lediglich
  das Python-Modul "venv" (auf Debian/Ubuntu ggf. via "sudo apt install python3-venv").

Installation (einmalig auf dem Kassen-PC):
------------------------------------------

Empfohlene Methode – grafischer Assistent:

  1. Doppelklick auf „Kickerkasse-Install.desktop" im Dateimanager
     ODER im Terminal ausführen:
       python3 setup_wizard.py

  2. Dem Assistenten folgen: Systemprüfung → Root-Rechte → Installation → Hardware-Test.

  3. Nach Abschluss läuft der Agent automatisch als systemd-Service und
     startet bei jedem Booten neu. Der Assistent zeigt den lokalen
     Konfigurationscode für den TopAdmin-Bereich an.

Alternative – Terminal (ohne grafischen Assistenten):

  sudo python3 install_agent_service.py

Status prüfen:
    systemctl status kickerkasse-agent
    curl http://127.0.0.1:8765/status

Adapterzuordnung für zwei Schubladen:
    /etc/default/kickerkasse-agent

    KICKERKASSE_MAIN_DRAWER_DEVICE=/dev/serial/by-id/...
    KICKERKASSE_SMALL_PARTS_DRAWER_DEVICE=/dev/serial/by-id/...

  Der Installer trägt angeschlossene Adapter beim ersten Lauf automatisch ein und
  überschreibt spätere Zuordnungen nicht. Empfohlen ist die Zuordnung auf dem
  Vereins-PC unter Admin → Einstellungen → Erweitert → Hardware-Service:

    1. Ggf. aktuellen Browser mit dem lokalen Konfigurationscode koppeln.
    2. Jeden Adapter über „Auswahl testen“ identifizieren.
    3. Hauptschublade und Kleinteile-Lager auswählen und lokal speichern.

  Der externe Server kann die USB-Geräte nicht sehen. Der Browser spricht direkt mit
  127.0.0.1:8765; Konfigurationscode und Zuordnung werden nicht auf dem Server gespeichert.

Schublade manuell öffnen:
    curl -X POST http://127.0.0.1:8765/openDrawer

Kleinteile-Lager manuell öffnen:
    curl -X POST http://127.0.0.1:8765/openDrawer/small_parts
