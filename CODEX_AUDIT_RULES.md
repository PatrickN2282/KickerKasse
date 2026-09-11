# Codex Audit Rules

## Ziel

Dieses Repository enthält eine produktiv eingesetzte Kassensoftware.

Die Anwendung funktioniert bereits erfolgreich im Produktivbetrieb.

Ziel dieser Analyse ist NICHT die Neuentwicklung oder Umstrukturierung der Anwendung.

Ziel ist ausschließlich:

* Fehler finden
* Risiken identifizieren
* Wartbarkeit verbessern
* Sicherheitsprobleme erkennen
* Datenbanklogik prüfen
* Performanceprobleme erkennen
* Inkonsistenzen aufzeigen

---

## Wichtige Einschränkungen

### Keine Architektur-Rewrites

NICHT vorschlagen:

* Wechsel des Frameworks
* Wechsel der Datenbank
* Einführung neuer Architekturmuster
* Microservice-Migration
* Event-Sourcing
* CQRS
* Domain Driven Design
* komplette Refactorings

Wenn die Anwendung funktioniert, ist dies zu respektieren.

---

## Frontend

Frontend (Vue) soll zunächst ignoriert werden.

Frontend nur dann analysieren, wenn:

* Backend-Funktionalität ohne Frontend nicht nachvollziehbar ist
* API-Nutzung unklar bleibt
* Geschäftslogik ausschließlich im Frontend erkennbar ist

Ansonsten ausschließlich Backend analysieren.

---

## Datenbank

Besondere Aufmerksamkeit auf:

* Foreign Keys
* Löschlogik
* Datenkonsistenz
* Transaktionen
* Race Conditions
* Deadlocks
* Fehlende Indizes
* N+1 Queries
* ORM-Fehlkonfigurationen

---

## Sicherheit

Prüfen auf:

* SQL Injection
* Command Injection
* Path Traversal
* Broken Authentication
* Broken Authorization
* JWT-Probleme
* Secrets im Repository
* Unsichere Docker-Konfigurationen
* Privilegienprobleme

---

## Performance

Prüfen auf:

* unnötige Datenbankabfragen
* ineffiziente Schleifen
* unnötige API-Aufrufe
* Speicherlecks
* fehlende Pagination
* fehlendes Caching

---

## Ausgabeformat

Keine Codeänderungen durchführen.

Stattdessen eine Liste erzeugen:

### Kritisch

Probleme mit:

* Datenverlust
* Sicherheitsrisiken
* Absturzrisiken

### Hoch

Probleme mit:

* Stabilität
* Performance
* Wartbarkeit

### Mittel

Verbesserungen mit erkennbarem Nutzen.

### Niedrig

Kosmetische Themen.

---

## Für jede Feststellung

Ausgabeformat:

### Titel

Kategorie:
Schweregrad:

Betroffene Dateien:

Beschreibung:

Auswirkung:

Empfohlene Änderung:

Beispielimplementierung:

---

## Wichtig

Keine Vorschläge erzeugen, nur um Vorschläge zu erzeugen.

Wenn eine Implementierung sinnvoll und stabil ist, ausdrücklich erwähnen.

Qualität vor Quantität.
