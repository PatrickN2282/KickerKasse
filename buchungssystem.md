# Buchungssystem

## Grundregeln

- Die **Hauptstatistik** umfasst Verkäufe, Mitgliedsguthaben-Aufladungen und Kassenbewegungen.
- Das **Gutscheinkonto** ist ein Nebenbuch und fließt **nicht** in Bar-Einnahmen, Umsatz gesamt oder Soll-Kassenbestand ein.
- **Abschöpfungen** sind eigenständige Kassenbuchungen, reduzieren den Soll-Bestand und erscheinen in den Transaktionslisten.
- **Geschenk-Gutscheine** und **interne Materialbuchungen** werden separat ausgewiesen.

## Buchungstypen

| Buchungstyp | Auslöser | Wirkung Hauptstatistik | Wirkung Nebenbücher / Audit |
| --- | --- | --- | --- |
| Verkauf BAR | Verkauf mit `payment_method=CASH` | Erhöht Bar-Einnahmen und Umsatz gesamt um den bar bezahlten Restbetrag | Beleg in Transaktionsliste |
| Verkauf Guthaben | Verkauf mit `payment_method=BALANCE` | Erhöht Guthaben-Umsatz und Umsatz gesamt um den vollständig aus Guthaben bezahlten Betrag | Mitgliedsguthaben wird reduziert, Beleg in Transaktionsliste |
| Verkauf BAR + Guthaben | Verkauf mit `payment_method=CASH` und `balance_applied_cents > 0` | Bar-Einnahmen steigen um den Baranteil, Guthaben-Umsatz um den eingelösten Guthabenanteil, Umsatz gesamt um die Summe beider Teile | Mitgliedsguthaben wird reduziert, Beleg in Transaktionsliste |
| Verkauf mit Geschenk-Gutschein | Verkauf mit `voucher_applied_cents > 0` und `voucher_type=GIFT` | Gutschein-Umsatz steigt um den eingelösten Gutscheinwert; Rest folgt der Zahlungsart BAR oder Guthaben | Gutschein-Restwert sinkt, Beleg in Transaktionsliste |
| Verkauf mit Verzehrkarte | Verkauf mit `voucher_applied_cents > 0` und `voucher_type=PREPAID` | Gutschein-Umsatz steigt um den eingelösten Kartenwert; Rest folgt der Zahlungsart BAR oder Guthaben | Karten-Restwert sinkt, Beleg in Transaktionsliste |
| Verkauf von Verzehrkarten | Verkauf eines Produkts mit Marker `VERZEHRKARTE:` | Erhöht Umsatz gesamt entsprechend dem Verkauf; Bar- oder Guthabenanteil folgt der Zahlungsart | Gibt vorhandene PREPAID-Gutscheine aus und reduziert deren Lagerbestand |
| Mitgliedsguthaben aufladen | `TransactionType.RECHARGE` mit `member_id` | Erhöht **Bar-Einnahmen**, **Umsatz gesamt** und den Soll-Kassenbestand um den Aufladebetrag; wird zusätzlich als `Guthaben verkauft` ausgewiesen | Erhöht Mitgliedsguthaben, Beleg in Transaktionsliste |
| Gutscheinkonto aufladen | `TransactionType.RECHARGE` mit verknüpftem `ClubAccountEntry` | **Keine** Wirkung auf Bar-Einnahmen, Umsatz gesamt oder Soll-Kassenbestand | Erhöht nur das Gutscheinkonto, bleibt im Gutscheinkonto-Verlauf und als Beleg nachvollziehbar |
| Geschenk-Gutschein erstellen | Anlage eines `VoucherType.GIFT` | Keine direkte Wirkung auf Hauptumsatz oder Kassenbestand | Reduziert das Gutscheinkonto um den Gutscheinwert |
| Abschöpfung | `CashEntryType.WITHDRAWAL` | Reduziert den Soll-Kassenbestand um den Entnahmebetrag | Eigener Eintrag in Transaktionsliste und Abschöpfungsblock |
| Einlage | `CashEntryType.DEPOSIT` | Erhöht den Einlagenwert in der Kassenübersicht | Kassenbewegung im Cash-Entry-Bereich |
| Storno | `TransactionType.STORNO` | Wird separat als Storno ausgewiesen | Referenziert Ursprungsbeleg; gekoppelte Nebenbuchungen werden rückgängig gemacht |
| Interner Materialverkauf | Verkaufsposition mit `is_internal_material=true` auf reservierter Kategorie | Normale Verkaufswirkung gemäß Zahlungsart | Zusätzlich Eintrag im Materialkonto; Storno erzeugt Gegenbuchung |

## Zulässige Verkaufskombinationen

| Kombination | Voraussetzungen | Verrechnung |
| --- | --- | --- |
| Nur BAR | `payment_method=CASH`, keine Gutscheine, kein Guthabenanteil | Voller Zahlbetrag geht in Bar-Einnahmen |
| Nur Guthaben | `payment_method=BALANCE`, keine Gutscheine | Voller Zahlbetrag geht in Guthaben-Umsatz |
| BAR + Mitgliedsguthaben | `payment_method=CASH`, `balance_applied_cents > 0` | Guthabenanteil erhöht Guthaben-Umsatz, Rest erhöht Bar-Einnahmen |
| BAR + Geschenk-Gutschein | `payment_method=CASH`, Gift-Voucher eingelöst | Gutscheinwert erhöht Gutschein-Umsatz, Rest erhöht Bar-Einnahmen |
| BAR + Verzehrkarte | `payment_method=CASH`, Prepaid-Voucher eingelöst | Kartenwert erhöht Gutschein-Umsatz, Rest erhöht Bar-Einnahmen |
| BAR + Gutschein + Mitgliedsguthaben | `payment_method=CASH`, Voucher und `balance_applied_cents > 0` | Reihenfolge: Gutschein reduziert Warenkorb, dann Guthaben, verbleibender Rest ist BAR |
| Guthaben + Geschenk-Gutschein | `payment_method=BALANCE`, Gift-Voucher eingelöst | Gutschein reduziert Warenkorb, Rest wird komplett aus Guthaben bezahlt |
| Guthaben + Verzehrkarte | `payment_method=BALANCE`, Prepaid-Voucher eingelöst | Kartenwert reduziert Warenkorb, Rest wird komplett aus Guthaben bezahlt |

## Verrechnungsreihenfolge im Verkauf

1. Warenkorb bildet den Bruttobetrag.
2. Eingelöste Gutscheine reduzieren zuerst den offenen Betrag.
3. Danach wird – falls gewählt – Mitgliedsguthaben abgezogen.
4. Der verbleibende Rest wird über die eigentliche Zahlungsart bezahlt.

## Kassenlogik

### Bar-Einnahmen

Bar-Einnahmen enthalten:

- bar bezahlte Verkäufe
- bar bezahlte Mitgliedsguthaben-Aufladungen

Bar-Einnahmen enthalten **nicht**:

- Aufladungen des Gutscheinkontos
- eingelöste Gutscheine
- rein aus Guthaben bezahlte Verkäufe

### Soll-Kassenbestand

`Soll-Bestand = Anfangsbestand + Bar-Einnahmen - Abschöpfungen`

Dabei gilt:

- Mitgliedsguthaben-Aufladungen zählen zu den Bar-Einnahmen
- Gutscheinkonto-Aufladungen zählen **nicht** zum Soll-Bestand
- Abschöpfungen erscheinen zusätzlich als negative Transaktionszeilen

## Nebenbücher

### Gutscheinkonto

- Positive Buchung: manuelle Aufladung des Gutscheinkontos
- Negative Buchung: Ausgabe eines Geschenk-Gutscheins
- Keine Verrechnung mit Hauptstatistik oder Soll-Kassenbestand

### Materialkonto

- Nur Positionen aus der reservierten internen Materialkategorie mit gesetztem Flag
- Stornos erzeugen spiegelbildliche Gegenbuchungen

## Auditierbarkeit

- Verkäufe und Aufladungen mit Beleg behalten ihre Belegnummer.
- Abschöpfungen erscheinen in den Transaktionslisten mit negativem Betrag und ohne Belegnummer.
- Gutscheinkonto-Buchungen bleiben zusätzlich im separaten Kontoverlauf sichtbar.
