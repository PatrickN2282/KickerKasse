# Cash-Drawer Open Logic

## Grundprinzip

Die Schubladenöffnung folgt einer physischen Bewegung, nicht lediglich dem Namen einer Zahlungs- oder Buchungsart.

1. Das Backend validiert und speichert den Geschäftsvorgang.
2. Das Backend ermittelt aus den kanonischen Daten die logischen Ziele und liefert `drawer_targets` zurück.
3. Der Browser sendet je Ziel genau einen `POST` an den lokalen Hardware-Agenten auf `127.0.0.1:8765`.
4. Der Agent ordnet `main` und `small_parts` den konfigurierten USB-Adaptern zu und sendet den Schaltimpuls.

Der Backend-Server spricht bei Geschäftsvorgängen nicht mehr selbst mit `127.0.0.1`. Dadurch gibt es weder Doppelimpulse noch eine falsche Adressierung des Server-Loopbacks.

## Betriebsarten

| Installation | Weg | Zusätzliche Einstellung erforderlich |
|---|---|---:|
| Komplett lokal | Browser auf dem Kassen-PC → lokaler Agent → USB-Adapter | Nein |
| Externer Server mit Kassen-Client | Browser auf dem Kassen-PC → lokaler Agent → USB-Adapter | Nein; der Browser-Origin muss am Agenten gekoppelt sein |

Ein separater Modusschalter ist bewusst nicht vorhanden. In beiden zulässigen Betriebsarten befindet sich der Browser auf dem Rechner mit den Schubladen und verwendet denselben lokalen Weg.

## Hauptschublade (`main`)

| Vorgang | Öffnen | Begründung / Bedingung |
|---|---:|---|
| Barverkauf | Ja | Positiver Zahlbetrag, Trinkgeld, entgegengenommener Barbetrag oder Rückgeld |
| Guthaben plus Barrest | Ja | Der verbleibende positive Betrag wird bar abgewickelt |
| Reine Guthabenzahlung | Nein | Keine Bargeldbewegung |
| Vollständig deckender Gutschein | Nein | Zahlbetrag und Bargeldbewegung sind 0 |
| 0-Euro-Verkauf / internes Material | Nein | Keine Bargeldbewegung |
| Guthabenaufladung eines Mitglieds | Ja | Aufladung wird als Bareingang gebucht |
| Bareinlage | Ja | Bargeld wird eingelegt; gilt auch für die initiale Setup-Einlage |
| Direkte Abschöpfung | Ja | Bargeld wird entnommen |
| Im Z-Bon vorgemerkte Abschöpfung | Ja | Nach erfolgreicher Speicherung beim Z-Bon-Abschluss |
| Kassenzählung | Ja | Die Schublade wird vor Anzeige des Zähldialogs geöffnet |
| Storno einer Barzahlung | Ja | Barauszahlung entsprechend der ursprünglichen Bargeldbewegung |
| Storno einer reinen Guthaben-/Gutscheinzahlung | Nein | Keine Barauszahlung |
| Guthabenkorrektur | Nein | Reine Korrekturbuchung ohne Bargeldfluss |
| Bestandskorrektur | Nein | Betrifft ausschließlich Warenbestand |
| Z-Bon ohne neue Abschöpfung | Nein | Berichtserstellung allein ist keine Bargeldbewegung |
| Manuelle Öffnung | Ja | Nach Passwortbestätigung; im Hardware-Bereich nur für Top-Admin sichtbar |

## Kleinteile-Lager (`small_parts`)

Voraussetzung ist immer, dass beim Produkt `opens_small_parts_drawer` beziehungsweise **Kleinteile-Lager** aktiviert ist.

| Vorgang | Öffnen | Begründung / Bedingung |
|---|---:|---|
| Direkter Verkauf | Ja | Mindestens ein markierter Artikel wird ausgegeben; unabhängig von der Zahlungsart |
| Deckel neu anlegen | Ja | Ein markierter Artikel wird in diesem Moment physisch ausgegeben |
| Weitere Artikel auf Deckel buchen | Ja | Mindestens einer der neu gebuchten Artikel ist markiert |
| Deckel bezahlen | Nein | Ware wurde bereits bei der Buchung ausgegeben; nur eine Barzahlung kann `main` öffnen |
| Positive Bestandskorrektur | Ja | Markierter Artikel wird in das Lager aufgefüllt |
| Produkt mit positivem Anfangsbestand anlegen | Ja | Markierter Anfangsbestand wird eingelagert |
| Bestand eines Produkts erhöhen | Ja | Markierter Artikel wird eingelagert |
| Negative Bestandskorrektur | Optional | Nur bei aktivierter Option **Kleinteile-Lager öffnen**; reine Schwund-/Zählkorrekturen bleiben ohne Impuls |
| Storno eines Verkaufs | Ja | Der systemseitig zurückgebuchte markierte Bestand wird wieder eingelagert |
| Unveränderter Bestand | Nein | Keine Warenbewegung |
| Unbegrenzter Bestand | Nein | Kein physisch geführter Lagerbestand |
| Nicht markierter Artikel | Nein | Artikel liegt nicht in der zweiten Schublade |
| Manuelle Öffnung | Ja | Nach Passwortbestätigung; nur für Top-Admin sichtbar |

## API-Vertrag

Geschäftsvorgänge liefern eine geordnete, duplikatfreie Liste, zum Beispiel:

```json
{
  "drawer_targets": ["main", "small_parts"]
}
```

Eine leere Liste bedeutet, dass kein physischer Zugriff erforderlich ist. Das alte Feld `trigger_cash_drawer` wird aus Kompatibilitätsgründen noch akzeptiert, aber nicht als Hardwareanweisung vertraut. `open_small_parts_drawer` bleibt in Transaktionsantworten vorerst als Kompatibilitätsfeld erhalten.

## Manuelle Top-Admin-Steuerung

Unter **Admin → Einstellungen → Erweitert → Hardware-Service** stehen nur für Top-Admin zwei getrennte Aktionen bereit:

| Aktion | Ziel |
|---|---|
| Hauptschublade öffnen | `main` |
| Kleinteile-Lager öffnen | `small_parts` |

Beide Aktionen erfordern eine erneute Passwortbestätigung. Das Backend autorisiert das Ziel; der Browser sendet anschließend den lokalen Impuls.

## Sicherheits- und Fehlerregeln

| Fall | Verhalten |
|---|---|
| Unbekanntes Ziel | Wird abgelehnt |
| Browser-Origin nicht lokal gekoppelt | Wird vor dem Schaltimpuls abgelehnt; im Adminbereich kann ein Top-Admin den Browser koppeln |
| Beide Ziele auf demselben Adapter | Wird vom Agenten abgelehnt |
| Adapter nicht vorhanden | Agent sendet keinen Impuls |
| Agent nicht erreichbar | Der bereits gespeicherte Geschäftsvorgang bleibt gültig; der Hardwarefehler wird protokolliert |
| Mehrfach genanntes Ziel | Browser entfernt Duplikate vor dem Senden |
| Antwort nicht lesbar / Verbindung abgebrochen | Kein Wiederholungsimpuls; pro Ziel wird genau ein POST gesendet |
