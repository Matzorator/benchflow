# BenchFlow

BenchFlow ist ein praxisnahes Werkstatt- und Service-MVP fuer Reparaturprozesse.
Der Schwerpunkt liegt nicht auf generischem CRUD, sondern auf einem realistischen
Ablauf fuer Annahme, Bearbeitung, Dokumentation, Kostenvoranschlag, Rechnung und Ausgabe.

## Ziel des Projekts

BenchFlow ist gleichzeitig:
- ein benutzbares lokales Werkstatt-Tool
- ein Portfolio-Projekt mit Fokus auf HTML, CSS, JavaScript, Flask und SQLite
- ein nativer iOS-Client: die SwiftUI-App entstand parallel im Rahmen eines Swift-Kurses
  und setzt die Web-Oberflaeche als vollstaendige iPhone-App um

Wichtig dabei:
- klare Benutzerfuehrung statt Ein-Seiten-Ueberladung
- echte Werkstattobjekte wie Auftrag, Kunde, Geraet und Dokumentation
- einfacher, wartbarer MVP statt ueberladenem Framework-Stack

## Tech-Stack

| Bereich         | Technologie                        |
|-----------------|------------------------------------|
| Frontend        | HTML, CSS, JavaScript (serverseitig gerendert via Flask/Jinja2) |
| Backend         | Python + Flask                     |
| Datenbank       | SQLite                             |
| Native App      | Swift / SwiftUI (iOS 17+, macOS 14+) |
| Tests           | Python `unittest`                  |
| Build (iOS)     | XcodeGen (`project.yml`)           |

## Entstehung und Arbeitsweise

BenchFlow ist ein Eigenprojekt im Rahmen meiner Weiterbildung zum Fullstack Webentwickler.

Das Projekt wurde eigenstaendig konzipiert, strukturiert und entwickelt.
Bei der Umsetzung habe ich gezielt KI-gestuetzte Werkzeuge (u.a. als Pair-Programmer,
fuer Code-Reviews und zur Klaerung technischer Fragen) eingesetzt – aehnlich wie
Entwickler heute Linter, Dokumentation oder Stack Overflow nutzen.

Alle Architekturentscheidungen, der Workflow-Entwurf und das Debugging
lagen durchgehend bei mir.

## Lokaler Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 app.py
```

Danach im Browser oeffnen: `http://127.0.0.1:5000`

> Fuer den nativen iOS-Client: siehe `BenchFlowNative/README-Xcode.md`

## Projektstruktur

```text
app/
  __init__.py
  db.py
  routes.py
  api.py
  schema.sql
  static/
  templates/
tests/
BenchFlowNative/
instance/
README.md
```

Wichtige Dateien:
- `app/routes.py` – Flask-Routen, Formularverarbeitung, PDF-Erzeugung, Workflow-Logik
- `app/api.py` – JSON-API fuer den nativen SwiftUI-Client
- `app/db.py` – DB-Zugriff, Migrationen und Seed-Daten
- `app/schema.sql` – SQLite-Schema
- `app/static/styles.css` – Theme, Layout und Print-Styling
- `tests/test_app_flows.py` – Kernfluss-Tests
- `tests/test_api_flows.py` – API-Tests
- `BenchFlowNative/` – SwiftUI-App mit APIClient, Models, ViewModels und Views
- `BenchFlowNative/project.yml` – XcodeGen-Spezifikation fuer das iOS-17-Xcode-Projekt
- `BenchFlowNative/README-Xcode.md` – Startanleitung fuer Xcode und die Live-API

## Funktionsumfang

### Auftragsworkflow

- Dashboard mit Uebersicht und Schnellzugriffen
- eigene Listen fuer aktive Auftraege und Archiv
- Sortierung ueber Spaltenkoepfe (ASC/DESC)
- eigener Annahmefluss fuer neue Auftraege
- Detailseite als zentraler Arbeitsbereich pro Auftrag
- Statushistorie und Archivierung statt Loeschen

### Kunden und Geraete

- getrennte Kunden- und Geraetedaten mit erweitertem Stammdatenmodell
- Kundensuche bereits in der Auftragserfassung
- eigene Kundenliste mit Suche und Aktivfilter
- eigene Kundendetailseite mit bisherigen Auftraegen
- Demo-Datenbasis mit fiktiven Namen, Firmen und Adressen (datenschutzkonform)

### Dokumentation und Unterlagen

- mehrere Bilder und PDF-Unterlagen pro Auftrag
- Dokumenttypen: Kostenvoranschlag, Rechnung, Pruefprotokoll, Herstellerunterlage,
  Lieferschein, Servicebericht
- nachtraegliches Umtypisieren bestehender Dokumente

### Druck- und PDF-Flows

- Kundenbeleg und interner Werkstattbeleg (druckoptimiert)
- interner Label-/Stickerbereich mit QR-Code
- serverseitig erzeugter Kostenvoranschlag als PDF
- serverseitig erzeugte Rechnung als PDF
- KVA-Mailvorbereitung via `mailto:` mit vorausgefuellten Feldern
- freigegebener KVA kann direkt in eine Rechnung uebernommen werden

### JSON-API

Die REST-API verbindet Flask-Backend und SwiftUI-Client:

| Endpunkt | Beschreibung |
|---|---|
| `/api/meta` | Picker-Optionen (Status, Kategorien, Hersteller, Dokumenttypen) |
| `/api/dashboard` | Kennzahlen und zuletzt bearbeitete Auftraege |
| `/api/orders`, `/api/orders/<id>` | Auftragsliste und Auftragsdetail |
| `/api/archive` | Archivierte Auftraege |
| `/api/orders/<id>/quote` | KVA-Daten lesen und speichern |
| `/api/orders/<id>/invoice` | Rechnungsdaten lesen und speichern |
| `/api/orders/<id>/quote/email` | Vorbereiteter Mailflow fuer KVA |
| `/api/orders/<id>/attachments` | Bild-/PDF-Anhaenge verwalten |
| `/api/customers`, `/api/customers/<id>` | Kundenliste und Kundendetail |

### Nativer SwiftUI-Client (`BenchFlowNative/`)

Parallel zur Web-App entstand im Rahmen eines iOS-Kurses eine vollstaendige SwiftUI-App
fuer iPhone (iOS 17+):

- eigenes visuelles Design: dunkle Panel-Flaechen, cyanfarbene Akzente, flache
  BenchFlow-Navigation statt Standard-iOS-Chrome
- Auftragsliste, Archiv, Kundenliste und Detailseiten als native Screens
- KVA- und Rechnungsflow komplett nativ, inkl. direkter KVA-zu-Rechnung-Uebernahme
- Bild- und PDF-Anhaenge ueber die REST-API
- Light/Dark-Mode mit Theme-Spiegelung in eingebettete WebViews
- Fallback-Logik bei aelteren API-Versionen (z.B. fehlende Herstellerliste)
- XcodeGen-Projekt (`project.yml`) fuer reproduzierbares Xcode-Setup
- ATS-Ausnahme fuer lokalen Entwicklungsserver ohne globale HTTP-Freigabe

### UI (Web)

- technischer Darkmode, zuschaltbarer Lightmode mit Persistenz
- Listenansicht fuer Desktop
- Toast-Benachrichtigungen statt statischer Flash-Boxen

## Routenueberblick

| Route | Beschreibung |
|---|---|
| `/dashboard` | Uebersicht |
| `/orders` | Aktive Auftraege |
| `/orders/new` | Neuer Auftrag |
| `/orders/<id>` | Auftragsdetail |
| `/archive` | Archivierte Auftraege |
| `/customers` | Kundenliste |
| `/customers/<id>` | Kundendetailseite |
| `/orders/<id>/print` | Kundenbeleg |
| `/orders/<id>/print/internal` | Interner Beleg |

## Tests

```bash
python3 -m unittest discover -s tests -p "test_*.py"
```

Optionaler Syntax-Check:

```bash
python3 -m compileall app.py app tests
```

Die Test-Suite deckt ab: Auftragsanlage und -aktualisierung, Kundenfluss,
Bild- und PDF-Anhaenge, KVA- und Rechnungsworkflow, Archivierung,
Druck-Endpunkte sowie die komplette JSON-API.

## Aktueller Stand

BenchFlow ist deutlich ueber ein reines CRUD-MVP hinaus:
- Mehrseitenstruktur mit dokumentierten Werkstattablaeufen
- vollstaendiger KVA- und Rechnungsfluss inkl. PDF-Ausgabe
- parallele JSON-API fuer den nativen iOS-Client
- SwiftUI-App als vollwertige mobile Umsetzung
- datenschutzkonformes Demo-Datenset (keine echten Personen- oder Firmennamen)

## Bekannte Grenzen

- Mailversand ist bewusst ein vorbereiteter `mailto:`-Flow, kein SMTP-Versand
- KVA und Rechnung koennen bei Bedarf um weitere kaufmaennische Pflichtangaben
  erweitert werden
- die Test-Suite ist pragmatisch und nicht als vollstaendige Integrationsabdeckung gedacht

## Naechste sinnvolle Schritte

- optionale Versand- oder Zahlungsvermerke bei Rechnungen
- Firmen-/Ortsfilter oder Schnellaktionen in der Kundenliste
- Dokumentenverwaltung bei Bedarf um Freigabeprozesse erweitern
