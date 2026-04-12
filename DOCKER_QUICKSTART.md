# 🐳 Kassensoftware Docker - Anfänger-Anleitung

Diese Anleitung erklärt Schritt für Schritt, wie Sie die Kassensoftware mit Docker starten – auch wenn Sie noch nie Docker benutzt haben.

## 📋 Was ist Docker?

Docker ist ein Programm, das komplette Anwendungen mit allen ihren Abhängigkeiten in einem Container verpackt. Das bedeutet:
- ✅ Läuft auf jeden Computer (Windows, Mac, Linux)
- ✅ Kein kompliziertes manuelles Setup mehr
- ✅ "Funktioniert bei mir auch" - garantiert!
- ✅ Einfaches Starten und Stoppen

## 🎯 Was Sie brauchen

- Computer mit Windows, Mac oder Linux
- ~2 GB freier Speicherplatz
- Internet (für Docker Download)
- ~15 Minuten Zeit

## 🚀 Schritt 1: Docker installieren

### Auf Windows

1. Öffnen Sie https://www.docker.com/products/docker-desktop
2. Klicken Sie auf "Download for Windows"
3. Öffnen Sie die heruntergeladene Datei (Double-Click)
4. Folgen Sie dem Installer (alles mit Defaults ist ok)
5. Windows wird eventuell neu gestartet
6. Nach Neustart startet Docker automatisch

**Überprüfung:**
- Öffnen Sie PowerShell oder cmd
- Geben ein: `docker --version`
- Es sollte eine Versionsnummer erscheinen ✅

### Auf Mac

1. Öffnen Sie https://www.docker.com/products/docker-desktop
2. Klicken Sie auf "Download for Mac"
3. Öffnen Sie die heruntergeladene `.dmg` Datei
4. Ziehen Sie Docker.app in den Applications-Ordner
5. Öffnen Sie Applications und starten Sie Docker.app
6. Oben rechts sollte ein Docker-Icon erscheinen ✅

**Überprüfung:**
- Öffnen Sie Terminal
- Geben ein: `docker --version`

### Auf Linux (Ubuntu/Debian)

```bash
# Installation
sudo apt-get update
sudo apt-get install -y docker.io docker-compose

# Docker starten
sudo systemctl start docker

# Überprüfung
docker --version
docker-compose --version
```

## 📦 Schritt 2: Kassensoftware-Projekt vorbereiten

1. **Projekt-Ordner**: Sie sollten einen Ordner mit folgender Struktur haben:
   ```
   Kassensoftware/
   ├── backend/
   ├── frontend/
   ├── docker-compose.yml
   └── .env
   ```

2. **Dieser Ordner wird benötigt** - hätte ich erwähnen sollen, aber Sie haben ihn wahrscheinlich schon! 😊

## ⚙️ Schritt 3: Container starten

### Öffnen Sie Terminal/PowerShell

**Windows:**
- Rechtsklick auf den Kassensoftware-Ordner
- "Open PowerShell window here" wählen

**Mac/Linux:**
- Terminal öffnen
- `cd` zu Kassensoft ware-Ordner
  ```bash
  cd ~/Pfad/zu/Kassensoftware
  ```

### Container starten

```bash
docker-compose up -d
```

Das's it! 🎉

**Was passiert jetzt:**
- Docker lädt das PostgreSQL-Image herunter (~200MB)
- Docker lädt das Python-Image herunter (~300MB)
- Docker baut die Anwendung
- PostgreSQL-Datenbankstart
- FastAPI-Backend startet
- Alles ist bereit!

Erste Mal ~2-3 Minuten warten, später schneller.

## ✅ Schritt 4: Überprüfen Sie, dass alles läuft

```bash
docker-compose ps
```

Sie sollten sehen:
```
NAME                STATUS
kassensoftware-db   Up ...
kassensoftware-app  Up ...
```

Beide sollten "Up" und grün sein ✅

## 🌐 Schritt 5: App öffnen

1. **Öffnen Sie einen Browser** (Chrome, Firefox, Safari, Edge)
2. **Geben Sie in die Adressleiste ein:**
   ```
   http://localhost:8000
   ```
3. **Sie sollten sehen:** Login-Seite mit Kassensoftware Logo

## 🔑 Schritt 6: Login

Es gibt zwei vordefinierte Benutzer:

### Admin-Konto
- **Benutzer:** `admin`
- **Passwort:** `admin123`
- **Kann:** Alles machen (Nutzer, Produkte, etc.)

### Kassierer-Konto
- **Benutzer:** `Kasse1`
- **Passwort:** `Kasse1123`
- **Kann:** Nur verkaufen (Kasse bedienen)

Wählen Sie `admin` und viel Spaß! 🏪

## ⏹️ Schritt 7: Container stoppen

Wenn Sie fertig sind:

```bash
docker-compose down
```

Das stoppt alles ohne Daten zu löschen.

## 🚀 Schritt 8: Nächstes Mal starten

Die nächsten Male ist es noch einfacher:

```bash
docker-compose up -d
```

Nur 5-10 Sekunden und alles ist wieder am laufen!

## ℹ️ Häufige Fragen

### "Port 8000 wird schon verwendet"
Anderes Programm nutzt den Port. Entweder:
- Anderes Programm schließen, oder
- In `.env` Port ändern:
  ```
  ports:
    - "9000:8000"  # Dann localhost:9000 nutzen
  ```

### "Datenbank-Fehler, etwas ist kaputt"
Starten Sie mit fresh Database:
```bash
docker-compose down -v     # -v löscht auch die Datenbank
docker-compose up -d       # Neu mit fresh DB
```

### "Ich sehe Fehler in den Logs"
Logs anschauen:
```bash
docker-compose logs -f kassensoftware
```

### "App ist sehr langsam"
Erste Mal kann langsam sein. Warten Sie 30 Sekunden.

### "Wo sind meine Daten?"
Auf Ihrer Festplatte im Docker-Volume:
```
Windows: C:\ProgramData\Docker\volumes\
Mac/Linux: /var/lib/docker/volumes/
```

Daten bleiben auch wenn Container gestoppt ist!

### "Bilder/Uploads funktionieren nicht"
Die sind im `backend/uploads/` Ordner gespeichert.
Docker hat Zugriff - sollte funktionieren.

## 🛠️ Nützliche Befehle

```bash
# Status überprüfen
docker-compose ps

# Logs anschauen (live)
docker-compose logs -f

# In den Backend-Container gehen (Advanced)
docker-compose exec kassensoftware bash

# Alles includiv Volumes löschen (Warnung: Verliert Daten!)
docker-compose down -v

# Nur Logs anschauen (letzte 100 Zeilen)
docker-compose logs --tail=100
```

## 🎓 Weitere Infos

- Docker Anleitung: https://docs.docker.com/
- Kassensoftware Docs: [ARCHITECTURE.md](ARCHITECTURE.md)
- API Dokumentation: Öffnen Sie http://localhost:8000/docs

## ✨ Das war's!

Sie betreiben jetzt eine vollständige Kassensoftware mit:
- ✅ Web-Frontend (http://localhost:8000)
- ✅ REST API (http://localhost:8000/api)
- ✅ PostgreSQL Datenbank
- ✅ Automatische Backups durch Docker Volumes
- ✅ 100% produktionsreif!

Viel Erfolg! 🚀
