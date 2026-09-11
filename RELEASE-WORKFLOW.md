# Release-Workflow für KickerKasse

## Aufteilung der beiden Repositories

### Test-Repository

- `.github/workflows/ci.yml` verwenden.
- Den vorhandenen Test-Compose und die bestehende Portainer-Testanbindung beibehalten.
- Die Repository-Variable `OFFICIAL_RELEASES_ENABLED` nicht anlegen beziehungsweise auf `false` setzen.
- Keine offiziellen SemVer-Tags veröffentlichen.

### Offizielles Repository

- `.github/workflows/ci.yml` und `.github/workflows/release.yml` übernehmen.
- Unter `Settings → Secrets and variables → Actions → Variables` die Repository-Variable `OFFICIAL_RELEASES_ENABLED` mit dem Wert `true` anlegen.
- Unter `Settings → Actions → General → Workflow permissions` Schreibzugriff für den `GITHUB_TOKEN` erlauben.
- Nach dem ersten erfolgreichen Image-Push das GHCR-Paket in den Paketeinstellungen auf `Public` stellen.
- Branchschutz für `main` aktivieren und den CI-Workflow als erforderliche Prüfung festlegen.

## Einmalige Voraussetzungen

1. Das offizielle Repository muss die vollständigen Buildquellen enthalten.
2. Eine passende `LICENSE`-Datei muss festgelegt sein. Der Release-Workflow bricht ohne Lizenz bewusst ab.
3. `VERSION`, `frontend/package.json`, `frontend/package-lock.json`, `backend/main.py` und der Changelog müssen dieselbe Version nennen.
4. Der Paketname `ghcr.io/patrickn2282/kickerkasse` muss zum gewünschten GitHub-Konto passen.

## Release auslösen

Nach bestandener CI und abgeschlossenem Changelog:

```bash
git tag -a v2.6.7 -m "KickerKasse 2.6.7"
git push origin v2.6.7
```

Der Tag muss exakt zur Version in `VERSION` passen. Der Workflow prüft Frontend, Backend und Container erneut, veröffentlicht das versionsgebundene Image und erzeugt folgende Release-Dateien:

- `KickerKasse-2.6.7.zip`
- `KickerKasse-2.6.7.tar.gz`
- `SHA256SUMS`

## Portainer

Die bestehende Test-Stack-Anbindung kann weiter den Test-Branch und `docker-compose.yml` verwenden.

Für die offizielle Installation gibt es zwei Möglichkeiten:

1. Portainer weiterhin direkt an das offizielle Repository anbinden und dort die Release-Compose verwenden.
2. Den Stack aus dem heruntergeladenen Release-Paket erstellen und ausschließlich das veröffentlichte GHCR-Image beziehen.

Für reproduzierbare produktive Installationen sollte `KICKERKASSE_VERSION` auf eine konkrete Version gesetzt werden. Ein automatisches Update auf `latest` kann unerwartet Datenbankmigrationen starten und wird deshalb nicht empfohlen.
