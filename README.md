# BenchFlow

BenchFlow ist ein praxisnahes Werkstatt- und Service-MVP fuer Reparaturprozesse. Der Schwerpunkt liegt nicht auf generischem CRUD, sondern auf einem realistischen Ablauf fuer Annahme, Bearbeitung, Dokumentation, Kostenvoranschlag, Rechnung und Ausgabe.

## Ziel des Projekts

BenchFlow ist gleichzeitig:
- ein benutzbares lokales Werkstatt-Tool
- ein Portfolio-Projekt mit Fokus auf HTML, CSS, JavaScript, Flask und SQLite

Wichtig dabei:
- klare Benutzerfuehrung statt Ein-Seiten-Ueberladung
- echte Werkstattobjekte wie Auftrag, Kunde, Geraet und Dokumentation
- einfacher, wartbarer MVP statt ueberladenem Framework-Stack

## Tech-Stack

- Frontend: serverseitige Templates mit HTML, CSS und etwas JavaScript
- Backend: Python + Flask
- Datenbank: SQLite
- Tests: `unittest`

## Lokaler Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 app.py
```

Danach im Browser oeffnen:

- `http://127.0.0.1:5000`

## Projektstruktur

```text
app/
  __init__.py
  db.py
  routes.py
  schema.sql
  static/
  templates/
tests/
instance/
README.md
Start.md
```

Wichtige Dateien:
- `app/routes.py`: zentrale Flask-Routen, Formularverarbeitung, PDF-Erzeugung, Workflow-Logik
- `app/db.py`: DB-Zugriff, Migrationen und Seed-Daten
- `app/schema.sql`: SQLite-Schema
- `app/templates/`: Seiten und Druckansichten
- `app/static/styles.css`: Theme, Layout und Print-Styling
- `tests/test_app_flows.py`: Kernfluss-Tests

## Funktionsumfang

### Auftragsworkflow

- Dashboard mit Uebersicht und Schnellzugriffen
- eigene Listen fuer aktive Auftraege und Archiv
- eigener Annahmefluss fuer neue Auftraege
- Detailseite als zentraler Arbeitsbereich pro Auftrag
- Statushistorie und Archivierung statt Loeschen

### Kunden und Geraete

- getrennte Kunden- und Geraetedaten
- erweiterte Kundenstammdaten mit Firma, Adresse, Kontaktweg und interner Kundennotiz
- Kundensuche bereits in der Auftragserfassung
- eigene Kundendetailseite mit bisherigen Auftraegen

### Dokumentation und Unterlagen

- mehrere Bilder pro Auftrag
- PDF-Unterlagen pro Auftrag
- Dokumenttypen wie:
  - Kostenvoranschlag
  - Rechnung
  - Pruefprotokoll
  - Herstellerunterlage
  - Lieferschein
  - Servicebericht
- Bezug zum Auftrag direkt am Dokument
- nachtraegliches Umtypisieren bestehender PDF-Dokumente

### Druck- und PDF-Flows

- reduzierter Kundenbeleg
- interner Werkstattbeleg
- interner Label-/Stickerbereich mit QR-Code
- serverseitig erzeugter Kostenvoranschlag als PDF
- serverseitig erzeugte Rechnung als PDF
- KVA-Mailvorbereitung ueber `mailto:` mit vorausgefuelltem Empfaenger, Betreff und Mailtext

### UI

- technischer Darkmode
- zuschaltbarer Lightmode mit Persistenz
- Listenansicht fuer Desktop statt Kartenansicht
- Toast-Benachrichtigungen statt statischer Flash-Boxen

## Routenueberblick

- `/dashboard`: Uebersicht
- `/orders`: aktive Auftraege
- `/orders/new`: neuer Auftrag
- `/orders/<id>`: Detailseite eines Auftrags
- `/archive`: archivierte Auftraege
- `/customers/<id>`: Kundendetailseite
- `/orders/<id>/print`: Kundenbeleg
- `/orders/<id>/print/internal`: interner Beleg

## Tests

Testlauf:

```bash
python3 -m unittest discover -s tests -p "test_*.py"
```

Optionaler Syntax-Check:

```bash
python3 -m compileall app.py app tests
```

Die aktuelle Suite deckt unter anderem ab:
- Auftrag anlegen
- Auftrag aktualisieren
- Kundenuebernahme in der Erfassung
- Kundendetailseite
- Bild- und PDF-Anhaenge
- Dokumenttypen und Dokumenthinweise
- KVA-Workflow
- vorbereiteten KVA-Mailfluss
- Rechnungsworkflow
- Archivieren und Wiederherstellen
- Kunden- und internen Beleg

## Aktueller Stand

BenchFlow ist inzwischen deutlich ueber ein reines CRUD-MVP hinaus:
- Mehrseitenstruktur statt Sammeldashboard
- dokumentierte Werkstattablaeufe
- Kunden-, KVA- und Rechnungslogik
- Druck- und PDF-Pfade fuer Kunden- und interne Nutzung
- Demo-Daten fuer realistischeres Testen

## Bekannte Grenzen

- Mailversand ist aktuell bewusst ein vorbereiteter `mailto:`-Flow, kein SMTP-Versand
- Rechnungen und KVA sind gestalterisch angenaehert, koennen aber bei Bedarf noch um weitere kaufmaennische Angaben erweitert werden
- die Test-Suite ist bewusst pragmatisch und nicht als vollstaendige Integrationsabdeckung gedacht

## Naechste sinnvolle Schritte

- optionale Versand- oder Zahlungsvermerke bei Rechnungen
- Kundenliste als eigener Bereich mit schneller Suche und direktem Zugriff auf offene Vorgange
- Dokumentenverwaltung weiter verfeinern, falls zusaetzliche Kategorien oder Freigabeprozesse noetig werden
