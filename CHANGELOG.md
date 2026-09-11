# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

This changelog retrospectively consolidates the repository's noisy early AI-assisted history
into meaningful release milestones. Historical tags `b0.9` and `b0.91` are treated as
pre-release markers for the `0.9.x` stabilization phase.

## [Unreleased]

### Added
- Ongoing changes should continue to use Conventional Commits so `feat` maps to `MINOR`,
  `fix` maps to `PATCH`, and `feat!` or `BREAKING CHANGE` maps to `MAJOR`.

## [2.7.0] - 2026-09-11

### Added
- Ein GitHub-CI-Workflow prüft Frontend, Backend und den Docker-Build bei Branch- und Pull-Request-Änderungen.
- Ein geschützter Release-Workflow veröffentlicht bei offiziellen SemVer-Tags ein versionsgebundenes Multi-Plattform-Image in GHCR, erzeugt einen Herkunftsnachweis und legt ein GitHub Release an.
- Eine getrennte Produktions-Compose bezieht das veröffentlichte Image und hält Datenbank sowie Uploads in stabilen Docker-Volumes.
- Plattformbezogene Installations- und Updateskripte erzeugen lokale Geheimnisse, erhalten bestehende Konfigurationen und aktualisieren auf die Paketversion.
- Ein Paketgenerator erstellt aus einer festen Positivliste blanke ZIP- und TAR.GZ-Installationspakete samt SHA-256-Prüfsummen.
- `RELEASE-WORKFLOW.md` dokumentiert die Aufteilung zwischen Test- und offiziellem Repository sowie die Einrichtung in GitHub und Portainer.

### Changed
- Docker-Buildkontexte schließen Tests, Workflow-, Release- und Dokumentationsdateien aus.

### Validation
- Workflow-YAML, Release-Compose, PowerShell-, Shell- und Python-Skripte syntaktisch erfolgreich geprüft.
- Blanko-Pakete für Version 2.7.0 erzeugt; die Archive enthalten ausschließlich die vorgesehene Positivliste und keine Tests, Git-Dateien, echte `.env`, Abhängigkeiten oder Nutzerdaten.
- 14 Frontend-Tests, 2 gezielte Backend-Tests, ESLint und lokaler Docker-Produktionsbuild erfolgreich.
- Die vollständige GitHub-Ausführung einschließlich der gesamten Backend-Suite, Multi-Plattform-Build, GHCR-Push und GitHub Release ist erst nach Übernahme in das offizielle Repository möglich.

## [2.6.6] - 2026-09-11

### Added
- Der Erst-Start-Assistent fragt nun die App-Überschrift ab und schlägt bei einer frischen Installation „KickerKasse“ vor.

### Changed
- Der zentrale Standardwert für die App-Überschrift lautet bei neuen Installationen „KickerKasse“. Bereits gespeicherte Bezeichnungen bleiben erhalten.
- „Alles Wichtige an einem Ort“ steht nun platzsparend als Überschrift im Kopf des Hilfe- und Informationsfensters.
- Funktionsübersicht sowie Projekt-, Kontakt- und Versionsinformationen sind kompakter angeordnet.

### Validation
- 14 Frontend-Tests und 2 gezielte Backend-Tests erfolgreich; Frontend-Produktionsbuild, ESLint und Python-Kompilierung erfolgreich.
- Docker-Image neu gebaut; Anwendungs- und Datenbankcontainer sind gesund und OpenAPI meldet Version 2.6.6.

## [2.6.5] - 2026-09-11

### Changed
- Im Fenster „Hilfe & Informationen“ steht der Bereich „Projekt & Kontakt“ nun vor „Alles Wichtige an einem Ort“.
- Der Hinweis zur fehlenden TSE- und Revisionssicherheit befindet sich im festen Dialogfooter und bleibt in Übersicht und Funktionsdetails sichtbar.

### Fixed
- Die gemeinsame Zugangsdatenabfrage liegt zuverlässig über dem global auf Ebene 3000 angehobenen Kassenabschluss und ist dadurch bedienbar.
- Die Mitgliedersuche in der Kasse wird beim Öffnen, Schließen und nach einer Auswahl geleert. Beim nächsten Öffnen erhält das Suchfeld weiterhin automatisch den Fokus.

### Validation
- 14 Frontend-Tests, Frontend-Produktionsbuild und ESLint-Prüfung erfolgreich.
- Die visuelle Browserprüfung konnte ohne laufendes Backend nicht abgeschlossen und das Docker-Image nicht aktualisiert werden, weil Docker Desktop auf dem Testsystem derzeit nicht startet.

## [2.6.4] - 2026-09-10

### Added
- Aktive Artikel besitzen ein eigenes Kennzeichen „In der Kasse anzeigen“. Ausgeblendete Artikel bleiben mit Bestand, Kategorien und Historie in der Produktverwaltung und in Berichten erhalten.
- Die Artikelsichtbarkeit wird beim Stammdatenexport mitgeführt. Ältere Importdateien ohne dieses Feld bleiben kompatibel und importieren Artikel standardmäßig sichtbar.

### Changed
- „Zuletzt gebucht“ zeigt den vollständigen Warenwert vor Guthaben- und Gutscheinverrechnung sowie die beteiligten Zahlungsarten, beispielsweise „Gutschein + Guthaben + Bar“.
- Die Kategoriezuordnung im Produktformular verwendet dieselbe vollständig sichtbare Schalterdarstellung wie die übrigen Produktoptionen.

### Validation
- 14 Frontend-Tests und 5 gezielte Backend-Tests erfolgreich; Frontend-Produktionsbuild, ESLint und Python-Kompilierung erfolgreich.
- Docker-Image erfolgreich neu gebaut. Anwendungs- und Datenbankcontainer sind gesund, die Migration `product_kasse_visibility` wurde angewendet und OpenAPI meldet Version 2.6.4.

## [2.6.3] - 2026-09-10

### Changed
- Trinkgeld wird in der aktuellen Kassenberichtsliste, der Transaktionshistorie sowie in HTML-, CSV- und PDF-Exporten als eigener Betrag ausgewiesen.
- Die Vorbereitung von Gutscheinen und Verzehrkarten bleibt über Gutscheinbestand, Gutscheinkonto und Audit-Log nachvollziehbar, erzeugt aber keine Null-Euro-Verkaufstransaktion und keine Belegnummer mehr. Vorhandene alte Vorbereitungszeilen werden aus Transaktionslisten und neuen Kassenberichten ausgeblendet.

### Fixed
- Vollständig mit Mitgliedsguthaben bezahlte Verkäufe bestätigen gegenüber dem Server korrekt einen Restzahlbetrag von 0 Euro und lösen dadurch keinen falschen Preis-/Guthabenkonflikt mehr aus.
- Eindeutige HTTP-409-Ablehnungen werden nicht mehr als ungeklärte Buchung gespeichert. Nach einer serverseitigen Aktualisierung kann der korrigierte Verkauf unmittelbar erneut bestätigt werden.

### Validation
- 12 Frontend-Tests und 8 gezielte Backend-Tests erfolgreich; Frontend-Produktionsbuild und ESLint-Prüfung erfolgreich.
- Docker-Image erfolgreich neu gebaut; Anwendungs- und Datenbankcontainer sind gesund und OpenAPI meldet Version 2.6.3.
- Die vollständige Backend-Suite wurde zusätzlich ausgeführt: 278 Tests bestanden, 101 wurden übersprungen und 167 schlugen fehl. Der überwiegende Fehlergrund sind ältere HTTP-Test-Fixtures ohne den inzwischen verpflichtenden TopAdmin; sie werden bereits von der Ersteinrichtungssperre mit HTTP 401 abgewiesen. Die 8 für diese Änderung maßgeblichen Backend-Tests sind erfolgreich.

## [2.6.2] - 2026-09-09

### Fixed
- TopAdmins können das aktuelle Installationspaket für den lokalen Hardware-Service jederzeit unter „Einstellungen → Erweitert → Hardware-Service“ öffnen und herunterladen. Die Updatefunktion bleibt auch sichtbar, wenn ein alter oder aktueller Agent bereits erreichbar ist.
- Die Installationshilfe beschreibt den Updateablauf und weist darauf hin, dass Adapterzuordnung und lokaler Konfigurationscode bei einer erneuten Installation erhalten bleiben.

### Validation
- Frontend-Produktionsbuild und ESLint-Prüfung erfolgreich.

## [2.6.1] - 2026-09-09

### Fixed
- Während der Passwortbestätigung für eine Guthabenaufladung wird das Mitgliedsfenster ausgeblendet. Der Zugangsdaten-Dialog bleibt dadurch vollständig bedienbar; nach einem Abbruch erscheint das Mitgliedsfenster mit den erhaltenen Eingaben wieder.

### Validation
- Frontend-Produktionsbuild und ESLint-Prüfung erfolgreich.
- Docker-Image neu gebaut; Anwendungs- und Datenbankcontainer sind gesund und OpenAPI meldet Version 2.6.1.

## [2.6.0] - 2026-09-09

### Added
- Bareinlagen einschließlich der initialen Geldübernahme erscheinen mit ihrer gemeinsamen fortlaufenden Belegnummer in der Transaktionsliste; der Erstbestand wird dort als „Kassenstart / Geldübernahme“ bezeichnet.
- Bei Rollenvergabe im Mitgliedsformular wird das Passwort jetzt durch eine zweite Eingabe bestätigt. Abschöpfungen erlauben einen frei eingegebenen Namen, während TopAdmin aus der Vorschlagsliste entfernt ist.
- Kassenbericht, Lagerwarnung und Datenbanksicherung besitzen jeweils einen eigenen Betreff-Zusatz. Ihre Betreffe folgen nun einheitlich „Kassentitel - Funktion Datum Uhrzeit - Info“.

### Changed
- E-Mail-Einstellungen sind nach SMTP, Kassenbericht, Warenbestand und Datenbanksicherung gruppiert. Versand- und Kassenbericht-Automatik stehen am Anfang der SMTP-Konfiguration.
- Mitgliedsauswahlen beginnen mit Fokus im Suchfeld. Passwortfelder neuer Benutzer stehen untereinander, Kategorie- und Artikelzuordnung verwenden kompakte, deckende Schalter. Die Artikelzuordnung nutzt dieselbe Schalterdarstellung wie die übrigen Artikeloptionen.
- Kassenberichte können auch bei einer Differenz ohne Begründung erstellt werden; die Begründung bleibt als optionale Berichtsinformation verfügbar.
- Gutscheinfreigaben fragen ausschließlich die Zugangsdaten des angemeldeten, für die Aktion berechtigten Benutzers ab. Der Login zeigt den konfigurierten Kassentitel und keinen manuellen TopAdmin-Reset-Hinweis mehr.
- Die Anzeige „Zuletzt gebucht“ ist kompakt und bei Bedarf aufklappbar. Passwortbestätigungen bleiben beim Klick außerhalb des Dialogs geöffnet.
- Der gemeinsame Zugangsdaten-Dialog wird in die oberste Dokumentebene gerendert; dadurch bleibt die Passwortabfrage zur Guthabenaufladung vor dem geöffneten Mitgliedsfenster bedienbar.

### Fixed
- „Jetzt aktualisieren“ lädt die Anwendung nach Aktivierung des Service Workers zuverlässig neu, auch wenn der Browser kein `controllerchange`-Ereignis sendet.
- `CATEGORIES_UPDATED` wird im Audit-Log als „Kategorien geändert“ dargestellt.
- Verzehrkartenartikel sind aus Bestandskorrekturen entfernt; der Server weist direkte Korrekturversuche ebenfalls ab, damit Verzehrkarten nur mit fortlaufender Nummer im Gutscheinbereich entstehen.
- Manager können Geschenk-Gutscheine mit ihrem eigenen Passwort bestätigen; abweichende Benutzernamen werden im Dialog nicht mehr angeboten.

### Validation
- Frontend-Produktionsbuild und Python-Kompilierung erfolgreich; ESLint ohne Fehler (bestehende Formatwarnungen bleiben).
- Docker-Image erfolgreich neu gebaut. Die versionierte 2.6.0-Migration lief durch, beide Container sind gesund und OpenAPI meldet Version 2.6.0.
- Im Browser lädt „Jetzt aktualisieren“ die neue Oberfläche und entfernt den Updatehinweis; der konfigurierte Kassentitel ist auf der Loginseite sichtbar.
- Die drei Betreffvarianten wurden mit fester Berliner Zeit gegen das Zielformat geprüft. Der vorhandene initiale Kassenbestand wird lesend als `CASH_DEPOSIT` mit Belegnummer 1 geliefert.

### Migration
- Drei optionale Felder in `app_settings` speichern die getrennten Betreff-Infos für Kassenbericht, Lagerwarnung und Datenbanksicherung.

## [2.5.2] - 2026-09-09

### Fixed
- Die paginierte Gästeliste und ihr Produktfilter registrieren jetzt auch die vom API-Middlewarevertrag verwendeten Pfade mit abschließendem Schrägstrich. Eine frische Installation liefert dadurch eine erfolgreiche leere Liste anstelle von HTTP 404 „Not Found“.

### Validation
- Der Ausgangszustand wurde am laufenden Container bestätigt: `guest_list_entries` enthielt null Datensätze, während `/api/guest-list/entries-page/` und `/api/guest-list/products/` jeweils HTTP 404 lieferten.
- Container erfolgreich neu gebaut und gesund gestartet. Die authentifizierten Endpunkte liefern nun HTTP 200 mit `entries=[]`, `total=0`, `total_pages=0` beziehungsweise einer leeren Produktliste; dadurch greift der vorhandene UI-Leerzustand.

## [2.5.1] - 2026-09-09

### Fixed
- Ein frischer Datenbestand erzwingt den Erststart-Assistenten jetzt vor jeder bestehenden Sitzung und vor der Kassen-Direktanmeldung. Alte, mit demselben Entwicklungsschlüssel signierte Browsercookies können dadurch nicht mehr direkt die Kassenansicht öffnen.
- Der globale Router prüft den Setup-Status vor der Sitzungswiederherstellung und leitet bei fehlendem TopAdmin unabhängig von der aufgerufenen Route zum nicht schließbaren Setup weiter.
- Das automatisch erzeugte Kassenkonto erhält vor Abschluss der Ersteinrichtung eine zufällige Sitzungsfassung, sodass Cookies einer früheren Installation auch bei erneut vergebener Benutzer-ID ungültig bleiben.

### Validation
- Ursache am frisch erzeugten PostgreSQL-Volume nachvollzogen: nur Benutzer `Kasse`, kein TopAdmin und korrekter Backendstatus `setup_required=true`; gleichzeitig wurde ein altes Cookie als Benutzer-ID 1 akzeptiert.
- Container erfolgreich neu gebaut und gesund gestartet. Kassen-Direktanmeldung ohne TopAdmin liefert HTTP 409, ein nachgebildetes altes Kassen-Cookie HTTP 401. Die Browserprüfung öffnet `/login` mit dem nicht schließbaren Initial-Setup-Assistenten und Version 2.5.1.

## [2.5.0] - 2026-09-09

### Added
- Etappe 22 / Punkte 28 und 29: Kompakte Bereichsauswahl für die Verwaltung auf kleinen Displays, einzeilige mobile Hauptnavigation und priorisierte Mitgliederspalten mit direkt erreichbarem Guthaben und Bearbeiten.
- Gemeinsamer Dialog-Fokusvertrag mit Anfangsfokus, Tab-Fokusbindung, Fokusrückgabe und geregelter Escape-Behandlung. Zahlungsdialoge bleiben während der Buchung gesperrt; Mitglieds- und Produktdialog warnen vor dem Verwerfen ungespeicherter Formwerte.
- Meldungen verwenden Live-Regionen und benannte Schließen-Aktionen. Zentrale Fokusmarkierungen sowie Mindestgrößen für mobile Schaltflächen verbessern Tastatur- und Touchbedienung.
- Etappe 23 / Punkte 30 bis 32: Gemeinsame semantische Farben für Haupt-, Neben- und Gefahrenaktionen, sichtbarer Speicherzustand in Einstellungen sowie beschriftete Speicheraktionen und native, per Tastatur bedienbare Schalter.

### Changed
- Begriffe wurden auf „Verwaltung“, „Hilfe & Informationen“, „Anmelden/Abmelden“, „Kassenbericht“, „Verzehrkarte“, „Buchungszeitraum“, „Hintergrund“ und deutsche Währungsdarstellung vereinheitlicht. Die Belastung des Gutscheinkontos wird korrekt bei Gutscheinerstellung erklärt.
- Produktbilder werden bei Bearbeitung erst nach erfolgreich gespeicherten Stammdaten übertragen; ein Bildfehler benennt den bereits gespeicherten Teil ausdrücklich. Strukturierte API-Fehler werden in weiteren Verwaltungsbereichen über den gemeinsamen Fehlerparser angezeigt.
- Etappe 24 / Punkt 41: Unbenutzte Einstellungs-, Z-Bon- und Hardware-Dubletten entfernt. Alte Analyse- und Roadmapdateien sind als historische Dokumente gekennzeichnet; README beschreibt die tatsächlich auswählbaren Kassenansichten und die aktuelle Testumgebung.

### Validation deferred
- Die gemeinsame Prüfung für 390 × 844, 768 × 1024 und 1280 × 800, Tastatur/Fokus, Kontrast, Formularzustände, Frontendtests, Build/Lint sowie Docker-/PostgreSQL-Abnahme ist in der Projektprüfung hinterlegt. **Keine Tests, Builds, Lint-, Docker- oder Browserprüfungen ausgeführt.** Etappen 14–24 bleiben bis zum Abschlusslauf technisch unbestätigt.

## [2.4.0] - 2026-09-08

### Added
- Etappe 20 / Punkte 33 und 27: Serverseitige Suche, Zeitraum-/Typ-/Produktfilter, Trefferzahlen und Pagination für Gäste- und Materiallisten. Gefilterte Materialmengen und -werte beziehen sich auf die gesamte Auswahl; Ladefehler sind vom leeren Ergebnis getrennt und direkt wiederholbar.
- Serverseitiger Gutschein-Gesamtexport für die aktuelle Typ-/Statusauswahl mit Anfangs- und Restwert, Status, Grund/Beschreibung sowie Verkaufs- und Einlösungszeitpunkt, Benutzer und Beleg. UTF-8-BOM, vollständige CSV-Quotierung und Formelprävention schützen Umlaute, Trennzeichen, Anführungszeichen und freie Texte.
- Etappe 21 / Punkt 34: Aktivstatusfilter, verständliche Deaktivierung und Reaktivierung von Produkten. Kategorien werden in der Produktliste gezeigt und können von Admin/TopAdmin direkt im Produktdialog zugeordnet werden.

### Changed
- Produktpflege erklärt die fachliche Trennung: Kategorien steuern die Kassenanzeige, Warengruppen dienen Berichten. Manager behalten Bearbeitungs- und Aktivierungsrechte; Kategoriezuordnungen bleiben Admin/TopAdmin vorbehalten.
- Listen übertragen pro Aufruf höchstens 100 Datensätze. Der Gutscheinexport ist von der sichtbaren Tabellenseite unabhängig und kündigt die Zahl der exportierten Treffer an.

### Validation deferred
- `backend/tests/test_stage2021_lists_exports_products.py` sowie gemeinsame Browser-, Rollen-, CSV-, PostgreSQL-, Build- und Lint-Abnahme sind nur hinterlegt. **Keine Tests, Builds, Lint-, Docker- oder Browserprüfungen ausgeführt.** Etappen 14–21 bleiben bis zum gemeinsamen Abschlusslauf technisch unbestätigt.

## [2.3.0] - 2026-09-08

### Added
- Etappe 18 / Aufgabe 25: Nach erfolgreichem Verkauf oder Deckelvorgang nennt eine dauerhaftere Warnung jedes nicht geöffnete Hardwareziel und weist auf die manuelle Prüfung statt einer erneuten Buchung hin. Hardwarezustände sind zusätzlich als Text beschriftet.
- Etappe 19 / Aufgabe 26: Lagerwarnungen erhalten einen unabhängigen täglichen Schedulerjob mit eigener Prüfzeit und funktionieren ohne aktivierten Kassenbericht-Zeitplan.
- Letzter Zeitpunkt, Status und Meldung der automatischen Kassenbericht- und Lagerläufe werden dauerhaft gespeichert und in der E-Mail-Konfiguration angezeigt; der Berichtstag des Vortags ist ausdrücklich sichtbar.

### Changed
- Die automatische Kassenberichtserstellung bestimmt den Vortag anhand der konfigurierten Anwendungszeitzone. Ein Lauf ohne kritische Lagerbestände wird als nachvollziehbarer Prüflauf ohne erforderliche Mail festgehalten.
- Migration 2.3.0 ergänzt die Lagerprüfzeit und persistenten Versandstatus in `app_settings`.

### Validation deferred
- `backend/tests/test_stage19_mail_automation.py`, `frontend/tests/hardware-feedback.test.js` und die manuelle Hardware-, Scheduler-, Mail- und Browserabnahme sind nur hinterlegt. **Keine Tests, Builds, Lint-, Docker-, Hardware-, Mail- oder Browserprüfungen ausgeführt.** Etappen 14–19 bleiben bis zum gemeinsamen Abschlusslauf technisch unbestätigt.

## [2.2.0] - 2026-09-08

### Added
- Etappe 17 / Aufgaben 24 und 35: Benutzergebundene Kassenentwürfe überstehen Reload, Sitzungsunterbrechung und Benutzerwechsel. PWA-Updates warten auf einen leeren Bon; der Session-Timer warnt und schützt offene Vorgänge.
- Der letzte serverbestätigte Verkauf bleibt mit endgültiger Belegnummer, Betrag, gegebenem Bargeld und Rückgeld sichtbar.
- Verkauf bestätigt den angezeigten Preis- und Guthabenstand. Änderungen führen vor jeder Buchung zu HTTP 409, aktualisieren die Anzeige und verlangen eine erneute Bestätigung.

### Fixed
- Frische Installationen erreichen den Initial-Setup-Dialog wieder: Der Router beendet beim Seitenstart keine Serversitzung mehr, die Anwendung rendert auch bei zunächst fehlenden öffentlichen Einstellungen, und ein leerer Datenbestand prüft den TopAdmin unabhängig von optionalen E-Mail-Einstellungen.
- Fehler beim Setup-Status gelten nicht länger fälschlich als „TopAdmin vorhanden“; begrenzte Wiederholung und eine sichtbare manuelle Wiederholung halten den Erststart erreichbar.

### Validation deferred
- `backend/tests/test_stage17_reliability.py` sowie die manuelle Browser-, PWA-, Sitzungs- und PostgreSQL-Abnahme sind nur hinterlegt. **Keine Tests, Builds, Lint-, Docker- oder Browserprüfungen ausgeführt.** Etappen 14–17 bleiben bis zum gemeinsamen Abschlusslauf technisch unbestätigt.

## [2.1.0] - 2026-09-08

### Added
- Etappe 16 / Aufgaben 21 und 22: Zeilenweise Importvorschau mit Konflikten, Quellmodus „fremd“/„gleiche Installation“ und ausdrücklicher Bestätigung neuer Anfangsguthaben/-bestände.
- Versionierter CSV-Vertrag 2 mit sämtlichen fachlichen Produktfeldern, Archivstatus, verlustfreier Kategoriezuordnung als JSON-Liste sowie getrenntem Haupt-/Originalbildtransfer einschließlich AVIF. Legacy-CSV bleibt lesbar.

### Fixed
- Fremde technische IDs überschreiben keine vorhandenen Datensätze. Bestehende Guthaben/Bestände, verknüpfte Konten und Archivstatus werden geschützt; ersetzende Importe berücksichtigen alle modellierten Fremdschlüssel einschließlich Deckel, Gäste und Konten.
- Aktuelle Konfliktprüfung unter Wartungs-/Datenbanksperre; Daten, vorbereitete Medien und Abschlussaudit teilen eine Transaktionsgrenze. Wiederanlaufjournal unterstützt jetzt auch Importvorgänge.
- Größen-/Entpackgrenzen, doppelte Quellschlüssel, ungültige Pfade/Spalten/Versionen, fehlende Kategorien und doppelte Bildvarianten werden abgewiesen. Alte Medien werden vor dem Schreiben neu zugeordneter IDs aus der vorbereiteten Kopie entfernt.
- Import ist TopAdmin vorbehalten; Analyse/Export bleiben für Admin verfügbar. Der Dialog sperrt veraltete Vorschauen und Eingaben während laufender Anfragen.

### Validation deferred
- `backend/tests/test_stage16_transfer.py` und gemeinsame manuelle/PostgreSQL-Abnahmeschritte nur hinterlegt. **Keine Tests, Builds, Lint-, Docker- oder Browserprüfungen ausgeführt.** Technische und persönliche Abnahme offen; keine laufende Anwendung aktualisiert.

## [2.0.0] - 2026-09-08

### Changed
- Etappe 15 / Aufgabe 23: Vollständige Sicherung v2 enthält Datenbank, Migrations-/Schemamanifest, Zeilenanzahlen, SHA-256-Prüfsummen und alle Upload-Medien. Datenbanktabellen werden während der Aufnahme gegen Schreibzugriffe gesperrt.
- **BREAKING:** Restore akzeptiert ausschließlich vollständige v2-Archive mit passendem Schema. v1- und Teilarchive werden vor dem Ersetzen abgewiesen. Alte Sicherungen zunächst mit der zugehörigen alten Anwendung in einer isolierten Instanz einspielen, diese aktualisieren und dort neu als v2 exportieren. Fehlende alte Medien müssen aus einer separaten Mediensicherung ergänzt werden.
- Prozessübergreifende Wartungssperre für API-Zugriffe und Sicherung; andere Zugriffe erhalten während der Umschaltung HTTP 503 mit Wiederholungshinweis. Der Export beginnt nur in einer Zugriffspause.
- Restore prüft Format, Dateipfade, Vollständigkeit, Prüfsummen, Spalten und Fremdschlüssel sowie Datentypen und Datenbankregeln in temporären PostgreSQL-Tabellen vor TRUNCATE. Größenlimits: 256 MiB ZIP, 512 MiB entpackt, 128 MiB JSON und 10.000 Dateien.
- Medien werden vorbereitet und bei Fehlern zurückgesetzt. Ein persistentes Journal und ein Auditmarker ordnen beim Neustart die richtige Mediengeneration zu. Das Upload-Mount-Verzeichnis bleibt bestehen.
- Restore-Audit ist Bestandteil des Datenbank-Commits; vorhandene Sessions und unbenutzte Passwort-Resetlinks werden ungültig. Oberfläche und Dokumentation erklären Format und Neuanmeldung.

### Validation deferred
- Auf ausdrücklichen Nutzerwunsch **keine Tests, Builds, Lint- oder Live-Prüfungen ausgeführt**. Regressionstests in `backend/tests/test_stage15_backup.py` und gemeinsame Abnahmeschritte in der Projektprüfung hinterlegt. Technische Freigabe offen.

## [1.6.15] - 2026-09-08

### Fixed
- Etappe 14 / Aufgabe 37: Wesentliche Produkt-, Mitglieder-, Benutzer-, Kategorie-, Gutschein- und Einstellungsänderungen werden gemeinsam mit ihren Audit-Einträgen bestätigt. Verschachtelte Repository-Commits werden bis zum erfolgreichen Abschluss zurückgestellt; Auditfehler rollen die Änderungen zurück.
- Verknüpfte Mitgliedskonten, Rollenwechsel, Empfängeränderungen, Guthaben-/Bestandskorrekturen und Kategoriezuordnungen werden nachvollziehbar protokolliert. Passwortwechsel erhalten einen Änderungsvermerk; geheime Werte werden zentral auch in verschachtelten Auditdaten entfernt.
- Bild-/Originalbildänderungen und Löschungen erhalten Audit-Einträge; bei Fehlern werden die vorherigen Medien zurückgesetzt. Optionale Export-/Analyse-/Fehlerprotokolle melden Auditfehler im Serverlog.
- Der Datenbankteil des Stammdatenimports einschließlich Abschlussaudit erhält eine gemeinsame Transaktion; die fachliche Import- und Medienvalidierung bleibt Etappe 16.

### Validation deferred
- Regressionstests in `backend/tests/test_stage14_audit.py` nur hinterlegt, **nicht ausgeführt**. Technische und persönliche Abnahme offen.

## [1.6.14] - 2026-09-08

### Fixed
- Etappe 13 / Punkte 36 und 05: Neue Verkaufspositionen speichern Produktname, Warengruppe, Kategorie, Steuersatz und internen Materialwert zum Buchungszeitpunkt. Verkauf und Deckelzahlung verwenden dieselbe Snapshot-Erzeugung. Auswertungen übernehmen gespeicherte Produkt-, Kunden- und Akteursdaten; spätere Umbenennungen, Umgruppierungen oder Preisänderungen ändern diese historischen Merkmale nicht.
- Ältere Positionen ohne ausreichende Merkmale werden als Altbestand mit unbekannter Zuordnung gekennzeichnet. Migration 1.6.14 erfindet keine historischen Produkt-/Steuerdaten und verändert keine archivierten Berichte. Aufladungen erhalten eine von der aktuellen Mitgliedsreferenz unabhängige Buchungsart.
- Mitglieder werden über den bisherigen Löschweg archiviert. Guthaben muss vorher fachlich geklärt sein; Belege, Guthaben-/Korrekturlogs, Gästereferenzen und Fotos bleiben erhalten. Archiv und verknüpfter Kontozustand werden mit dem Audit atomar gespeichert. Verknüpfte Zugänge werden deaktiviert und ihre Sitzungen widerrufen.
- Archivierte Mitglieder sind aus aktiven Auswahllisten und neuen Mitgliedsbuchungen ausgeschlossen. Die Mitgliederverwaltung bietet Archivansicht und Wiederherstellung. Wiederherstellung aktiviert keinen deaktivierten Zugang automatisch; Mitglieder mit Systemzugang bleiben dem Top-Admin vorbehalten.

### Notes
- Frontend und Backend gemeinsam auf 1.6.14 aktualisieren. Mitgliedsnummern bleiben auch im Archiv belegt. Archivierung ist keine Guthabenauszahlung und keine Datenlöschung. Bestehende Z-Bon-Archive bleiben unverändert. Etappe 10 bleibt zurückgestellt.

## [1.6.13] - 2026-09-07

### Fixed
- Etappe 12 / Punkt 11: Buchungen erhalten im Frontend eine benutzerbezogene Vorgangskennung. Nach einem unklaren Verbindungsabbruch wird vor der Wiederholung der gespeicherte Status geprüft. Parallele identische Anfragen erzeugen nur eine Buchung; abweichender Inhalt wird abgewiesen.
- Buchung und serialisierte Antwort werden innerhalb derselben Datenbanktransaktion bestätigt. Erfasst sind Verkauf, Guthabenaufladung, Deckelanlage/-ergänzung/-zahlung, Gutscheinwege, Bareinlage/-entnahme und Z-Bon. Fehler beim Antwortjournal rollen auch die Buchung zurück. Bestätigte Ergebnisse bleiben über eine benutzergebundene Statusabfrage abrufbar.
- Die Oberfläche zeigt ungeklärte Vorgänge mit Statusprüfung. Schlüssel und Inhaltsprüfsummen überstehen das Neuladen desselben Tabs; Passwörter und Buchungsinhalte werden nicht lokal gespeichert. Wiederhergestellte Bestätigungen öffnen die Schublade nicht erneut. Z-Bon-Mailversand erfolgt erst nach dem Commit und wird bei einer Wiederholung nicht erneut ausgelöst.

### Notes
- Migration 1.6.13 ergänzt `booking_operations`. Frontend und Backend gemeinsam aktualisieren. Die lokale Wiederaufnahme gilt für denselben Browser-Tab und Benutzer. Etappe 10 bleibt ausdrücklich zurückgestellt.

## [1.6.12] - 2026-09-07

### Fixed
- Etappe 11 / Punkte 19 und 10: Ersteller und prüfendes Mitglied werden anhand gültiger IDs aufgelöst; der Bericht speichert die serverseitigen Namen. Unzulässige Ersteller, ungültige Stückelungen, negative/gebrochene Stückzahlen, nicht endliche Beträge und widersprüchliche Zählsummen werden abgewiesen. Zählbestand und Differenz werden in Cent berechnet; Abweichungen erfordern eine Begründung.
- Ein gemeinsamer transaktionaler Datenbankzähler vergibt Belegnummern für Verkäufe und Bareinträge. Die Vorschau verbraucht keine Nummer und ist als vorläufig gekennzeichnet.
- Abschluss und Buchungen werden koordiniert; jede berücksichtigte Transaktion und jeder Bareintrag erhält eine feste Z-Bon-Zuordnung. Verspätet bestätigte Buchungen mit älterem Zeitstempel bleiben dadurch für den nächsten Abschluss sichtbar.

### Notes
- Migration 1.6.12 ergänzt Zähler und Abschlussreferenzen. Bestehende Belegnummern sowie unveränderliche Berichte bleiben erhalten; historische Zuordnungen folgen den bisherigen Abschlussgrenzen.

## [1.6.11] - 2026-09-07

### Fixed
- Etappe 9 / Punkt 20: Gäste werden je Verkaufsposition übermittelt, serverseitig gegen Gastpflicht, Anzahl und Mitgliedsreferenz geprüft und gemeinsam mit Verkauf, Zahlung und Bestand gespeichert. Der Server vergibt Beleg- und Positionszuordnung; frei übermittelte Belegreferenzen werden abgewiesen. Der alte separate Schreibendpunkt verweist mit HTTP 409 auf den gemeinsamen Verkaufsweg.
- Variable Gastartikel fragen zuerst den Preis und danach den Namen ab. Gastnamen erscheinen im Bon und in der Zahlungsübersicht. Eine Mengenerhöhung fordert neue Angaben an; Entfernen einer Position entfernt deren Gäste. Fehlgeschlagene Buchungen erhalten Bon und Namen. Verschiedene variable Preise werden in getrennten Positionen geführt.
- Bestandsprüfung und Abzug berücksichtigen die Gesamtmenge je Produkt auch bei mehreren Gast-/Preispositionen im selben Bon. Fehler im Verkaufsablauf rollen ausstehende Änderungen zurück.

### Notes
- Migration 1.6.11 ergänzt die Belegpositionsreferenz an Gästen. Historische Einträge bleiben erhalten und werden nicht nachträglich erfundenen Positionen zugeordnet. Frontend und Backend gemeinsam aktualisieren; alte Kassenansichten neu laden.

## [1.6.10] - 2026-09-07

### Fixed
- Etappe 8 / Punkte 08 und 13: Gutscheincodes am Beleg verwenden ein Textfeld. Neue Einlösungen erhalten eine separate Zuordnung mit Gutschein-ID, Code, Beleg und Teilbetrag; mehrere Gutscheine und wiederholte Teileinlösungen bleiben nachvollziehbar. Doppelte Angaben desselben Gutscheins einschließlich Nummer-/Codealias werden abgewiesen; verwendete Gutscheine werden in stabiler Reihenfolge gesperrt.
- Geschenkgutschein und Verzehrkartenserie speichern Gutscheine, Erstellungsbeleg, gegebenenfalls Kontobewegung, Produktbestand und Audit gemeinsam. Fehler hinterlassen keine Teilserie. Parallele Serien teilen einen transaktionsgebundenen Nummernvergabeschutz; bestehende Verzehrkartenprodukte werden unter Zeilensperre aktualisiert.

### Notes
- Migration 1.6.10 erweitert das Belegfeld und ergänzt `voucher_redemptions`. Historische Codes werden erhalten; frühere Einlösungsbeträge werden nicht aus unvollständigen Daten rekonstruiert. Die globale Belegnummernvergabe bleibt Aufgabe 10.

## [1.6.9] - 2026-09-07

### Fixed
- Etappe 7 / Punkte 03 und 12: Deckelabrechnung sperrt den Deckel und speichert Verkauf, Bestand, Materialkonto, Audit und Schließen gemeinsam. Fehler oder unzureichender Bestand hinterlassen den ursprünglichen Deckel. Eine erneute Abrechnung desselben Deckels erzeugt keine weitere Zahlung.
- Deckel bleiben Barvorgänge ohne Mitgliedsauswahl, Gäste oder Verzehrkarten. Die Oberfläche erklärt und prüft diese Grenzen; die API lehnt nicht unterstützte Zusatzfelder sowie Gast-/Kartenartikel ab. Reguläre Preise, variable Eingaben und internes Material bleiben unterstützt; gespeicherte Verkaufspreise werden beim Bezahlen erhalten. Nicht unterstützte alte Deckel werden zur fachlichen Klärung abgewiesen.
- Anlegen und Ergänzen eines Deckels verhindern gleichzeitiges mehrfaches Absenden in der Oberfläche. Produktzeilen werden für Reservierungen und Abrechnung gesperrt.

### Added
- Regressionen für vollständige Rollbacks, Gast-/Belegzuordnung, Mehrfacheinlösung und PostgreSQL-Parallelität sowie ein Frontendtest für Bonerhalt nach fehlgeschlagener Buchung. Aufgabenliste und persönliche Live-Test-Schritte fortgeführt.

### Notes
- Drei PATCH-Schritte zur Korrektur bestehender Buchungsregeln; gemeinsamer auslieferbarer Stand ist 1.6.11. Stornos bleiben außerhalb des Umfangs. Allgemeine Parallelität, globale Belegnummern und sichere Wiederholung nach unklarem Netzwerkergebnis bleiben in den zugehörigen Aufgaben offen.

## [1.6.8] - 2026-09-07

### Fixed
- Etappe 6 / Punkt 04: Guthabenaufladung speichert Kontostand, Bartransaktion, verknüpften Guthabenlog und Audit mit einem gemeinsamen Commit. Fehler rollen die gesamte Buchung zurück. Aufladung und Verkauf lesen dasselbe Mitgliedskonto unter PostgreSQL-Zeilensperre mit aktualisiertem Kontostand; fehlende Mitglieder liefern HTTP 404.
- Positive Aufladebeträge und das resultierende Guthaben werden gegen den Datenbankbereich geprüft. Hardwareaktionen werden erst nach erfolgreicher Buchung angeboten.

### Added
- Fehler- und Parallelitätstests für Aufladungen und Verkauf sowie fortgeschriebene Aufgabenliste mit persönlichen Live-Test-Schritten. Gemeinsamer auslieferbarer Stand der Etappen 5/6 ist 1.6.8.

## [1.6.7] - 2026-09-07

### Fixed
- Etappe 5 / Punkte 15, 17 und 18: Geschützte APIs prüfen aktive Konten, aktuelle Rollen und eine widerrufbare Sitzungsfassung aus der Datenbank. Passwortänderung, Reset, Rollenwechsel und Deaktivierung widerrufen bisherige Sitzungen und offene Resetlinks; eine spätere Reaktivierung belebt alte Cookies nicht wieder.
- Passwortreset sperrt Konto und Token und speichert Passwort, Tokenverbrauch, Widerruf und Audit gemeinsam. Parallele Einlösung desselben oder unterschiedlicher Links desselben Kontos erlaubt genau einen Passwortwechsel. Das Audit-Aktionsfeld wird auf 64 Zeichen erweitert, damit Reset-Einträge auch unter PostgreSQL gespeichert werden können.
- Datenbankgestützte Begrenzung von Anmelde- und Resetversuchen mit festen 60-Sekunden-Fenstern; blockierte Anfragen verlängern die Wartezeit nicht. Resetanforderungen behalten eine generische Antwort auch während der Wiederholsperre und bei Versandfehlern. Erfolgreiche Passwortbestätigungen verbrauchen kein Fehlversuchsbudget.
- Direkt auffindbarer Einstieg „TopAdmin-Passwort vergessen?“ auf der Loginseite; Resetdialog erklärt Wiederholsperre und Linkgültigkeit.

### Notes
- PATCH-Releases zur Korrektur bestehender Zugangs- und Buchungsregeln. Migration 1.6.7 ergänzt Sitzungsfassung, Begrenzungstabelle und Audit-Feldlänge. Nach dem Upgrade ist eine erneute Anmeldung erforderlich. Frontend und Backend gemeinsam aktualisieren. Alte Aufladungen werden nicht nachträglich mit vermuteten Transaktionen verknüpft.
- Stornos bleiben außerhalb des Umfangs. Allgemeine Belegnummernvergabe, sichere Wiederholung nach Zeitüberschreitung und übrige parallele Buchungswege bleiben in ihren vorgesehenen Etappen offen.

## [1.6.6] - 2026-09-07

### Fixed
- Etappe 4 / Punkte 06 und 07: Produkt-Stammdatenupdates lehnen Bestandsmengen ausdrücklich ab. Das Formular sendet keine Mengen und überträgt die Bestandsart nur bei einer bewussten Änderung. Wechsel der Bestandsart sind nur bei Bestand 0 möglich. Einlagerungen akzeptieren ausschließlich positive Mengen; Einlagerung und Bestandskorrektur lesen unter PostgreSQL-Zeilensperre den aktuellen Wert.
- Gemeinsame Validierungsgrenzen für Produkt-, Mitglieder- und Kategorieanlage, Bearbeitung und Import: nichtnegative Centwerte/Mengen im Datenbankbereich, getrimmte Namen, Textlängen und Ablehnung expliziter Nullwerte in Pflichtfeldern. Zusammengesetzte Mitgliedsnamen werden vor dem Schreiben geprüft. Optionale Leerwerte und Mitgliedspreis 0 bleiben erlaubt.
- Vollständige Importvalidierung vor Ersetzung und Medien-Schreibzugriffen mit Bereich, Zeile und Feld in Fehlermeldungen. Nichtnumerische, unendliche und ungültige Wahrheitswerte werden zurückgewiesen. Formularfehler für Stammdaten werden lesbar angezeigt.
- Benannte Datenbank-Constraints für nichtnegative Preise, Bestände, Mindestbestände und Mitgliedsguthaben sowie gültige Steuersätze und Namen. Vorhandene ungültige Daten stoppen das Upgrade mit betroffenen IDs; keine automatische Änderung von Salden oder Mengen.

### Added
- HTTP-/Service-/Import-Regressionstests und PostgreSQL-Tests für Datenbankgrenzen, veraltete Sessions und parallele Einlagerungen. Aufgabenliste mit Erledigungs- und persönlichem Live-Test-Protokoll fortgeführt.

## [1.6.5] - 2026-09-07

### Fixed
- Etappe 3 / Punkte 38 und 39: Compose verwendet `.env`-Werte für Datenbankzugang, Schlüssel und Betriebsmodus. Neue `.env.example`, lokale Standardbindung, passender psycopg2-Treiber und Ausschluss lokaler Daten aus dem Buildkontext. Fehler bei der Installation von Python-Abhängigkeiten brechen den Build ab.
- Pflichtfehler der Startmigrationen werden weitergegeben. Erfolgreiche Schritte werden versioniert unter PostgreSQL-Sperre dokumentiert; Schema- und Constraintprüfung verhindern auch beim lokalen Start einen Betrieb mit unvollständigem Schema.
- Legacy-Enummigration erhält Managerrollen, Teil-Einlösestatus und Enum-Standardwerte. Neue Gutschein-Restwertspalten werden mit unterscheidbaren Nullwerten angelegt und wiederholbar befüllt; vorhandene Werte und Status werden nicht bei jedem Start erneut normalisiert.

### Added
- Konfigurations- und PostgreSQL-Integrationstests für Erstinstallation, Upgrade, wiederholten/parallelen Start, kontrollierte Fehler und unterbrochene Backfills. Anleitung für `.env`, bestehende Datenbankvolumes, HTTPS-Betrieb und Migrationen.

## [1.6.4] - 2026-09-07

### Fixed
- Mitgliederrollen sind auch beim expliziten Entfernen (`role: null`) TopAdmin vorbehalten. Normale Profiländerungen und Passwortneuvergabe verändern weder Aktivierung noch Rolle eines bestehenden verknüpften Kontos. Importierte Mitglieder ohne Zugang bleiben ohne unbeabsichtigte Kontoerstellung bearbeitbar; die erstmalige Zugangseinrichtung bleibt TopAdmin vorbehalten.
- Die allgemeine Benutzerverwaltung schützt verknüpfte Konten auf allen Änderungswegen: Dort bleibt nur die Passwortneuvergabe erlaubt. Rollen und Aktivierung laufen über die Mitgliederverwaltung. TopAdmin-Schutz gilt einschließlich Rollenaliasen und Reaktivierung; allgemeine Updates lehnen Kontozustands-, Verknüpfungs- und Passwort-Hash-Felder ausdrücklich ab. Der fehlende Import für die Behandlung von Datenbankkonflikten in der Benutzer-API wurde ergänzt.
- Reguläre Transaktionslisten/-details, Umsatz-/Mitgliederstatistiken, allgemeine Bargeldverwaltung und Materialkonto erfordern Admin. Manager behalten Z-Bon, Verlauf und die separate operative Materialliste. Die Finanzansicht lädt für Manager keine gesperrten Statistiken mehr im Hintergrund; auch der ältere Z-Bon-Mailweg prüft die erlaubten Rollen.
- Kasse und Gastdialog laden eine reduzierte Mitgliedsauswahl ohne Kontakt-, Notiz- und Benutzerkontodaten. Vollständige Mitgliederprofile sind nur für die Verwaltung zugänglich. Inaktive Mitgliedskonten werden in der Benutzerübersicht korrekt gekennzeichnet und gefiltert.

### Added
- 89 HTTP-/Service-Regressionstests für die Rollen- und Datenzugriffsgrenzen aus Etappe 2, einschließlich erlaubter Verwaltungs-, Z-Bon- und Materialabläufe.
- Erledigungsvermerke und Live-Test-Protokoll für Punkte 14/16 in der Projektprüfung; aktualisierte Rollen-/API-Matrix in `User-Auth.md`.

### Notes
- Patch-Release zur Durchsetzung bereits vorgesehener Berechtigungen. Keine Datenbankmigration. Backend und Frontend gemeinsam aktualisieren, da die Kasse nun `/api/members/selection` und die Materialliste `/api/admin/vouchers/material-transactions` verwendet. Passwort-/Sitzungswiderruf, Transaktionsatomarität und PostgreSQL-Prüfungen bleiben in den dafür vorgesehenen Etappen offen.

## [1.6.3] - 2026-09-07

### Fixed
- Backup- und Lager-Mailadressen können ausschließlich durch TopAdmin geändert werden. Gewöhnliche Admins dürfen nur ausdrücklich freigegebene Design- und Anzeigeeinstellungen bearbeiten; neue Einstellungsfelder erfordern standardmäßig TopAdmin. Gemischte unzulässige Anfragen werden vollständig mit HTTP 403 zurückgewiesen.
- Allgemeine Mitglieder-Updates lehnen `balance_cents` ausdrücklich mit HTTP 422 ab, einschließlich `null`, unveränderter Werte und gemischter Änderungen. Auch der Mitglieder-Service verhindert diesen direkten Änderungsweg. Aufladung und protokollierte Guthabenkorrektur bleiben verfügbar.

### Added
- HTTP- und Service-Regressionstests für die Berechtigungsgrenzen, ausbleibende Teiländerungen, Empfänger-Auditprotokolle sowie reguläre Mitgliederbearbeitung, Aufladung und Korrektur. HTTPX ist als Testabhängigkeit erfasst.
- Fortschrittsprotokoll, kleinere Umsetzungspakete und Live-Test-Abnahme in `Projektpruefung-2026-09-06.md`; Punktnummern bleiben stabil.

### Notes
- Patch-Release für die Sicherheitskorrekturen aus Punkt 01 und 02 der Projektprüfung. Keine Datenbankmigration erforderlich. Gemeinsame Datenbankgrenzen einschließlich Mitgliedsguthaben werden nach Bestandsprüfung unter Punkt 07 umgesetzt.

## [1.6.2] - 2026-09-04

### Changed
- Der Bereich `Help & Info` wurde als responsive Funktionsübersicht mit eigenen Detailseiten für Kasse, Mitglieder, Produkte, Voucher, Deckel/Gäste, Finanzen, Verbrauchsmaterial/Hardware und Administration/PWA neu aufgebaut.
- Jeder Funktionsabschnitt besitzt eine deutlich erkennbare Mehr-Navigation; Detailseiten bieten eine konsistente Zurück-Navigation und aktuelle rollen- sowie abrechnungsbezogene Hinweise.

### Added
- Tastaturbedienung mit Escape-Navigation, zugängliche Dialogbeschriftungen, sichtbare Fokuszustände und reduzierte Animationen bei entsprechender Systemeinstellung.

## [1.6.1] - 2026-09-04

### Fixed
- Interne Materialbuchungen behalten serverseitig ihren Zahlbetrag von 0,00 €; der Produkt- oder Mitgliedspreis wird nur noch als Materialkontowert verwendet.
- Variable Preise bleiben der im Kassiervorgang eingegebene Ad-hoc-Preis, während Festpreise bei Direktverkauf und neuen Deckelpositionen serverseitig aus den Produktdaten ermittelt werden.
- Mitgliedspreise von 0,00 € werden korrekt angewendet; Rabattberechtigung des Mitglieds und Rabattfähigkeit des Artikels werden in Frontend und Backend einheitlich berücksichtigt.
- Positive Barverkäufe ohne übermittelten Barbetrag werden abgelehnt, echte 0-Euro-Buchungen bleiben ohne Bargeld möglich.
- Das interne Kennzeichen wird serverseitig abgelehnt, wenn der Artikel nicht zur reservierten internen Materialkategorie gehört.

### Added
- Zentrale Preisermittlung für Direktverkauf, Deckel und Materialbewertung.
- Automatisierte Preis- und Checkout-Tests sowie `Buchungswege.md` mit fachlicher Testmatrix und erwarteten Kassen-/Lageröffnungen.

### Compatibility
- Keine Datenbankmigration und keine neue Laufzeitabhängigkeit erforderlich; bestehende Installationen und historische Buchungen bleiben unverändert lesbar.

## [1.6.0] - 2026-09-04

### Added
- Eigene Admin-Seite für die Transaktionsliste des internen Verbrauchsmaterials, erreichbar für Manager, Admin und TopAdmin.
- HTML-Vorschau der gefilterten regulären Transaktionsliste mit anschließendem CSV- oder PDF-Download.
- Abhängigkeitsfreier PDF-Fallback für schlanke Installationen ohne WeasyPrint.

### Changed
- Die Gästeliste wird produktübergreifend chronologisch dargestellt; Datum, Gastname, Gastgeber, Anlass und Beleg sind direkt vergleichbar.
- Rollen- und Funktionsdokumentation wurde an die neuen Listen- und Exportrechte angepasst.

## [1.5.0] - 2026-09-03

### Added
- Central drawer-intent responses for cash movements, stock movements, Deckel bookings and storni.
- TopAdmin-only manual controls for the main and small-parts drawers.
- `CD-Open-Logic.md` as the authoritative drawer-opening decision table.

### Fixed
- Fully voucher-funded and zero-value sales no longer request the main cash drawer.
- Positive stock corrections now request the small-parts drawer for marked products.
- Deckel settlement no longer fails while building its drawer response.
- Browser-local drawer pulses replace duplicate server- and client-side sale triggers.

### Security
- The local agent rejects drawer pulses from browser origins that were not paired locally.

## [1.4.1] - 2026-08-31

Patch release adding secure client-local setup for the two USB drawer adapters.

### Added
- TopAdmin controls for listing locally detected adapters, sending a test pulse to each
  selected adapter and saving the logical main/small-parts assignment.
- Client-local pairing for PWAs hosted on an external server: a protected `/pair` flow
  authorizes only the current browser origin without exposing USB access to the server.
- Installer-generated local configuration code, displayed by the graphical setup wizard.
- Stable `/dev/serial/by-path` discovery as fallback when `/dev/serial/by-id` is unavailable.

### Changed
- Drawer mappings are written atomically to `/etc/default/kickerkasse-agent` and activated
  immediately without an agent restart.
- The local agent configuration file is restricted to root (`0600`).

### Security
- Adapter tests and configuration writes require the client-local configuration code.
- Requested test devices must be present in the agent's discovered-device allowlist.
- External PWA origins require explicit local pairing; permissive all-origin CORS is not used.

## [1.4.0] - 2026-08-31

Feature release for a second USB-controlled drawer used as a small-parts store.

### Added
- Logical `main` and `small_parts` drawer targets in the local hardware agent.
- Safe `/openDrawer/small_parts` endpoint; the existing `/openDrawer` endpoint remains
  backward compatible and always addresses the main drawer.
- Persistent adapter mapping through `/etc/default/kickerkasse-agent`, preferring stable
  `/dev/serial/by-id` device paths.
- Product option `Kleinteile-Lager` with explanatory text and additive database migration.
- Separate hardware status for the main drawer and small-parts store in admin settings.
- Automated tests for adapter assignment, endpoint isolation and product trigger logic.

### Changed
- Sales containing at least one marked product request the small-parts drawer in addition
  to any payment-dependent main-drawer opening, including Deckel settlements.
- The installer preserves an existing adapter mapping and automatically records up to two
  connected adapters during first installation.

### Security
- The agent rejects unknown drawer targets and prevents both logical drawers from using
  the same physical adapter.

## [1.3.1] - 2026-08-31

Release 5 hardens future Z-Bon archives without rewriting historical records.

### Added
- Nullable cent fields for all canonical revenue, tender, recharge, tip and cash-movement
  values in `zbon_history`, including additive startup migration support.
- Persistence and API exposure of the new cent fields for every newly created Z-Bon.

### Changed
- Existing archives deliberately retain `NULL` for values that cannot be reconstructed
  reliably; no automatic historical mutation is performed.
- Transaction records persist tendered cash and paid-out change when these values are known.

## [1.3.0] - 2026-08-31

Release 4 adds low-risk historical verification as a read-only feature.

### Added
- Finance-protected `GET /api/transactions/zbon/audit` consistency report.
- Cent-based reconstruction of archived cash targets from stored Z-Bon components.
- Explicit `consistent`, `mismatch`, and `insufficient_data` classifications.

### Security
- Historical Z-Bons remain immutable; the audit endpoint never updates archive data.

## [1.2.1] - 2026-08-31

Release 3 unifies all current-period Z-Bon output channels.

### Changed
- Legacy generate, HTML, PDF, manual email and scheduled email paths now use the same
  canonical period preview as `Admin -> Finanzen`.
- Scheduled reports cover the open period since the last Z-Bon instead of independently
  recalculating one calendar day.
- PDF responses are emitted from the same rendered HTML and correct in-memory byte stream.

### Fixed
- Removed channel-specific formulas that could display different cash targets in the
  frontend, HTML report, PDF and email.

## [1.2.0] - 2026-08-31

Release 2 introduces variable donated change for cash payments.

### Added
- Freely selectable tip/donation amount up to the available change.
- One-click donation of the complete change amount.
- Identical donation support when settling a Deckel.
- Server-side validation and tests for tendered cash, donation and returned change.

### Changed
- Tip is treated as a cash donation and stored separately from article revenue.

## [1.1.13] - 2026-08-31

Release 1 establishes one canonical, cent-based Z-Bon calculation.

### Added
- Explicit cent values for article revenue, payment allocations, member recharges,
  prepaid sales, donations, deposits, withdrawals and calculated cash.
- Automated tests for cash movements, prepaid separation and the externally settled
  club/voucher account.

### Fixed
- `Admin -> Finanzen` and the Z-Bon now display the same calculated cash target.
- Cash member recharges and donated change are included in the cash target.
- Club/voucher account recharges remain excluded from physical register cash.

## [1.1.12] - 2026-08-07

Patch release for Kasse user switch-login modal consistency and username-dropdown reliability.

### Changed
- The `Login` action in the navbar for the `Kasse` user now uses the shared credential
  modal instead of the legacy custom login popup.

### Fixed
- Username selection in shared credential dialogs now uses a robust explicit dropdown
  selector combined with free text input, so list selection works reliably while manual
  username entry remains possible.

## [1.1.11] - 2026-08-07

Patch release for TopAdmin toggle visibility in the active admin settings flow.

### Fixed
- The `Direktanmeldung \"Kasse\"` toggle is now rendered in the actually used
  `Admin -> Einstellungen -> Erweitert` (`AdminConfig`) view.
- The toggle remains TopAdmin-only, while regular Admin users can still save the
  non-privileged Kassenfunktionen toggles without permission errors.

## [1.1.10] - 2026-08-07

Patch release for controlled disabling of direct `Kasse` login.

### Added
- New TopAdmin toggle in `Settings -> Ext. Settings` to enable or disable direct
  `Kasse` login from the login screen.

### Changed
- When direct `Kasse` login is disabled, the `Kasse anmelden` button is hidden on the
  login screen to enforce personal, attributable usage via named user accounts.

### Security
- `/api/auth/login-kasse` now enforces the new setting server-side and rejects direct
  `Kasse` logins when disabled.

## [1.1.9] - 2026-08-07

Patch release for TopAdmin password-reset trigger reliability on the login screen.

### Changed
- The reset modal now shows a clear warning when no email channel for password-reset
  delivery is configured (SMTP/E-Mail disabled or incomplete).

### Fixed
- Login no longer hard-reloads the page on expected `401` responses from
  `/auth/login` and `/auth/login-kasse`, so failed-attempt state can continue inside
  the current login view.
- The frontend auth store now correctly exposes the
  `topAdminResetAvailable` flag, enabling the reset modal to open after 5 consecutive
  failed TopAdmin login attempts.

## [1.1.8] - 2026-08-07

Patch release for credential-modal username input usability.

### Fixed
- Username selection in password-confirmation dialogs now remains freely editable after
  choosing an entry from suggestions, so the value can be cleared again and replaced with
  a manually typed account such as `TopAdmin`.

## [1.1.7] - 2026-08-07

Patch release for imported-member edit reliability and unified password-confirmation UX.

### Changed
- Password-protected admin and system actions now use one shared credential dialog
  component with consistent visual styling aligned to the login screen language.

### Fixed
- Members imported into a fresh environment can now be edited and receive role updates
  even when their member email equals the already configured TopAdmin email.
- Legacy databases now remove obsolete unique constraints on `members.email` during
  migration so member imports no longer fail on duplicate email-only collisions.
- Member-to-user sync no longer aborts role assignment/edit workflows when a target
  email is already occupied by another user account.

## [1.1.6] - 2026-08-06

Patch release for the credential modal's visual alignment.

### Changed
- The shared system credential modal now uses a single clear title in the header and moves
  the action hint into the body, so password prompts no longer look like two stacked modal
  variants.

## [1.1.5] - 2026-08-06

Patch release for imported-member edit handling and visible error feedback.

### Fixed
- Imported members that previously had a role can now be updated again after a normal export
  and import into a fresh installation, even when the linked user account was not included
  in the import.
- The member form now shows a visible error when save/update fails instead of appearing to
  do nothing.

## [1.1.4] - 2026-08-06

Patch release for the central credential modal's user dropdown behavior.

### Changed
- Password-confirmation dialogs now load the known user list including inactive accounts,
  while still excluding `TopAdmin` and `Kasse`, so the shared modal shows the intended
  dropdown in admin workflows such as prepaid voucher creation.

### Fixed
- The credential modal no longer falls back to the old-looking single-username input when
  the system has known users available for selection.

## [1.1.3] - 2026-08-06

Patch release for imported-member editability and credential-modal consolidation follow-up.

### Changed
- The shared system credential modal remains the single template for all password-protected
  actions outside the login screen.

### Fixed
- Imported members that previously had a user role can now be edited again even if their
  linked account was not recreated during import.
- Role-bearing members without a linked user account no longer hit a false-positive
  password-required validation during ordinary member edits after import.

## [1.1.2] - 2026-08-05

Patch release for import/export follow-up fixes and modal unification.

### Added
- Unified password-confirmation dialogs behind a single shared Vue template, while keeping
  the existing component entry points for backward compatibility.
- Username dropdown support in password-confirmation flows for known users, excluding the
  TopAdmin and cash-register accounts.

### Changed
- Password-protected modal windows now share one consistent system-style layout that mirrors
  the login screen's visual language while omitting the `Kasse anmelden` button.
- Member-linked user accounts are now resynchronized with collision-safe usernames when a
  member later receives a role again after an import/export roundtrip.

### Fixed
- Import/export now logs the actions in the audit trail and states clearly that user
  accounts are not exported or imported.
- Import/export follow-up member-role assignments now avoid ambiguous 400 responses when a
  previously used username still exists in the database.
- Member renaming after import no longer stalls on stale linked-user username state.
- TopAdmin password confirmation now consistently raises the reset flow after repeated
  failed attempts.

## [1.1.0] - 2026-08-05

Roadmap-driven UX and TopAdmin-security release. See `Roadmap-UX-Sicherheit.md` for the full
technical concept, affected-files list, risk assessment, and implementation plan behind this
release.

### Added
- Self-service password-reset workflow for the TopAdmin account: a mandatory email address
  during initial setup, a login failed-attempt counter, a non-dismissible reset modal after
  5 consecutive failed TopAdmin logins, one-time/time-limited reset tokens, a dedicated
  `/password-reset/:token` page, and full audit logging of the reset flow
  (`PasswordResetToken` model, `PasswordResetService`, new `/api/auth/password-reset/*`
  endpoints, `TopAdminResetModal.vue`, `PasswordResetView.vue`).
- "Passwort wiederholen" (repeat password) field with real-time mismatch validation in
  `UserFormModal.vue` and `UserPasswordResetModal.vue`.
- Inline success feedback showing the auto-generated username (`Vorname.Nachname`, with
  `.2`, `.3`, ... on collisions) when a member account is created via role assignment.
- Inline, in-dialog error feedback (shake animation, red border, message below the field)
  for `PasswordConfirmModal.vue` and `CredentialConfirmModal.vue`, replacing toast-only
  errors for password-protected actions (Verzehrkarten/prepaid vouchers, gift vouchers,
  balance recharge, hard reset, database restore, Z-Bon creation, cash drawer).
- Toggle-switch control for category visibility, replacing the checkbox in
  `CategoryFormModal.vue`.
- Visible Python 3.9+ requirement hint in the hardware-service installer UI.

### Changed
- Modal dialogs no longer close on backdrop click across the application (~16 components);
  closing is now exclusively via the explicit close button, "Abbrechen", or equivalent
  action buttons.
- `CategoryFormModal.vue` layout tightened (single unified default color for
  `highlight_color` shared between load and reset, compact 3-column header row) to avoid
  scrollbars, aligned with the `CategoryAssignmentModal.vue` ("Artikel zuordnen") reference
  layout.
- Hardware-service installer download now offers a single complete ZIP package instead of
  individual file downloads; the removed `backend/app/routers/hardware_agent.py` duplicate
  router (never registered/imported) was emptied out with an explanatory deprecation notice.
- `backend/services/install_agent_service.py` now verifies the Python version, creates an
  isolated virtual environment, and installs missing runtime dependencies (flask, pyserial)
  automatically, with structured logging and user-facing status messages.
- Guest-list entry form (`GuestListModal.vue`) field order changed to visitor name first,
  "Gast von" member assignment second.
- "Standard wiederherstellen" design-color reset button now has a descriptive tooltip
  ("Setzt alle Farbanpassungen auf die Standardwerte der Anwendung zurück.").

### Fixed
- Fixed a mismatch between the initial `highlight_color` load default and the
  "Standard wiederherstellen" reset default in `AdminConfig.vue`.
- Fixed a missing `.btn`/`.btn-secondary` style definition in
  `GuestListOverviewModal.vue` that left the "Schließen" button unstyled.
- Password-protected actions (recharge, hard reset, database restore, Z-Bon creation,
  voucher creation/edit, club-account top-up) now keep their confirmation dialog open on a
  wrong-password response instead of closing prematurely and only showing a toast.

### Security
- Added production validation for session secrets and secure cookies; removed the public debug user-count endpoint.
- Restricted database-backup restores to authenticated TopAdmin sessions with password confirmation and audit logging.
- TopAdmin password-reset tokens are stored only as a SHA-256 hash, are single-use, and
  expire after 60 minutes; every request/confirm step is written to the audit log.

### Testing
- Added the project's first backend test suite (`backend/tests/`, run with `pytest` after
  `pip install -r requirements.txt -r requirements-dev.txt`), covering: the login
  failed-attempt counter and its 5-attempt threshold, matching/mismatching email handling in
  the reset request step, single-use and expiry enforcement for reset tokens, the
  `TopAdminSetupRequest` mandatory-email validation, and username-collision suffixing
  (`Vorname.Nachname`, `.2`, `.3`, ...) when assigning a role to a member. Tests run against
  an in-memory SQLite database and do not require PostgreSQL.

### Changed
- `VERSION`, `CHANGELOG.md`, and the release workflow are now the authoritative release inputs.
- Database migration now runs once in the container entrypoint and prevents startup when it fails.
- Sale prices for fixed products are now calculated server-side from product and member data.

### Fixed
- Prevented repeat reversals of the same sale in the service layer and added a database-level partial unique index for new databases.
- Existing databases now validate historical reversals before the one-storno-per-sale index is installed.
- Grouped sale writes into one commit so failed stock, balance, voucher, or prepaid-card processing does not leave partial bookings.
- Locked member and product rows during checkout to prevent concurrent balance and inventory updates from overwriting each other.

## [1.0.0] - 2026-05-19

First structured stable release of KickerKasse after retrospective history consolidation and
release-governance hardening.

### Added
- Root `VERSION` file for a single repository-wide release number.
- Release workflow with Conventional-Commit validation, SemVer checks, frontend build output,
  and GitHub release bundle creation.
- Repository-level release guidance for changelog discipline, tag naming, and meaningful commits.

### Changed
- Consolidated 352 historical commits and 75 pull requests into semantically versioned milestones.
- Formalized the repository around reproducible release inputs instead of ad-hoc beta tags.

## [0.9.2] - 2026-05-19

Release-candidate stabilization phase that made the admin area operationally consistent and
prepared the repository for a production-grade release. Historical tag alignment: `b0.91`.

### Added
- Donation link and deployment-oriented README sections.
- Responsive modal variants and compact admin layouts for smaller displays.
- Unified `AdminConfig` area by combining design, data maintenance, and extended settings.
- Sticky admin headers and consistent inactive-tab styling across admin pages.

### Changed
- Moved non-operational and design-heavy reference material into `.github/development-documentation`.
- Standardized admin layouts, buttons, spacing, and navigation behavior across views.

### Fixed
- Finance and correction scroll/header offset issues.
- Product card width regressions and modal sizing inconsistencies.
- `.env.example` scheduler entry cleanup and repository cleanup for uploaded sample assets.

## [0.9.1] - 2026-05-06

Correctness and security hardening phase centered on correction bookings, permissions, and session handling.

### Added
- Configurable session timer for controlled auto-logout behavior.
- Admin correction tab with mandatory reasons for account/product corrections.
- Finance integration for correction bookings and correction visibility in operational views.

### Changed
- Tightened role permission boundaries and documented the updated authorization model.

### Fixed
- Extended-settings authorization guard ordering.
- Correction validation wording and finance integration polish.

## [0.9.0] - 2026-05-04

Feature-complete beta for the point-of-sale experience, with layout variants, image tooling, and
frontend architecture cleanup. Historical tag alignment: `b0.9`.

### Added
- Admin search filters and stricter cart stock handling.
- Product `Warengruppe` metadata and Z-Bon aggregation by product group.
- HTML preview layouts for checkout and receipt designs.
- Multiple Kasse layout variants, category color styling, and business-data design controls.
- Interactive product image crop editor with Kasse card preview and pan/zoom controls.
- Variable pricing, tip/donation handling, and reset-to-original image behavior.
- PWA icon set improvements including maskable app icons.

### Changed
- Extracted shared Kasse behavior into a reusable `useKasse` composable.
- Added synchronized `kasse_layout` settings across clients and settings screens.

### Fixed
- Layout persistence and cross-client layout synchronization.
- Crop bounds, scale handling, and image preview regressions.

## [0.8.0] - 2026-04-27

Operational hardening milestone focused on admin workflows, cash/booking correctness, and reset safety.

### Added
- Internal material-sale context and refined finance views for internal accounts.
- Open-Deckel indicators and unlimited-stock product handling.
- Hard-reset flow with sequence reset and controlled logout behavior.
- Tabular finance views, voucher sections in finance, and explicit withdrawal payment handling.

### Changed
- Redesigned admin edit modals and aligned admin layouts with the members view.
- Clarified booking, audit, and payment labeling inside finance and Z-Bon flows.

### Fixed
- Booking audit calculations, transaction sorting, and recharge vs. cash separation.
- Hard-reset cleanup for linked users and category recreation defaults.
- Scheduler/admin view accessibility and action button semantics.

## [0.7.0] - 2026-04-24

Breaking domain-model expansion that renamed stored-value concepts and introduced deeper finance workflows.

### Added
- Verzehrkarten as a first-class prepaid flow with updated voucher and checkout behavior.
- Material-account and Deckel workflows in checkout and finance areas.
- Richer finance modals, bon-button adjustments, and improved cashier/admin UI states.
- Project branding under the name **KickerKasse by KGB Hannover**.

### Changed
- Renamed the former Guthabenkarten concept to Verzehrkarten across backend, database, and UI.
- Refined admin/cashier frontend flows and account views.

### Fixed
- Backend startup import errors and migration defaults around the evolving finance model.
- Product deletion wiring and Z-Bon modal state handling.

## [0.6.0] - 2026-04-21

Administrative and operational maturity milestone covering user lifecycle, finance workflows, and deployability.

### Added
- Member metadata, finance modal groundwork, and club-account handling.
- Top-admin backend maintenance flow and password-oriented user-management improvements.
- Soft-delete support for users and better gift-voucher attribution.
- Frontend lockfile to stabilize deployments and builds.

### Changed
- Tightened user/role flows, finance naming, and Z-Bon operator selection.

### Fixed
- Voucher club-account routing and user deletion edge cases.
- Deployment stack reproducibility issues caused by missing frontend lock metadata.

## [0.5.0] - 2026-04-19

Identity and experience milestone that established roles, membership workflows, and installable app branding.

### Added
- Role-based safeguards for critical actions.
- Configurable app title, theme handling, and contrast helpers.
- Membership improvements including sequential member numbers and optional email flows.

### Changed
- Finalized branding and validation behavior for the PWA-facing frontend.

### Fixed
- Member-number backfill ordering and retry handling.

## [0.4.0] - 2026-04-17

Voucher stabilization milestone that connected voucher lifecycle handling with Z-Bon and finance workflows.

### Added
- Admin voucher editing, improved redemption handling, and clearer finance/Z-Bon voucher flows.
- Better Z-Bon preview feedback and cash-count display refinements.

### Changed
- Simplified voucher models and enum migration behavior.
- Aligned voucher API, UI, and generated voucher-code handling.

### Fixed
- Voucher creation, listing, redemption, and validation feedback defects from the initial rollout.

## [0.3.0] - 2026-04-15

First voucher implementation spike. This introduced major domain functionality, but the feature was still unstable.

### Added
- Initial voucher issuance and integration into the wider checkout flow.

### Fixed
- Rapid same-day routing, database, and voucher hotfixes that followed the first rollout.

## [0.2.0] - 2026-04-14

Early product milestone that established the Z-Bon as the financial reporting core and pivoted report output to HTML.

### Added
- First Z-Bon implementation, including detailed views and export rendering.
- Category and counter updates plus broader functional monitoring hooks.

### Changed
- Switched the Z-Bon output approach away from PDF and toward HTML rendering.
- Applied broader CSS and layout passes while the finance flow was still forming.

### Fixed
- HTML API integration errors discovered during the rendering pivot.

## [0.1.0] - 2026-04-12

Initial development baseline and bootstrap phase.

### Added
- First repository import with backend, frontend, and Docker-based local startup.

### Changed
- Updated API routing and Docker port mapping during the first deployment attempts.

### Fixed
- Initial login fixes and early Docker/Windows compatibility fixes.
