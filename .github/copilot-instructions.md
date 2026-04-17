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
