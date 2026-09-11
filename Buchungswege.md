# Buchungswege und Testszenarien

Stand: Version 1.6.4

Diese Matrix beschreibt die erwartete Preis-, Zahlungs-, Bestands- und Schubladenlogik einer neuen Installation. Bestehende Buchungen und Bestände werden nicht nachträglich verändert. Die aktuelle Anwendung bleibt mit vorhandenen Datenbanken kompatibel; für diese Korrektur sind weder neue Tabellen/Spalten noch neue Laufzeitabhängigkeiten erforderlich.

## Legende und Grundregeln

| Begriff | Bedeutung |
|---|---|
| `main` | Hauptkassenschublade; öffnet nur bei tatsächlicher Bargeldbewegung oder einer ausdrücklichen manuellen/Zählaktion |
| `small_parts` | Kleinteile-Lager; öffnet bei physischer Ausgabe oder Einlagerung eines Artikels mit aktivierter Option **Kleinteile-Lager** |
| – | Keine Schublade wird geöffnet |
| Festpreis | Serverseitig gespeicherter regulärer Preis oder zulässiger Mitgliedspreis; der Client kann ihn nicht überschreiben |
| Variabler Preis | Im Kassiervorgang eingegebener Preis, etwa für Spenden oder MHD-Artikel; 0,00 € ist zulässig |
| Internes Material | Verkaufspreis immer 0,00 €; separater Materialkontowert zum regulären bzw. berechtigten Mitgliedspreis |

Ein Mitgliedspreis gilt nur, wenn ein Mitglied ausgewählt ist, dieses `has_discount=true` besitzt, der Artikel `is_discountable=true` besitzt und `member_price_cents` gesetzt ist. Ein gesetzter Mitgliedspreis von 0 Cent ist ausdrücklich gültig.

`small_parts` ist in allen nachfolgenden Verkaufszeilen nur dann enthalten, wenn mindestens ein ausgegebener Artikel entsprechend markiert ist. Ohne diese Produktoption entfällt das Ziel.

## Direktverkauf und Preisermittlung

| ID | Ausgangslage / Eingabe | Erwartete Buchung | Bestand / Nebenkonto | Schubladen | Prüfung |
|---|---|---|---|---|---|
| P01 | Festpreis 5,00 €, Gast, Client sendet abweichend 0,01 €, bar 5,00 € | Artikel und Zahlbetrag 5,00 € | Bestand −1 | `main` (+ `small_parts`) | Automatisiert: `test_fixed_price_is_server_authoritative` |
| P02 | Festpreis 5,00 € / Mitgliedspreis 3,50 €, rabattberechtigtes Mitglied, bar 3,50 € | Artikel und Zahlbetrag 3,50 € | Bestand −1 | `main` (+ `small_parts`) | Automatisiert: `test_fixed_member_price_is_server_authoritative` |
| P03 | Wie P02, Mitglied nicht rabattberechtigt | Artikel und Zahlbetrag 5,00 € | Bestand −1 | `main` (+ `small_parts`) | Automatisiert: Preis-Unit-Test |
| P04 | Wie P02, Artikel nicht rabattfähig | Artikel und Zahlbetrag 5,00 € | Bestand −1 | `main` (+ `small_parts`) | Automatisiert: Backend- und Frontend-Preis-Unit-Test |
| P05 | Mitgliedspreis ausdrücklich 0,00 €, berechtigtes Mitglied | Artikel 0,00 €, Zahlbetrag 0,00 € | Bestand −1 | `small_parts` oder – | Automatisiert: Backend- und Frontend-Preis-Unit-Test |
| P06 | Variabler Artikel, Eingabe 2,25 €, bar 2,25 € | Artikel und Zahlbetrag 2,25 €; Basis-/Mitgliedspreis überschreibt die Eingabe nicht | Bestand −1 bzw. unbegrenzt | `main` (+ `small_parts`) | Automatisiert: `test_variable_price_is_the_cashier_entered_price` |
| P07 | Variabler Artikel, Eingabe 0,00 € | Artikel und Zahlbetrag 0,00 € | Bestand −1 bzw. unbegrenzt | `small_parts` oder – | Automatisiert: Preis- und Bargeld-Unit-Tests |
| P08 | Negativer variabler Preis | Eingabe/API wird abgelehnt | Keine Änderung | – | Automatisiert: Schema/Preis-Unit-Test |
| P09 | Inaktiver oder nicht vorhandener Artikel | Verkauf wird abgelehnt | Keine Änderung | – | Backend-Validierung; manuelle API-Prüfung |
| P10 | Artikel außerhalb der internen Kategorie wird als intern gesendet | Verkauf wird abgelehnt | Keine Änderung | – | Automatisiert: `test_internal_flag_is_rejected_for_product_outside_reserved_category` |

## Internes Verbrauchsmaterial

Beispiel der gemeldeten Ausgangslage: **Ball, regulär 5,00 €, Mitglied 3,50 €, Kategorie Verbrauchsmaterial - Intern**.

| ID | Buchungsweg | Zahlbetrag / Artikelzeile | Materialkonto | Bestand | Schubladen | Prüfung |
|---|---|---:|---:|---:|---|---|
| M01 | Ball intern, kein Mitglied, bar 0,00 € | 0,00 € | +5,00 € | −1 | `small_parts` oder –; niemals `main` | Automatisiert: `test_reported_internal_material_case_books_zero_and_material_value` |
| M02 | Ball intern, rabattberechtigtes Mitglied | 0,00 € | +3,50 € | −1 | `small_parts` oder –; niemals `main` | Automatisiert: `test_internal_material_uses_eligible_member_price_only_for_material_account` |
| M03 | Ball intern, Mitglied ohne Rabatt | 0,00 € | +5,00 € | −1 | `small_parts` oder – | Automatisiert: zentrale Preisregeln |
| M04 | Ball intern, Artikel nicht rabattfähig | 0,00 € | +5,00 € | −1 | `small_parts` oder – | Automatisiert: zentrale Preisregeln |
| M05 | Zwei Bälle intern, berechtigtes Mitglied | 0,00 € | +7,00 € | −2 | `small_parts` oder – | Automatisiert: M02 mit Menge 2 |
| M06 | Interner variabler Artikel | 0,00 €; kein Preisdialog im internen Kategorienweg | Konfigurierter Katalogwert | −1 | `small_parts` oder – | Automatisiert: Preis-Unit-Test |
| M07 | Internes Material plus regulärer Artikel 2,50 €, gegeben 3,00 € | Gesamt 2,50 €, Rückgeld 0,50 € | Materialwert nur für interne Zeile | Je Artikel −1 | `main` + `small_parts` bei markiertem Material | Automatisiert: `test_mixed_internal_and_regular_sale_opens_both_required_drawers` |
| M08 | Interne Kategorie im normalen Produktkontext, Kennzeichen `intern=false` | Normaler Fest-/variabler Verkaufspreis | Kein Materialkontoeintrag | Bestand −1 | Nach Zahlungs- und Lagerregel | Manuelle UI-Prüfung für mehrfach kategorisierte Produkte |

## Zahlungswege

| ID | Zahlungsweg | Erwartete Verteilung | Schubladen | Prüfung |
|---|---|---|---|---|
| Z01 | Bar, passend gegeben | Gesamter Restbetrag bar, Rückgeld 0 | `main` (+ `small_parts`) | Automatisierte Checkout-Tests |
| Z02 | Bar mit Überzahlung | Bar-Restbetrag, Differenz als Rückgeld | `main` (+ `small_parts`) | Automatisiert: gemischter Verkauf und Bargeldtests |
| Z03 | Bar mit Teil-/Vollspende des Rückgelds | Artikelumsatz und Trinkgeld/Spende getrennt; Rückgeld entsprechend reduziert | `main` (+ `small_parts`) | Automatisiert: `test_variable_tip_reduces_change`, `test_full_change_can_be_donated` |
| Z04 | Positiver Barverkauf ohne gegebenen Barbetrag | Ablehnung, keine Buchung | – | Automatisiert: `test_positive_cash_sale_without_tendered_amount_is_rejected` |
| Z05 | Echter 0-Euro-Verkauf ohne/mit 0 Cent Bargeld | Erfolgreich, Rückgeld 0 | `small_parts` oder – | Automatisiert: Bargeldtests und M01 |
| Z06 | Vollständig mit Mitgliedsguthaben | Guthaben −Warenwert, Barrest 0 | `small_parts` oder –; kein `main` | Automatisiert: `test_balance_payment_uses_no_cash_drawer` |
| Z07 | Guthaben reicht nicht, Rest bar | Verfügbares Guthaben wird angerechnet, positiver Rest bar | `main` (+ `small_parts`) | Service-/Drawer-Tests; manueller UI-Test |
| Z08 | Guthaben reicht bei Zahlart Guthaben nicht vollständig | Ablehnung; Nutzer kann anschließend Teilguthaben + Barrest wählen | – | Backend-Validierung; manueller UI-Test |
| Z09 | Geschenk-Gutschein deckt vollständig | Gutschein −Warenwert, Barrest 0 | `small_parts` oder –; kein `main` | Gutschein-Service-/Drawer-Tests |
| Z10 | Verzehrkarte deckt vollständig | Verzehrkarte −Warenwert, Barrest 0 | `small_parts` oder –; kein `main` | Gutschein-Service-/Drawer-Tests |
| Z11 | Gutschein deckt teilweise, Rest bar | Gutscheinanteil plus positiver Barrest | `main` (+ `small_parts`) | Gutschein-Service-/Drawer-Tests; manueller UI-Test |
| Z12 | Gutschein/Guthaben bei 0-Euro-Warenkorb | Keine Einlösung ohne positiven Warenwert | – | Backend-Validierung |
| Z13 | Trinkgeld bei Guthaben-/Gutscheinzahlung | Ablehnung, da Trinkgeld nur bar zulässig | – | Automatisiert: Bargeld-Unit-Test |

## Mitgliederbearbeitung und Guthaben (ab 1.6.3)

| ID | Vorgang | Erwartetes Ergebnis | Prüfung |
|---|---|---|---|
| G01 | Allgemeines Mitglieder-Update enthält `balance_cents`, auch zusammen mit Stammdaten oder als `null` | HTTP 422 für Manager/Admin/TopAdmin; Guthaben, Stammdaten und Historien bleiben unverändert | Automatisiert: `test_generic_member_update_rejects_balance_even_when_mixed` |
| G02 | Gewöhnliche Mitgliedsnotiz ändern | Stammdatenänderung mit Audit; Guthaben unverändert | Automatisiert: `test_generic_member_details_remain_editable` |
| G03 | Manager lädt 5,00 € mit korrektem Passwort auf | Guthaben +500 Cent und Baraufladung über 500 Cent; falsches Passwort wird abgelehnt | Automatisiert: `test_manager_recharge_still_requires_password_and_records_cash` |
| G04 | Admin/TopAdmin korrigiert Guthaben über den vorgesehenen Korrekturweg | Zielguthaben und Korrekturprotokoll mit Altwert, Neuwert, Differenz, Grund und Bearbeiter; keine Barbuchung | Automatisiert: `test_authorized_balance_correction_remains_logged` |
| G05 | Manager verwendet den Guthabenkorrekturendpunkt | HTTP 403; keine Änderungen oder Buchungen | Automatisiert: `test_manager_cannot_use_balance_correction` |

Die Tests stehen in `backend/tests/test_admin_update_boundaries.py`. Die gemeinsame Absicherung von Aufladungen bei Fehlern, von Parallelität und von Datenbankgrenzen bleibt in der Projektprüfung unter 04, 09 beziehungsweise 07 offen.

## Deckel

| ID | Vorgang | Preis-/Bestandswirkung | Schubladen | Prüfung |
|---|---|---|---|---|
| D01 | Deckel mit Festpreisartikel anlegen; Clientpreis weicht ab | Gespeicherter Festpreis wird verwendet; Bestand bleibt bis Bezahlung reserviert | `small_parts` bei markierter neuer Ware, sonst – | Automatisiert: `test_deckel_resolves_fixed_variable_and_internal_prices` |
| D02 | Variablen Artikel mit 2,75 € auf Deckel buchen | Eingegebene 2,75 € werden als Positionspreis gespeichert | `small_parts` bei Markierung, sonst – | Automatisiert: D01 |
| D03 | Internes Material auf Deckel buchen | Positionspreis 0,00 €; Kennzeichen und Notiz bleiben erhalten | `small_parts` bei Markierung, sonst – | Automatisiert: D01 |
| D04 | Weiteren Festpreisartikel zu bestehendem Deckel buchen | Nur neue Position wird kanonisch bepreist; gleiche Positionen werden zusammengeführt | `small_parts` nur für neu ausgegebene markierte Ware | Automatisiert: `test_deckel_append_resolves_new_item_price` |
| D05 | Deckelpreis ändert sich nach dem Buchen im Produktstamm | Bereits gespeicherte Deckelposition bleibt als Preissnapshot bestehen | – bis Bezahlung | Kompatibilitätsregel; manueller Test |
| D06 | Positiven Deckel bar bezahlen | Gespeicherte Positionen werden Transaktion; Bestand wird abgezogen | Nur `main`; Ware wurde bereits ausgegeben | Deckel-/Drawer-Tests; manueller End-to-End-Test |
| D07 | Reinen 0-Euro-Materialdeckel bezahlen | Transaktion 0,00 €; Materialkonto wird gebucht; Bestand wird abgezogen | – | Service-/Preisregeln; manueller End-to-End-Test |
| D08 | Unzulässiges internes Kennzeichen auf Deckel | Anlegen/Erweitern wird abgelehnt | – | Automatisiert: `test_deckel_rejects_internal_flag_for_regular_product` |
| D09 | Nicht ausreichender freier Bestand wegen anderer Deckelreservierung | Anlegen/Erweitern/Bezahlen wird abgelehnt | – | Deckel-Bestandsvalidierung |

## Weitere Bargeld- und Lagerbewegungen

| ID | Vorgang | Buchungswirkung | Schubladen | Prüfung |
|---|---|---|---|---|
| K01 | Mitgliedsguthaben bar aufladen | Bargeldeingang und Erhöhung Mitgliedsguthaben | `main` | Bestehende Recharge-Tests / manueller UI-Test |
| K02 | Bareinlage einschließlich Anfangsbestand | Positiver Kasseneintrag | `main` | Cash-Management-Tests |
| K03 | Direkte Abschöpfung | Negativer Kasseneintrag | `main` | Cash-Management-Tests |
| K04 | Abschöpfung im Z-Bon vormerken und Abschluss speichern | Negativer Kasseneintrag nach erfolgreichem Abschluss | `main` | Z-Bon-Tests / manueller UI-Test |
| K05 | Kassenzählung starten | Keine Buchung allein durch Öffnung; Zählergebnis fließt in Abschluss | `main` | Manueller Hardware-Test |
| K06 | Z-Bon ohne neue Abschöpfung | Nur Bericht/Archiv; keine Bargeldbewegung | – | Z-Bon-Tests |
| L01 | Markierten Artikel mit positivem Anfangsbestand anlegen | Bestand wird eingelagert | `small_parts` | Produkt-/Drawer-Tests |
| L02 | Bestand eines markierten Artikels erhöhen | Positive Bestandsbewegung | `small_parts` | Automatisiert: Drawer-Unit-Test |
| L03 | Bestand ohne physische Entnahme nach unten korrigieren | Negative Korrektur | – | Automatisiert: Drawer-Unit-Test |
| L04 | Bestand mit Option **Kleinteile-Lager öffnen** nach unten korrigieren | Physische Entnahme | `small_parts` | Automatisiert: Drawer-Unit-Test |
| L05 | Unbegrenzter oder nicht markierter Artikel | Keine physisch geführte Kleinteilebewegung | – | Drawer-Unit-Test |
| H01 | TopAdmin öffnet Hauptschublade manuell | Keine Geschäftsbuchung | `main` | Manueller Passwort-/Hardware-Test |
| H02 | TopAdmin öffnet Kleinteile-Lager manuell | Keine Geschäftsbuchung | `small_parts` | Manueller Passwort-/Hardware-Test |

## Automatisierte Ausführung

Backend aus dem Repository-Root:

```powershell
$env:DATABASE_URL='sqlite:///:memory:'
py -3.13 -m pytest backend/tests -q
```

Frontend:

```powershell
Set-Location frontend
npm test
npm run lint
npm run build
```

Die Preis-Tests laufen mit einer isolierten In-Memory-Datenbank und verändern weder bestehende Buchungen noch Bestände. Hardwareimpulse werden in Unit-Tests als logische Ziele geprüft; die tatsächliche USB-Zuordnung muss einmal je Kassen-PC manuell getestet werden.

## Nicht im aktuellen Umfang

Stornos sind im derzeitigen Frontend nicht vorgesehen und deshalb nicht Bestandteil dieser fachlichen Testmatrix. Bereits vorhandene Backend-Stornofunktionen und historische Daten werden durch die Preisbereinigung nicht migriert oder umgeschrieben.
