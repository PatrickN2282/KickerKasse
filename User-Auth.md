# Benutzer- und Rollenrechte

Diese Datei ist die maßgebliche Referenz für das Berechtigungssystem. **TopAdmin** besitzt immer alle Rechte der darunterliegenden Rollen zusätzlich.

## Grundprinzip

- **Verkauf**: Kassenbetrieb ohne Admin-Bereich
- **Manager**: operative Admin-Funktionen für Mitglieder, Produkte, Gutscheine, Gäste-/Materiallisten und Z-Bon
- **Admin**: volle operative Verwaltung inklusive Korrekturbuchungen, Vereinskonto und Systemkonfiguration
- **TopAdmin**: Systemhoheit, Rollenvergabe, Ext. Settings und Hard-Reset

## Systemlogik

- Beim Start wird automatisch nur der versteckte Benutzer **Kasse** angelegt.
- Der erste **TopAdmin** entsteht ausschließlich über den initialen Setup-Flow im Login.
- **TopAdmin** kann nicht regulär über die Benutzerverwaltung erstellt, geändert oder gelöscht werden.
- Mitgliedern mit Rolle kann ein verknüpftes Benutzerkonto zugeordnet werden.
- Die Rolle **TopAdmin** ist nicht an Mitglieder vergebbar.
- Mitglieds-E-Mail-Adressen sind **nicht** global eindeutig und dürfen mit anderen
	Mitgliedern oder Benutzerkonten identisch sein.
- Der Admin-Bereich ist für **Manager**, **Admin** und **TopAdmin** erreichbar.
- Der Tab **Einstellungen** bündelt **Design** und für **TopAdmin** zusätzlich **Datenpflege**, **Ext. Settings**, **E-Mail** und **Audit-Log**.
- Benutzerkonten werden in der Benutzerverwaltung deaktiviert statt physisch gelöscht.
- Deaktivierte Benutzer bleiben sichtbar (über Filter) und können reaktiviert werden.

---

## Verkauf

- Darf sich normal mit eigenem Benutzer anmelden
- Darf sich über den Button **„Kasse anmelden“** als Benutzer **Kasse** direkt anmelden
- Darf die Kasse benutzen
- Darf Produkte verkaufen
- Darf bei als **variabel** konfigurierten Artikeln den Preis im Kassiervorgang eingeben; der eingegebene Betrag gilt nur für die konkrete Buchung
- Darf Mitgliedsguthaben als Rabatt bzw. Zahlart verwenden
- Darf Geschenk-Gutscheine und Verzehrkarten in der Kasse einlösen
- Darf Deckel anlegen, bearbeiten und abrechnen
- Darf internes Material ausschließlich über die reservierte Kategorie **Verbrauchsmaterial - Intern** mit 0,00 € und optionaler Notiz erfassen; der Artikelwert wird getrennt im Materialkonto protokolliert
- Darf sich aus der Kasse heraus über den Header-Button **„Login“** mit einem echten Benutzer anmelden
- Darf **nicht** in den Admin-Bereich wechseln

## Manager

Darf zusätzlich zu **Verkauf**:

- den Admin-Bereich direkt aus der Kasse heraus öffnen
- die Tabs **Mitglieder**, **Produkte**, **Gutscheine**, **Finanzen**, **Gästeliste** und **Verbrauchsmaterial** öffnen
- Mitglieder anlegen und bearbeiten
- Mitgliedsfotos hochladen oder ändern
- Mitgliedsguthaben aufladen
- Produkte anlegen, bearbeiten und löschen
- Produktbilder hochladen oder ändern
- Geschenk-Gutscheine erstellen
- den Bereich **Gutscheine → Verwaltung** ansehen
- im Bereich **Gutscheine → Verwaltung** keine Änderungen durchführen
- im Tab **Finanzen** nur die Bereiche **Z-Bon** und **Z-Bons Verlauf** nutzen
- die chronologische Gästeliste mit Datum, Gast, Gastgeber, Produkt/Anlass und Beleg ansehen und filtern
- die Transaktionsliste des internen Verbrauchsmaterials einschließlich Mengen, Notizen, Belegen und Buchungswerten ansehen und filtern
- Z-Bons ansehen, vorbereiten, als HTML herunterladen und erstellen
- Abschöpfungen **im Z-Bon-Modal** vormerken
- als **„Erstellt von“** nur Benutzer/Mitglieder mit Rolle **Manager**, **Admin** oder **TopAdmin** auswählen
- als **Kassenprüfer** jedes Mitglied auswählen oder die Auswahl wieder entfernen

Darf **nicht**:

- Korrekturbuchungen durchführen oder einsehen
- Verzehrkarten erstellen
- Gutscheine bearbeiten
- das Gutscheinkonto oder das interne Materialkonto im Finanzbereich einsehen bzw. verwalten; die separate, lesende Verbrauchsmaterialliste bleibt erlaubt
- Abschöpfungen außerhalb des Z-Bon-Flows direkt buchen
- die Tabs **Kategorien**, **Benutzer** oder **Einstellungen** öffnen
- Rollen vergeben oder Passwörter für Benutzerkonten außerhalb der erlaubten Member-Workflows verwalten
- **Ext. Settings** oder Hard-Reset nutzen

## Admin

Darf zusätzlich zu **Manager**:

- den Tab **Konto-Korrektur** im Finanzbereich öffnen
- Mitgliedsguthaben korrigieren
- Warenbestände korrigieren
- Geschenk-Gutscheine in der Verwaltung bearbeiten
- Verzehrkarten erstellen
- mehrere Verzehrkarten gleichzeitig erstellen
- für Verzehrkarten automatisch Produktartikel anlegen und Lagerbestand erhöhen
- den Bereich **Gutscheine → Gutscheinkonto** verwenden
- das **Gutscheinkonto** aufbuchen
- das **Materialkonto** im Finanzbereich einsehen
- die reguläre Transaktionshistorie filtern, als HTML-Vorschau öffnen und als CSV oder PDF herunterladen
- Abschöpfungen außerhalb des Z-Bon-Modals direkt buchen
- die Tabs **Kategorien**, **Benutzer** und **Einstellungen** öffnen
- direkte Benutzerkonten anlegen, bearbeiten, deaktivieren und reaktivieren
- Passwörter für direkte Benutzerkonten neu vergeben
- Mitglieder mit Rolle in der Benutzerübersicht einsehen und deren Passwort neu setzen
- Mitglieder löschen
- App-Name, Farben und Logo anpassen

Darf **nicht**:

- **Ext. Settings** öffnen oder verändern
- Rollen an Mitglieder oder TopAdmin-Rechte vergeben
- den Bereich **Datenpflege** öffnen
- Datenbank-Backups exportieren oder wiederherstellen
- Hard-Reset ausführen
- das eigene Benutzerkonto deaktivieren

## TopAdmin

Darf zusätzlich zu **Admin**:

- den initialen TopAdmin-Setup ausführen
- Rollen an Mitglieder vergeben, ändern oder entfernen
- Mitgliedskonten mit Systemzugang initial ausstatten
- E-Mail-Adressen für rollenbasierte Mitgliedskonten pflegen
- den Bereich **Ext. Settings** im Tab **Einstellungen** öffnen
- Kassenlayout umschalten
- den Session-Timer konfigurieren
- Geschäftsdaten pflegen
- den automatischen Backup-Mail-Versand konfigurieren
- zusätzliche E-Mail-Empfänger für Lagerbestands- und Backup-Mails pflegen
- den Hard-Reset in **Datenpflege** ausführen
- Datenbank-Backups exportieren und wiederherstellen
- Audit-Log-Einträge einsehen
- alle Admin-Rechte ohne Einschränkung nutzen
- den Kassen-Direktlogin zentral deaktivieren

### Neue/aktualisierte Features

- Zusätzliche Empfänger für Lagerbestands-Mails und Backup-Mails
- Automatischer E-Mail-Versand für Z-Bons und Datenbank-Backups
- Audit-Log für nachvollziehbare Admin-Änderungen
- Import/Export für Datenbestände
- Hardware-Service für den lokalen Kassen-PC

## Hinweise

### API-Grenzen ab Version 1.6.4

Die Navigationsrechte gelten auch bei direkten API-Aufrufen. TopAdmin erbt die hier genannten Admin-Rechte.

| Bereich / Endpunkt | Verkauf | Manager | Admin / TopAdmin |
|---|---|---|---|
| `GET /api/members/selection` | Ja | Ja | Ja |
| Vollständige Mitgliederliste und Einzelprofil | Nein | Ja | Ja |
| Mitgliederstatistik, reguläre Transaktionsliste/-details, Tagesdetailstatistik, gefilterte Historie, Umsatzstatistik und Exporte | Nein | Nein | Ja |
| Z-Bon-Vorschau, Erstellung, Verlauf, Berichtsdateien/-versand und zugehörige Tageszusammenfassung | Nein | Ja | Ja |
| Allgemeine Bargeldeinlage/-abschöpfung, Bargeldeinträge und Saldenabruf außerhalb des Z-Bon-Ablaufs | Nein | Nein | Ja |
| `GET /api/admin/vouchers/material-transactions` (operative Materialliste) | Nein | Ja | Ja |
| Materialkonto, Gutscheinkonto und Schedulerstatus | Nein | Nein | Ja |

Die Mitgliedsauswahl liefert ausschließlich ID, Mitglieds-/Mitgliedschaftsnummer, Namen, Bildpfad, Rabattberechtigung und Guthaben. Kontaktinformationen, Notizen, Rollen und Kontozustände gehören zur Verwaltungsantwort. Die Materialliste enthält weiterhin Menge, Materialwert, Notiz, Bearbeiter, Mitgliedsname und Belegnummer, aber keine Zahlungsaufteilung des zugehörigen Verkaufs. Die ausdrücklich erlaubten Z-Bon-Berichte behalten ihren für den Abschluss erforderlichen Inhalt.

Mitgliederrollen können ausschließlich durch TopAdmin gesetzt, geändert oder entfernt werden; auch ein explizites `null` oder das erneute Senden derselben Rolle ist eine geschützte Eingabe. Normale Namens-/Kontaktänderungen oder Passwortneuvergabe erhalten den Aktivierungszustand und die Benutzerrolle. Eine tatsächliche Rollenentfernung deaktiviert den Zugang; eine neue Rollenvergabe durch TopAdmin aktiviert ihn. Das bloße Mitsenden einer unveränderten Rolle reaktiviert ein deaktiviertes Konto nicht.

Bei verknüpften Konten erlaubt `/api/users/{id}` ausschließlich Passwortneuvergabe. Stammdaten und Rollen werden über die Mitgliederverwaltung gepflegt; die direkten Deaktivierungs-/Reaktivierungsaktionen gelten für direkte Benutzerkonten. `is_active`, `member_id` und `password_hash` werden im allgemeinen Benutzerupdate ausdrücklich zurückgewiesen. TopAdmin kann über keinen dieser Verwaltungswege verändert oder über Schreibweisen wie `top_admin` vergeben werden. Die Neuanlage eines Zugangs zu einem importierten Mitglied mit historischer Rolle ist TopAdmin vorbehalten.

Ab 1.6.7 prüfen geschützte API-Wege einschließlich Produkt-/Mitgliedsbildern das aktive Konto und seine Sitzungsfassung in der Datenbank. Rollen werden aus dem aktuellen Konto gelesen. Passwortänderung, erfolgreicher Reset, Rollenwechsel und Deaktivierung widerrufen vorherige Sitzungen und offene Resetlinks, auch bei verknüpften Mitgliedskonten. Reaktivierung stellt alte Sitzungen nicht wieder her. Nach dem Upgrade ist eine erneute Anmeldung notwendig. Bereits geladene Ansichten reagieren beim nächsten geschützten API-Aufruf; ein Push-Logout ist nicht vorgesehen. Öffentliche Login-/Setup- und Brandingressourcen sowie der bewusst vorgesehene Kassen-Direktzugang bleiben verfügbar.

### Anmelde- und Resetlimits ab 1.6.7

Alle Fenster dauern 60 Sekunden und werden durch abgewiesene Versuche nicht verlängert. Die Zähler liegen mit gehashten Schlüsseln in der Datenbank und gelten auch über mehrere Prozesse und Neustarts hinweg.

| Vorgang | Grenze pro Zeitfenster | Rückmeldung |
|---|---|---|
| Persönlicher Login | 5 Versuche pro normalisiertem Kontonamen, zusätzlich 30 pro Herkunfts-IP | HTTP 429 mit Wartezeit und `Retry-After` |
| Passwortbestätigung innerhalb einer Sitzung | Nach 5 falschen Bestätigungen pro bestätigendem Konto begrenzt; richtige Bestätigungen zählen nicht | HTTP 429 mit Wartezeit |
| Resetanforderung | 5 pro Herkunfts-IP und höchstens eine pro normalisierter E-Mail-Adresse | Identische generische Antwort, auch für unbekannte Adressen, Wiederholungen und Versandfehler |
| Einlösen eines Resetlinks | 10 Versuche pro Herkunfts-IP | HTTP 429 mit Wartezeit |

Die Herkunft ist `request.client.host`. Hinter einem Reverse-Proxy nur vertrauenswürdige Proxy-Adressen für weitergereichte Client-IP-Header konfigurieren (`FORWARDED_ALLOW_IPS` bei Uvicorn); öffentlich angelieferte Header nicht pauschal vertrauen. Ohne passende Proxy-Konfiguration können mehrere Nutzer dasselbe Herkunftsbudget teilen.

„TopAdmin-Passwort vergessen?“ öffnet den Resetdialog ohne vorherige Fehlversuche. Ein Link gilt 60 Minuten und nur einmal. Erfolgreicher Reset sperrt alle weiteren offenen Links desselben Kontos und speichert Passwort, Tokenverbrauch, Sitzungswiderruf und Audit gemeinsam. Ein technischer Fehler rollt diese Änderungen zusammen zurück. Es entsteht keine dauerhafte Kontosperre aus dem Fehlversuchszähler.

- Der TopAdmin ist in der regulären Benutzerverwaltung nicht als normales bearbeitbares Benutzerkonto sichtbar.
- Der Systembenutzer **Kasse** ist ein versteckter Direktlogin für den Verkaufsmodus.
- Die Benutzerverwaltung zeigt direkte Benutzerkonten und Mitglieder mit Rolle gemeinsam an, behandelt diese aber unterschiedlich.

## Buchungswege ab 1.6.11

Die bestehenden Rollenrechte für Verkauf, Deckel und Gutscheine gelten weiter. Gäste können ausschließlich innerhalb des Verkaufs an der jeweiligen Position gespeichert werden; Beleg- und Positionsreferenzen bestimmt der Server. Der frühere separate POST-Endpunkt für Gäste liefert HTTP 409 mit Aktualisierungshinweis. Die Gastübersicht und bekannte Gäste bleiben lesbar. Deckel sind Barvorgänge ohne Mitgliedsauswahl, Gäste oder Verzehrkarten; die API weist nicht unterstützte Zusatzfelder zurück.

## Import/Export und Mitgliedskonten

- Beim Standard-Import/Export werden Mitglieder, Produkte und Kategorien übertragen,
	Benutzerkonten jedoch bewusst **nicht**.
- Nach einem Import darf ein Mitglied mit historischer Rolle weiter bearbeitet werden,
	auch wenn das frühere verknüpfte Benutzerkonto in der Zielumgebung nicht existiert.
- Wird bei Rollenvergabe ein Benutzerkonto (neu) erzeugt und dessen E-Mail wäre als
	Benutzer-E-Mail bereits belegt, bleibt die Mitglieder-Bearbeitung funktionsfähig;
	das System führt in diesem Fall keine kollidierende Benutzer-E-Mail-Setzung durch.

## Buchungswiederholung und Kassenabschluss (1.6.12–1.6.13)

Das aktuelle Frontend kennzeichnet jede Finanzbuchung mit einer UUID (`Idempotency-Key`). Buchung und Antwortjournal werden gemeinsam bestätigt. Die Statusabfrage `/api/transactions/operations/{kennung}` ist nur für den aktiven, ursprünglichen Benutzer zugänglich; fremde Kennungen geben keine Buchungsdaten preis. Ein anderer Inhalt mit derselben Kennung wird abgewiesen. Passwörter werden weder im Fingerprint berücksichtigt noch im Browserjournal gespeichert. Eine neue Buchung durchläuft weiterhin die jeweilige Rollen- und Passwortprüfung; ein bereits bestätigtes Ergebnis kann der ursprüngliche angemeldete Benutzer erneut abrufen.

Offene Kennungen und Prüfsummen liegen im Sitzungsspeicher des jeweiligen Browser-Tabs, getrennt nach Benutzer. Bei einem unklaren Ausgang denselben Tab offen lassen und die Buchung unverändert erneut bestätigen oder den angebotenen Status prüfen. Der Wiederabruf löst keinen weiteren Schubladenimpuls aus. Alte Frontends ohne Kennung besitzen diesen Schutz nicht und müssen nach dem Update neu geladen werden.

Für den Z-Bon werden Ersteller aus den bestehenden berechtigten Finanzpersonen und Prüfer aus bestehenden Mitgliedern ausgewählt. Die API nimmt IDs statt freier Namensangaben an und speichert die aufgelösten Namen im Bericht. Die bisherige fachliche Regel bleibt bestehen: Ein prüfendes Mitglied braucht keinen Finanzzugang. Stückelungen, Stückzahlen, Centbeträge und Differenzbegründung werden serverseitig geprüft.

## Mitgliederarchiv (1.6.14)

Admins archivieren und reaktivieren reguläre Mitglieder. Bei hinterlegter Systemrolle oder verknüpftem Benutzerkonto ist dies dem Top-Admin vorbehalten. Ein Top-Admin-Mitglied wird nicht über das Archiv deaktiviert. Restguthaben blockiert die Archivierung, bis es über den vorgesehenen dokumentierten Weg fachlich geklärt ist.

Archivierung erhält alle historischen Referenzen und deaktiviert einen verknüpften Zugang im selben Commit wie den Archiveintrag und das Audit. Der bestehende Sitzungswiderruf macht dessen alte Anmeldungen ungültig. Das Mitglied verschwindet aus aktiven Auswahllisten; Verkäufe, Gastzuordnungen und Aufladungen dürfen es nicht neu verwenden. Wiederherstellung aktiviert einen deaktivierten Zugang nicht automatisch. Historische Belege und Berichte bleiben lesbar.
