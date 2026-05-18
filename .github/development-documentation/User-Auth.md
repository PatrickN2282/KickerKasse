# Benutzer- und Rollenrechte

Diese Datei ist die maßgebliche Referenz für das Berechtigungssystem. **TopAdmin** besitzt immer alle Rechte der darunterliegenden Rollen zusätzlich.

## Grundprinzip

- **Verkauf**: Kassenbetrieb ohne Admin-Bereich
- **Manager**: operative Admin-Funktionen für Mitglieder, Produkte, Gutscheine und Z-Bon
- **Admin**: volle operative Verwaltung inklusive Korrekturbuchungen, Vereinskonto und Design
- **TopAdmin**: Systemhoheit, Rollenvergabe, Ext. Settings und Hard-Reset

---

## Verkauf

- Darf sich normal mit eigenem Benutzer anmelden
- Darf sich über den Button **„Kasse anmelden“** als Benutzer **Kasse** direkt anmelden
- Darf die Kasse benutzen
- Darf Produkte verkaufen
- Darf Mitgliedsguthaben als Rabatt bzw. Zahlart verwenden
- Darf Geschenk-Gutscheine und Verzehrkarten in der Kasse einlösen
- Darf Deckel anlegen, bearbeiten und abrechnen
- Darf internes Material an der Kasse mit Notiz erfassen
- Darf sich aus der Kasse heraus über den Header-Button **„Login“** mit einem echten Benutzer anmelden
- Darf **nicht** in den Admin-Bereich wechseln

## Manager

Darf zusätzlich zu **Verkauf**:

- den Admin-Bereich direkt aus der Kasse heraus öffnen
- die Tabs **Mitglieder**, **Produkte**, **Gutscheine** und **Finanzen** öffnen
- Mitglieder anlegen und bearbeiten
- Mitgliedsguthaben aufladen
- Produkte anlegen, bearbeiten und löschen
- Geschenk-Gutscheine erstellen
- den Bereich **Gutscheine → Verwaltung** nur ansehen
- im Bereich **Gutscheine → Verwaltung** keine Änderungen durchführen
- im Tab **Finanzen** nur die Bereiche **Z-Bon** und **Z-Bons Verlauf** nutzen
- Z-Bons ansehen, vorbereiten, als HTML herunterladen und erstellen
- Abschöpfungen **im Z-Bon-Modal** vormerken
- als **„Erstellt von“** nur Benutzer/Mitglieder mit Rolle **Manager**, **Admin** oder **TopAdmin** auswählen
- als **Kassenprüfer** jedes Mitglied auswählen oder die Auswahl wieder entfernen

Darf **nicht**:

- Korrekturbuchungen durchführen oder einsehen
- Verzehrkarten erstellen
- Gutscheine bearbeiten
- das Gutscheinkonto / Materialkonto verwalten
- Abschöpfungen außerhalb des Z-Bon-Flows direkt buchen
- die Tabs **Kategorien**, **Benutzer**, **Design**, **Datenpflege** oder **Ext. Settings** öffnen
- Rollen vergeben oder Passwörter für Benutzerkonten außerhalb der erlaubten Member-Workflows verwalten

## Admin

Darf zusätzlich zu **Manager**:

- den Tab **Konto-Korrektur** öffnen
- Mitgliedsguthaben korrigieren
- Warenbestände korrigieren
- Geschenk-Gutscheine in der Verwaltung bearbeiten
- Verzehrkarten erstellen
- mehrere Verzehrkarten gleichzeitig erstellen
- für Verzehrkarten automatisch Produktartikel anlegen und Lagerbestand erhöhen
- den Bereich **Gutscheine → Gutscheinkonto** verwenden
- das **Gutscheinkonto** aufbuchen
- das **Materialkonto** im Finanzbereich einsehen
- Abschöpfungen außerhalb des Z-Bon-Modals direkt buchen
- die Tabs **Kategorien**, **Benutzer**, **Design** und **Datenpflege** öffnen
- Benutzer anlegen, bearbeiten und löschen
- Mitglieder löschen
- App-Name, Farben und Logo anpassen

Darf **nicht**:

- **Ext. Settings** öffnen oder verändern
- Rollen an Mitglieder oder TopAdmin-Rechte vergeben
- Hard-Reset ausführen

## TopAdmin

Darf zusätzlich zu **Admin**:

- den initialen TopAdmin-Setup ausführen
- Rollen an Mitglieder vergeben, ändern oder entfernen
- Mitgliederkonten mit Systemzugang initial ausstatten
- den Tab **Ext. Settings** öffnen
- Kassenlayout umschalten
- den Session-Timer konfigurieren
- den Hard-Reset in **Datenpflege** ausführen
- alle Admin-Rechte ohne Einschränkung nutzen

Hinweise:

- Der TopAdmin ist in der regulären Benutzerverwaltung nicht als normales bearbeitbares Benutzerkonto sichtbar.
- Der Systembenutzer **Kasse** ist ein versteckter Direktlogin für den Verkaufsmodus.
