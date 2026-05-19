# Benutzer- und Rollenrechte

Diese Datei ist die maßgebliche Referenz für das Berechtigungssystem. **TopAdmin** besitzt immer alle Rechte der darunterliegenden Rollen zusätzlich.

## Grundprinzip

- **Verkauf**: Kassenbetrieb ohne Admin-Bereich
- **Manager**: operative Admin-Funktionen für Mitglieder, Produkte, Gutscheine und Z-Bon
- **Admin**: volle operative Verwaltung inklusive Korrekturbuchungen, Vereinskonto und Systemkonfiguration
- **TopAdmin**: Systemhoheit, Rollenvergabe, Ext. Settings und Hard-Reset

## Systemlogik

- Beim Start wird automatisch nur der versteckte Benutzer **Kasse** angelegt.
- Der erste **TopAdmin** entsteht ausschließlich über den initialen Setup-Flow im Login.
- **TopAdmin** kann nicht regulär über die Benutzerverwaltung erstellt, geändert oder gelöscht werden.
- Mitgliedern mit Rolle kann ein verknüpftes Benutzerkonto zugeordnet werden.
- Die Rolle **TopAdmin** ist nicht an Mitglieder vergebbar.
- Der Admin-Bereich ist für **Manager**, **Admin** und **TopAdmin** erreichbar.
- Der Tab **Einstellungen** bündelt **Design**, **Datenpflege** und für **TopAdmin** zusätzlich **Ext. Settings**.

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
- Mitgliedsfotos hochladen oder ändern
- Mitgliedsguthaben aufladen
- Produkte anlegen, bearbeiten und löschen
- Produktbilder hochladen oder ändern
- Geschenk-Gutscheine erstellen
- den Bereich **Gutscheine → Verwaltung** ansehen
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
- Abschöpfungen außerhalb des Z-Bon-Modals direkt buchen
- die Tabs **Kategorien**, **Benutzer** und **Einstellungen** öffnen
- direkte Benutzerkonten anlegen, bearbeiten und löschen
- Passwörter für direkte Benutzerkonten neu vergeben
- Mitglieder mit Rolle in der Benutzerübersicht einsehen und deren Passwort neu setzen
- Mitglieder löschen
- App-Name, Farben und Logo anpassen
- den Bereich **Datenpflege** einsehen

Darf **nicht**:

- **Ext. Settings** öffnen oder verändern
- Rollen an Mitglieder oder TopAdmin-Rechte vergeben
- Hard-Reset ausführen

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
- den Hard-Reset in **Datenpflege** ausführen
- alle Admin-Rechte ohne Einschränkung nutzen

## Hinweise

- Der TopAdmin ist in der regulären Benutzerverwaltung nicht als normales bearbeitbares Benutzerkonto sichtbar.
- Der Systembenutzer **Kasse** ist ein versteckter Direktlogin für den Verkaufsmodus.
- Die Benutzerverwaltung zeigt direkte Benutzerkonten und Mitglieder mit Rolle gemeinsam an, behandelt diese aber unterschiedlich.
