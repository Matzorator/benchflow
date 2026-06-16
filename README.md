<<<<<<< HEAD Test
# 🔧 BenchFlow - Werkstatt & Service MVP

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![Swift](https://img.shields.io/badge/Swift-F05138?style=for-the-badge&logo=swift&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)

> **Ein praxisnahes Werkstatt- und Service-MVP für Reparaturprozesse. Kein generisches CRUD –
> sondern ein realistischer Ablauf für Annahme, Bearbeitung, Dokumentation, Kostenvoranschlag,
> Rechnung und Ausgabe. Inklusive nativer iOS-App (SwiftUI).**

---

## 🎬 Demo

### Dashboard
![Dashboard](screenshots/dashboard.png)
*Zentrale Übersicht mit Kennzahlen und Schnellzugriffen*

### Auftragsdetail
![Auftragsdetail](screenshots/order_detail.png)
*Detailseite als Arbeitsbereich: Status, KVA, Rechnung, Anhänge in einem View*

### Nativer iOS-Client
![SwiftUI App](screenshots/swiftui_app.png)
*BenchFlow als iPhone-App – gleiche Daten, native SwiftUI-Oberfläche*

### PDF-Ausgabe
![PDF Kostenvoranschlag](screenshots/pdf_kva.png)
*Serverseitig erzeugter Kostenvoranschlag als druckfertiges PDF*

---

## ⚡ Quick Start

```bash
# 1. Repository klonen
git clone https://github.com/Matzorator/benchflow.git
cd benchflow

# 2. Virtualenv & Abhängigkeiten
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. App starten
python3 app.py
```

**Dann im Browser öffnen:** `http://127.0.0.1:5000` 🎉

> Für den nativen iOS-Client: siehe [`BenchFlowNative/README-Xcode.md`](BenchFlowNative/README-Xcode.md)

---

## ✨ Highlights

- 📋 **Echter Werkstattworkflow** – Annahme → Bearbeitung → KVA → Rechnung → Ausgabe
- 📄 **PDF-Erzeugung** – Kostenvoranschlag und Rechnung serverseitig als druckfertiges PDF
- 📱 **Native iOS-App** – SwiftUI-Client mit vollständiger API-Anbindung (Swift-Kurs-Projekt)
- 🔍 **Kundenmanagement** – Stammdaten, Suchfluss, Auftragshistorie
- 🗂️ **Dokumentenverwaltung** – Bilder & PDFs pro Auftrag, typisiert und umtypisierbar
- 🧪 **Getesteter Code** – `unittest`-Suite mit über 30 abgedeckten Flows

<details>
<summary>📋 Alle Features anzeigen</summary>

### 📋 Auftragsworkflow
- ✅ Dashboard mit Kennzahlen und Schnellzugriffen
- ✅ Eigene Listen für aktive Aufträge und Archiv
- ✅ Sortierung über Spaltenköpfe (ASC/DESC)
- ✅ Annahmefluss für neue Aufträge mit Kundensuche
- ✅ Detailseite als zentraler Arbeitsbereich pro Auftrag
- ✅ Statushistorie und Archivierung statt Löschen

### 👥 Kunden & Geräte
- ✅ Getrennte Kunden- und Gerätedaten
- ✅ Erweitertes Stammdatenmodell (Firma, Adresse, Kontaktweg, interne Notiz)
- ✅ Kundensuche direkt in der Auftragserfassung
- ✅ Kundenliste mit Suche und Aktivfilter
- ✅ Kundendetailseite mit Auftragshistorie
- ✅ Datenschutzkonformes Demo-Datenset (keine echten Personen)

### 📄 Dokumente & Anhänge
- ✅ Mehrere Bilder und PDFs pro Auftrag
- ✅ Dokumenttypen: KVA, Rechnung, Prüfprotokoll, Herstellerunterlage, Lieferschein, Servicebericht
- ✅ Nachträgliches Umtypisieren bestehender Dokumente

### 🖨️ Druck & PDF
- ✅ Kundenbeleg und interner Werkstattbeleg (druckoptimiert)
- ✅ Label-/Stickerbereich mit QR-Code
- ✅ Serverseitig erzeugter KVA als PDF
- ✅ Serverseitig erzeugte Rechnung als PDF
- ✅ KVA-Mailvorbereitung via `mailto:` mit vorausgefüllten Feldern
- ✅ Direkte KVA-zu-Rechnung-Übernahme mit Bestätigungsdialog

### 📱 Nativer SwiftUI-Client
- ✅ Vollständige iPhone-App (iOS 17+) mit REST-API-Anbindung
- ✅ Eigenes visuelles Design: dunkle Panels, Cyan-Akzente, flache BenchFlow-Navigation
- ✅ Alle Kernflows nativ: Aufträge, Archiv, Kunden, KVA, Rechnung, Anhänge
- ✅ Light/Dark-Mode mit Theme-Spiegelung in eingebettete WebViews
- ✅ XcodeGen-Projekt für reproduzierbares Xcode-Setup
- ✅ Fallback-Logik bei älteren API-Versionen

### 🌐 JSON-API
- ✅ REST-API als Bindeglied zwischen Flask-Backend und SwiftUI-Client
- ✅ Vollständige Abdeckung: Dashboard, Aufträge, Archiv, Kunden, KVA, Rechnung, Anhänge
- ✅ `/api/meta` liefert Picker-Optionen für Status, Kategorien, Hersteller, Dokumenttypen

### 🎨 UI (Web)
- ✅ Technischer Darkmode, zuschaltbarer Lightmode mit Persistenz
- ✅ Listenansicht für Desktop
- ✅ Toast-Benachrichtigungen statt statischer Flash-Boxen

</details>

---

## 🗺️ Roadmap

### 🎯 Version 1.0 (Aktuell)
- ✅ Vollständiger Auftragsworkflow
- ✅ KVA- und Rechnungsflow mit PDF-Ausgabe
- ✅ Dokumentenverwaltung mit Typisierung
- ✅ JSON-API für nativen iOS-Client
- ✅ SwiftUI-App (iOS 17+)

### 🔄 Version 2.0 (Geplant)
- 🔨 **Zahlungs- und Versandvermerke** bei Rechnungen
- 🔨 **SMTP-Mailversand** statt `mailto:`-Flow
- 🔨 **Firmen-/Ortsfilter** in der Kundenliste
- 🔨 **Erweiterte Dokumentenfreigabe** mit Genehmigungsprozess

---

## 🛠️ Tech-Stack

| Bereich | Technologie |
|---|---|
| Frontend | HTML, CSS, JavaScript (serverseitig via Flask/Jinja2) |
| Backend | Python + Flask |
| Datenbank | SQLite |
| Native App | Swift / SwiftUI (iOS 17+, macOS 14+) |
| Tests | Python `unittest` |
| Build (iOS) | XcodeGen (`project.yml`) |

---

## 🌐 API-Übersicht

| Endpunkt | Beschreibung |
|---|---|
| `/api/meta` | Picker-Optionen (Status, Kategorien, Hersteller, Dokumenttypen) |
| `/api/dashboard` | Kennzahlen und zuletzt bearbeitete Aufträge |
| `/api/orders`, `/api/orders/<id>` | Auftragsliste und Auftragsdetail |
| `/api/archive` | Archivierte Aufträge |
| `/api/orders/<id>/quote` | KVA-Daten lesen und speichern |
| `/api/orders/<id>/invoice` | Rechnungsdaten lesen und speichern |
| `/api/orders/<id>/quote/email` | Vorbereiteter Mailflow für KVA |
| `/api/orders/<id>/attachments` | Bild-/PDF-Anhänge verwalten |
| `/api/customers`, `/api/customers/<id>` | Kundenliste und Kundendetail |

---

## 🌐 Web-Routen

| Route | Beschreibung |
|---|---|
| `/dashboard` | Übersicht |
| `/orders` | Aktive Aufträge |
| `/orders/new` | Neuer Auftrag |
| `/orders/<id>` | Auftragsdetail |
| `/archive` | Archivierte Aufträge |
| `/customers` | Kundenliste |
| `/customers/<id>` | Kundendetailseite |
| `/orders/<id>/print` | Kundenbeleg |
| `/orders/<id>/print/internal` | Interner Beleg |

---

## 📁 Projektstruktur

```
benchflow/
│
├── app.py                      # App-Einstiegspunkt
├── requirements.txt
├── README.md
│
├── app/
│   ├── __init__.py
│   ├── routes.py               # Flask-Routen, PDF-Erzeugung, Workflow-Logik
│   ├── api.py                  # JSON-API für den SwiftUI-Client
│   ├── db.py                   # DB-Zugriff, Migrationen, Seed-Daten
│   ├── schema.sql              # SQLite-Schema
│   ├── static/
│   │   └── styles.css          # Theme, Layout, Print-Styling
│   └── templates/              # Jinja2-Seiten und Druckansichten
│
├── tests/
│   ├── test_app_flows.py       # Kernfluss-Tests
│   └── test_api_flows.py       # API-Tests
│
├── BenchFlowNative/            # SwiftUI-App
│   ├── project.yml             # XcodeGen-Konfiguration
│   ├── README-Xcode.md         # Startanleitung für Xcode
│   └── BenchFlowNative/        # Quellcode: APIClient, Models, ViewModels, Views
│
└── instance/                   # SQLite-Datenbankdatei (lokal, nicht versioniert)
```

---

## 🧪 Tests
=======
# BenchFlow - React/Express Version

BenchFlow ist ein praxisnahes Werkstatt- und Service-MVP fuer Reparaturprozesse. Diese Variante nutzt moderne Web-Technologien mit React, Express und einer nativen SwiftUI-App.

Der Schwerpunkt liegt nicht auf generischem CRUD, sondern auf einem realistischen Ablauf fuer Annahme, Bearbeitung, Dokumentation, Kostenvoranschlag, Rechnung und Ausgabe.

## Ziel des Projekts

BenchFlow ist gleichzeitig:
- ein benutzbares lokales Werkstatt-Tool
- ein Portfolio-Projekt mit Fokus auf React, Node.js, Express und modernem Frontend
- eine Production-ready Architektur

Wichtig dabei:
- klare Benutzerfuehrung statt Ein-Seiten-Ueberladung
- echte Werkstattobjekte wie Auftrag, Kunde, Geraet und Dokumentation
- moderne Entwickler-Experience mit Vite und React

## Tech-Stack

### Web
- **Frontend:** React + Vite
- **Backend:** Node.js + Express
- **Datenbank:** SQLite oder PostgreSQL
- **Styling:** CSS3 mit Legacy-CSS Migration

### Mobile
- **Native iOS/macOS App:** Swift / SwiftUI (iOS 17+, macOS 14+)
- **Integration:** REST API zum Express-Backend

## Struktur

```text
frontend/           # React + Vite SPA
  src/
    components/
    pages/
    App.jsx
  package.json
  vite.config.js

BenchFlowNative/    # SwiftUI Native App
  Sources/
    Views/
    ViewModels/
    Support/

README.md
.gitignore
```

## Lokaler Start

### Web-Version (React + Express)

```bash
# Backend
npm install
npm run dev

# Frontend (in separatem Terminal)
cd frontend
npm install
npm run dev
```

Danach im Browser oeffnen:
- Frontend: `http://localhost:5173`
- Backend: `http://localhost:3000`

### Native App (SwiftUI)

Siehe `BenchFlowNative/README-Xcode.md` fuer Xcode Setup-Anweisungen.

Wichtige Dateien:
- `app/routes.py`: zentrale Flask-Routen, Formularverarbeitung, PDF-Erzeugung, Workflow-Logik
- `app/api.py`: JSON-API fuer den nativen SwiftUI-Client
- `app/db.py`: DB-Zugriff, Migrationen und Seed-Daten
- `app/schema.sql`: SQLite-Schema
- `app/templates/`: Seiten und Druckansichten
- `app/static/styles.css`: Theme, Layout und Print-Styling
- `tests/test_app_flows.py`: Kernfluss-Tests
- `tests/test_api_flows.py`: API-Tests fuer Dashboard, Auftrags-, Kunden-, KVA-, Rechnungs- und Attachment-Flows
- `BenchFlowNative/`: SwiftUI-App-Struktur mit `APIClient`, Models, ViewModels, Views und ATS-`Info.plist`
  - `BenchFlowNative/project.yml`: XcodeGen-Spezifikation fuer ein iOS-17-Xcode-Projekt
  - `BenchFlowNative/README-Xcode.md`: kurzer Startfaden fuer Xcode und die Live-API

## Funktionsumfang

### Auftragsworkflow

- Dashboard mit Uebersicht und Schnellzugriffen
- eigene Listen fuer aktive Auftraege und Archiv
- Sortierung in Auftrags- und Archivlisten direkt ueber die Spaltenkoepfe mit ASC/DSC
- eigener Annahmefluss fuer neue Auftraege
- Detailseite als zentraler Arbeitsbereich pro Auftrag
- Statushistorie und Archivierung statt Loeschen

### Kunden und Geraete

- getrennte Kunden- und Geraetedaten
- erweiterte Kundenstammdaten mit Firma, Adresse, Kontaktweg und interner Kundennotiz
- Kundensuche bereits in der Auftragserfassung
- eigene Kundenliste mit Suche und Filter fuer aktive bzw. alle Kunden
- eigene Kundendetailseite mit bisherigen Auftraegen
- Demo-Kundendaten bewusst mit klar fiktiven Namen, Firmen, Adressen und Maildomains angelegt

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
- freigegebener KVA kann direkt in eine Rechnung uebernommen und als Rechnungs-PDF erzeugt werden
- falls bereits eine Rechnung existiert, weist die Detailseite vor dem direkten KVA-Import auf das Ueberschreiben hin und fragt dies bestaetigt ab

### JSON-API und nativer Client

- `/api/meta` liefert Picker-Optionen fuer Status, Kategorien, Dokumenttypen und Kontaktwege
- `/api/dashboard` liefert Kennzahlen und zuletzt bearbeitete Auftraege fuer den nativen Startbildschirm
- `/api/orders`, `/api/orders/<id>` sowie `/api/archive` bilden aktive und archivierte Auftragslisten plus Detaildaten als JSON ab
- `/api/orders/<id>/quote`, `/api/orders/<id>/invoice`, `/api/orders/<id>/quote/email` spiegeln KVA-, Rechnungs- und Mailvorbereitungsfluss fuer den SwiftUI-Client
- `/api/orders/<id>/attachments` und `/api/orders/<id>/attachments/<media_id>` decken Upload und Loeschen von Bild-/PDF-Anhaengen ab
- `/api/customers` und `/api/customers/<id>` liefern Kundenliste und Kundendetails fuer die native App
- `BenchFlowNative/Info.plist` enthaelt eine gezielte ATS-Ausnahme fuer `http://192.168.178.31` ohne globale Freigabe unsicherer Loads
- `BenchFlowNative/project.yml` erzeugt daraus ein iOS-17-App-Target fuer Xcode, damit die SwiftUI-App nicht nur als lose Quelltextsammlung vorliegt
- Die XcodeGen-Konfiguration nutzt die normale iOS-`resources`-Phase und automatisches Signing; dadurch entsteht ein korrekt signiertes `.app`-Bundle, das sich im Simulator installieren und starten laesst
- Die native SwiftUI-Oberflaeche orientiert sich visuell an der bestehenden Web-App: dunkle Panel-Flaechen, cyanfarbene Akzente, technische Header, kompaktere iPhone-Hierarchie und bewusst flaechigere Screen-Chrome mit reduziertem Blur an oberer und unterer Kante
- Die Archiv-Ansicht nutzt inzwischen eine eigene native Screen-Komposition statt Standard-`List`: Titel und Steuerbutton sitzen hoeher im Safe-Area-Kopfbereich, der Mittelteil ist als klare Panel-Zone aufgebaut und die untere Navigation liegt als kompakte eigene BenchFlow-Leiste dichter am Bildschirmrand
- Das Archiv-Muster wurde anschliessend als gemeinsames Seitenraster weitergezogen: Dashboard, Auftragsliste, Kundenliste sowie Detail-/Formularseiten nutzen jetzt dieselbe flaechige Kopfzeile oben, weniger Standard-iOS-Chrome und eine konsistent tief sitzende BenchFlow-Navigation unten
- Fuer die Flaechennutzung wurde die SwiftUI-Struktur anschliessend grundsaetzlich entkoppelt von Systemcontainern: die App nutzt keine sichtbare `TabView`-Chrome mehr, wichtige Screens wurden von `Form`/`List` auf `ScrollView`/`LazyVStack` umgestellt, und Kopf-/Fuss-Chrome wird als eigene BenchFlow-Oberflaeche gerendert statt ueber die Standard-iOS-Inset-Logik
- Ein sichtbarer schwarzer Rand in der nativen App war dabei kein beabsichtigtes Design, sondern ungenutzte Fensterflaeche: Hintergrund und Root-Container wurden deshalb auf echte Vollflaeche gezogen, und die Seiten-Chrome nutzt nun Inhalts-Insets statt die gesamte Seite als "Karte" nach innen zu padden
- Fuer aktuelle iPhone-Simulatoren und Geraete besitzt die SwiftUI-App jetzt auch einen echten Launch Screen; ohne diesen fiel iOS in einen Kompatibilitaetsmodus mit verkleinerter App-Flaeche und schwarzen Randbereichen zurueck
- Die native Auftragsliste wurde anschliessend entschlackt: statt drei paralleler Dropdowns fuer Status, Kategorie und Dokumenttyp nutzt sie jetzt einen gemeinsamen Quick-Filter plus Suche
- Die native Detailseite wurde anschliessend staerker als mobiler Arbeitsbereich organisiert: kompaktere Uebersicht, fruehere Schnellaktionen und konsistent gestylte Formularfelder statt roh verteilter Eingaben
- Die native Kundenliste folgt jetzt derselben reduzierten Filteridee wie die Auftragsliste: ein kompakter Umfangsfilter plus Suche statt einer sperrigen separaten Segmentflaeche
- Die native Auftragserfassung nutzt fuer bestehende Kunden jetzt ebenfalls einen ruhigeren Suchfluss: statt einer permanenten Rohliste erscheint erst eine echte Kundensuche mit Trefferanzeige und Uebernahme ins Formular
- KVA-, Rechnungs- und Attachment-Bloecke in der nativen Detailseite wurden anschliessend mobiler organisiert: zuerst Status-/Summenuebersicht, danach Eingabe und direkte PDF-/Mail-/Dokumentaktionen
- Ein freigegebener KVA kann in der nativen Detailseite jetzt direkt in eine Rechnung uebernommen werden; dabei werden Beschreibungen, Kosten und Datum in den Rechnungsflow uebertragen und sofort als Rechnung gespeichert
- Im nativen Detailscreen werden Arbeitszeit-, Material-, Fremdleistungs- und Versandkosten fuer KVA und Rechnung jetzt in Euro eingegeben; die API speichert intern weiter in Cent, damit Summen, Historieneintraege und PDF-Ausgaben konsistent bleiben
- Die Herstellerauswahl der Web-App wird jetzt auch in der nativen Neuauftrag- und Detailansicht ueber `/api/meta` gespiegelt, damit `Hersteller` wieder als Dropdown statt nur als Freitext zur Verfuegung steht
- Falls ein laufender Server das neue `manufacturer_options`-Feld in `/api/meta` noch nicht liefert, nutzt die SwiftUI-App automatisch dieselbe lokale Herstellerliste wie die Web-App als Fallback, damit die Auswahl nicht leer bleibt
- Der QR-Code im nativen `Druck / Tools`-Block wird nicht mehr als `AsyncImage` geladen, weil der Flask-Server SVG ausliefert; stattdessen oeffnet die App den QR direkt ueber den bestehenden Browser-Sheet-Flow
- Kundenbeleg, interner Beleg und weitere Browser-Sheet-Dokumente folgen in der nativen App jetzt auch dem gewaehlten App-Theme: Der iOS-WebView spiegelt `light`/`dark` in die Print-Seiten, statt auf ein getrenntes dunkles Web-Theme zurueckzufallen

### UI

- technischer Darkmode
- zuschaltbarer Lightmode mit Persistenz
- Lightmode-Flaechen fuer gemeinsame Karten-, Listen- und Formularbausteine zentral vereinheitlicht
- Listenansicht fuer Desktop statt Kartenansicht
- Toast-Benachrichtigungen statt statischer Flash-Boxen

## Routenueberblick

- `/dashboard`: Uebersicht
- `/orders`: aktive Auftraege
- `/orders/new`: neuer Auftrag
- `/orders/<id>`: Detailseite eines Auftrags
- `/archive`: archivierte Auftraege
- `/customers`: Kundenliste
- `/customers/<id>`: Kundendetailseite
- `/orders/<id>/print`: Kundenbeleg
- `/orders/<id>/print/internal`: interner Beleg

## Tests

Testlauf:
>>>>>>> react-work/main

```bash
python3 -m unittest discover -s tests -p "test_*.py"
```

Optionaler Syntax-Check:

```bash
python3 -m compileall app.py app tests
```

<<<<<<< HEAD
<details>
<summary>📋 Abgedeckte Test-Flows</summary>

- ✅ Auftrag anlegen und aktualisieren
- ✅ Kundenübernahme in der Erfassung
- ✅ Kundenliste und Kundenfilter
- ✅ Kundendetailseite
- ✅ Bild- und PDF-Anhänge
- ✅ Dokumenttypen und Dokumenthinweise
- ✅ KVA-Workflow
- ✅ Vorbereiteter KVA-Mailflow
- ✅ Rechnungsworkflow
- ✅ Archivieren und Wiederherstellen
- ✅ Kunden- und interner Beleg
- ✅ JSON-API: Dashboard, Auftragsdetail, Kundenliste, KVA/Rechnung, Attachment-Upload

</details>

---

## ⚠️ Bekannte Grenzen

- Mailversand ist bewusst ein vorbereiteter `mailto:`-Flow, kein SMTP-Versand
- KVA und Rechnung können bei Bedarf um weitere kaufmännische Pflichtangaben erweitert werden
- Die Test-Suite ist pragmatisch und nicht als vollständige Integrationsabdeckung gedacht

---

## 🤝 Contributing

Beiträge sind willkommen!

1. Fork das Repository
2. Branch erstellen (`git checkout -b feature/NeuesFeature`)
3. Commit (`git commit -m 'Add: Neues Feature'`)
4. Push (`git push origin feature/NeuesFeature`)
5. Pull Request öffnen

---

## 📄 License

MIT License – siehe [LICENSE](LICENSE) Datei

---

## 💡 Entstehung und Arbeitsweise

BenchFlow ist ein Eigenprojekt im Rahmen meiner Weiterbildung zum Fullstack Webentwickler.

Das Projekt wurde eigenständig konzipiert, strukturiert und entwickelt.
Bei der Umsetzung habe ich gezielt KI-gestützte Werkzeuge (u.a. als Pair-Programmer,
für Code-Reviews und zur Klärung technischer Fragen) eingesetzt – ähnlich wie
Entwickler heute Linter, Dokumentation oder Stack Overflow nutzen.

Alle Architekturentscheidungen, der Workflow-Entwurf und das Debugging
lagen durchgehend bei mir.

---

## 📬 Kontakt

**Matthias Osypka**

[![Email](https://img.shields.io/badge/Email-Matthias.Osypka%40icloud.com-blue?style=flat-square&logo=mail.ru)](mailto:Matthias.Osypka@icloud.com)
[![GitHub](https://img.shields.io/badge/GitHub-Follow-181717?style=flat-square&logo=github)](https://github.com/Matzorator)

💡 **Suche nach:** Entwickler Position im Bereich Fullstack Web Entwicklung

---

## 📊 Projekt-Statistik

```
Stack:              Python · Flask · SQLite · Swift · JavaScript
Test-Flows:         30+
API-Endpunkte:      12+
Dokumenttypen:      6
Unterstützte OS:    macOS (Web) · iOS 17+ (Native)
```

---

<div align="center">

**Entwickelt mit ❤️ und 🍵**

[⬆ Nach oben](#-benchflow---werkstatt--service-mvp)

</div>
=======
Die aktuelle Suite deckt unter anderem ab:
- Auftrag anlegen
- Auftrag aktualisieren
- Kundenuebernahme in der Erfassung
- Kundenliste und Kundenfilter
- Kundendetailseite
- Bild- und PDF-Anhaenge
- Dokumenttypen und Dokumenthinweise
- KVA-Workflow
- vorbereiteten KVA-Mailfluss
- Rechnungsworkflow
- Archivieren und Wiederherstellen
- Kunden- und internen Beleg
- JSON-API fuer Dashboard, Auftragsdetail, Kundenliste, KVA/Rechnung und Attachment-Upload

## Aktueller Stand

BenchFlow ist inzwischen deutlich ueber ein reines CRUD-MVP hinaus:
- Mehrseitenstruktur statt Sammeldashboard
- dokumentierte Werkstattablaeufe
- Kundenliste, Kunden-, KVA- und Rechnungslogik
- Druck- und PDF-Pfade fuer Kunden- und interne Nutzung
- parallele JSON-API fuer einen nativen SwiftUI-Client
- Demo-Daten fuer realistischeres Testen
- allgemein nachgeschaerfter Lightmode fuer wiederverwendete UI-Bausteine
- datenschutzsichere Demo-Datenbasis ohne echte Personen- oder Firmennamen

## Bekannte Grenzen

- Mailversand ist aktuell bewusst ein vorbereiteter `mailto:`-Flow, kein SMTP-Versand
- Rechnungen und KVA sind gestalterisch angenaehert, koennen aber bei Bedarf noch um weitere kaufmaennische Angaben erweitert werden
- die Test-Suite ist bewusst pragmatisch und nicht als vollstaendige Integrationsabdeckung gedacht

## Naechste sinnvolle Schritte

- optionale Versand- oder Zahlungsvermerke bei Rechnungen
- Dokumentenverwaltung weiter verfeinern, falls zusaetzliche Kategorien oder Freigabeprozesse noetig werden
- Kundenliste bei Bedarf weiter um Firmen-/Ortsfilter oder Schnellaktionen ausbauen
>>>>>>> react-work/main
