# Z-Bon Spezifikation (KGB Kassensystem)

## 1. Zweck

Der Z-Bon ist ein revisionssicherer Kassenabschluss über **alle Transaktionen seit dem letzten Z-Bon**.
Er dient der vollständigen Nachvollziehbarkeit von Umsatz, Zahlungsarten und Kassenbestand.

---

## 2. Allgemeine Pflichtangaben

### 2.1 Identifikation

* Z-Bon Nummer (fortlaufend, eindeutig, ohne Lücken)
* Kassen-ID / Kassenbezeichnung
* Geschäftseinheit (Name, Adresse, optional Vereinsregister)

### 2.2 Zeitangaben

* Erstellungsdatum und Uhrzeit
* Zeitraum:

  * Erste Transaktion (Timestamp)
  * Letzte Transaktion (Timestamp)

### 2.3 Belegreferenz

* Belegnummer von (erste seit letztem Z-Bon)
* Belegnummer bis (letzte seit letztem Z-Bon)
* Anzahl Transaktionen

### 2.4 Verantwortliche

* Z-Bon erstellt von (Name)
* Abschöpfung durchgeführt von (Name)
* Kassensturz durchgeführt von (Name, optional)

---

## 3. Umsatzstruktur

### 3.1 Artikelumsatz (Bruttowerte)

Darstellung aller Verkäufe unabhängig von Zahlungsart:

* Gesamtanzahl Verkäufe
* Gesamtumsatz brutto
* optional:

  * Netto
  * Steuerbetrag

### 3.2 Aufteilung nach Zahlungsarten

Pflichtfelder:

* Barzahlung
* Guthaben (Verzehrkarten / Prepaid)
* Gutscheine (Gewinn / Rabatt)

Summe aller Zahlungsarten muss dem Bruttoumsatz entsprechen.

---

## 4. Guthabensystem (Verzehrkarten)

Separat vom Umsatz auszuweisen:

* Guthaben verkauft (Einzahlungen → erhöht Kassenbestand)
* Guthaben eingelöst (Verbrauch → kein Geldfluss)
* Offenes Guthaben (Restwert aller nicht eingelösten Guthaben)

---

## 5. Gutscheinsystem (Gewinn / Geschenk)

Separat vom Guthaben:

* Gutscheine erstellt (Ausgabe)
* Gutscheine eingelöst
* Offene Gutscheine (noch nicht eingelöst)

---

## 6. Kassenbestand

### 6.1 Berechnung Soll-Bestand

```
Endbestand =
  Anfangsbestand
+ Bareinnahmen (aus Artikelverkäufen)
+ Guthabenverkäufe
- Abschöpfung
```

### 6.2 Pflichtwerte

* Anfangsbestand (letzter bekannter Bestand nach vorherigem Z-Bon)
* Bareinnahmen
* Einnahmen aus Guthabenverkäufen
* Abschöpfungsbetrag
* Soll-Endbestand

### 6.3 Ist-Bestand

* gezählter Bargeldbestand
* Differenz (Ist - Soll)

---

## 7. Abschöpfung

Pflichtangaben:

* Betrag
* Zeitpunkt
* durchführende Person

Mehrere Abschöpfungen im Zeitraum sind zu aggregieren oder einzeln aufzulisten.

---

## 8. Bargeldzählung (optional)

Stückelung nach Nennwerten:

* Scheine (z. B. 50€, 20€, 10€, 5€)
* Münzen (2€, 1€, 0,50€, etc.)

Gesamtsumme muss dem Ist-Bestand entsprechen.

---

## 9. Stornos / Korrekturen

Pflichtblock:

* Anzahl Stornos
* Gesamtbetrag der stornierten Umsätze

---

## 10. Aufschlüsselungen (optional)

### 10.1 Nach Kategorien

* Umsatz je Kategorie (z. B. Getränke, Material)

### 10.2 Nach Kundengruppen

* Umsatz je Kundengruppe (z. B. Mitglied, Gast)

### 10.3 Nach Kunden

* Umsatz je Kunde

---

## 11. Konsistenzregeln

* Summe Zahlungsarten = Gesamtumsatz
* Kassenbestand rechnerisch korrekt
* Keine negativen Endbestände ohne Differenzangabe
* Belegnummern lückenlos

---

## 12. Technische Anforderungen

### 12.1 Unveränderbarkeit

Ein erzeugter Z-Bon darf nicht nachträglich verändert werden.

### 12.2 Datenbasis

Der Z-Bon basiert auf:

* allen Transaktionen seit dem letzten Z-Bon

### 12.3 Archivierung

Z-Bons müssen dauerhaft speicherbar und reproduzierbar sein.

---

## 13. Ausgabeformat (HTML)

Pflichtblöcke:

1. Header (System, Verein, Z-Bon Nummer)
2. Meta-Informationen (Zeitraum, Belege, Personen)
3. Artikelumsatz
4. Zahlungsarten
5. Guthaben
6. Gutscheine
7. Kassenbestand
8. Abschöpfung
9. optional: Aufschlüsselungen
10. Footer (Erstellungszeitpunkt, Berichtstyp)

---

## 14. Begriffsdefinitionen

* Umsatz: Wert der verkauften Waren/Dienstleistungen
* Bareinnahme: tatsächlicher Geldzufluss in die Kasse
* Guthaben: vorab bezahltes Kundenkonto
* Gutschein: nicht bezahlter Rabatt / Gewinn
* Abschöpfung: Entnahme von Bargeld aus der Kasse
* Kassenbestand: physisch vorhandenes Bargeld

---

# 15. Entwicklungsrichtlinien und Release-Workflow

## 15.1 Zielsetzung

Das Projekt wird semantisch versioniert und releasefähig entwickelt.

Ziel:

* reproduzierbare Releases
* nachvollziehbare Changelogs
* automatisierte Versionierung
* konsistente Commit-Historie
* saubere Produktions-Releases

---

## 15.2 Semantic Versioning

Das Projekt verwendet Semantic Versioning:

MAJOR.MINOR.PATCH

Beispiele:

* 1.0.0 = erste stabile Produktivversion
* 1.1.0 = neue Features ohne Breaking Changes
* 1.1.1 = Bugfix Release
* 2.0.0 = inkompatible Änderungen

---

## 15.3 Commit-Konventionen (Conventional Commits)

Commit Messages müssen folgendem Schema folgen:

type(scope): description

Erlaubte Typen:

* feat: neue Funktion
* fix: Fehlerbehebung
* refactor: interne Umstrukturierung
* docs: Dokumentation
* style: Formatierung / Layout
* test: Tests
* chore: technische Wartung
* build: Buildsystem / CI
* perf: Performanceverbesserung
* ci: CI/CD Änderungen

Breaking Changes:

* feat!: Beschreibung
* oder BREAKING CHANGE: im Commit Body

Beispiele:

feat(zbon): add aggregated payment statistics

fix(receipt): correct VAT rounding issue

refactor(storage): simplify transaction persistence

---

## 15.4 KI-gestützte Entwicklung

GitHub Copilot und KI-Tools dürfen verwendet werden.

Dabei gelten folgende Regeln:

* keine generischen Commit Messages
* keine Sammelcommits ohne Beschreibung
* Commits müssen fachlich nachvollziehbar bleiben
* neue Features müssen dokumentiert werden
* Breaking Changes müssen explizit gekennzeichnet werden

---

## 15.5 Changelog

Das Projekt verwendet ein strukturiertes CHANGELOG.md.

Format:
KEEP A CHANGELOG

Kategorien:

* Added
* Changed
* Fixed
* Removed
* Security

Changelog-Einträge müssen aus Commits und Pull Requests ableitbar sein.

---

## 15.6 Release-Typen

### Development / Beta Releases

Dürfen enthalten:

* experimentelle Features
* Entwicklungsartefakte
* Debugging-Komponenten
* interne Strukturen

Versionierung:

* v0.x.x
* beta
* rc

### Stable Releases

Stable Releases müssen enthalten:

* nur produktive Artefakte
* keine Entwicklungsdateien
* keine internen Testdaten
* reproduzierbare Build-Ergebnisse

Stable Releases werden als kontrollierte Release-Artefakte veröffentlicht.

---

## 15.7 Release-Prozess

Releases erfolgen über Git Tags.

Beispiele:

* v1.0.0
* v1.1.0
* v1.1.1

Regeln:

* jeder Release muss reproduzierbar sein
* Releases müssen auf einem stabilen Commit basieren
* Changelog muss aktualisiert werden
* Releases dürfen nicht manuell nachbearbeitet werden

---

## 15.8 GitHub Actions / CI-CD

CI/CD darf automatisch:

* Versionen erzeugen
* Tags erstellen
* Changelogs generieren
* Release-Artefakte bauen
* GitHub Releases veröffentlichen

Empfohlen:

* semantic-release
* conventional commits
* automatisierte Release-Pipelines

---

## 15.9 Produktions-Releases

Produktions-Releases sollen bevorzugt als:

* ZIP
* Build-Artefakt
* Installer
* Docker Image

veröffentlicht werden.

Das GitHub Source-ZIP gilt nicht als finales Produktivartefakt.
