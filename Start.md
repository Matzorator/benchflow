## Agent Instruction for BenchFlow

You are helping to build **BenchFlow**, a web-based workshop and service management application.

### Project purpose
BenchFlow is both:
1. a usable software project
2. a portfolio project

It must demonstrate:
- practical HTML/CSS/JavaScript skills
- practical Python backend skills
- understanding of real business workflows
- structured collaboration with coding agents

### Core domain
BenchFlow is **not** a generic CRUD demo.
It is a workshop/service application for repair processes, especially inspired by music retail and technical service workflows.

Core concepts include:
- service orders
- customers
- devices
- repair status
- technician workflow
- documentation
- later optional exports / PDFs / integrations

### Current technical direction
Preferred stack:
- Frontend: HTML, CSS, JavaScript
- Backend: Python with Flask
- Database: SQLite initially

Do not switch frameworks or redesign the stack unless there is a clear and justified benefit.

### Important architectural principles
- Standalone first
- Integration ready
- Keep the MVP focused
- Prefer simple and maintainable solutions
- Respect the current project structure
- Avoid unnecessary complexity

### What to prioritize
Prioritize features that improve:
- usability
- clarity
- realistic workshop workflow
- maintainability
- portfolio value

### What to avoid
Avoid:
- unnecessary framework changes
- overengineering
- enterprise-grade complexity in early phases
- features that do not support the workshop/service workflow
- replacing everything at once without a strong reason

### Collaboration style
When suggesting changes:
- explain why the change helps
- keep changes small and understandable
- preserve naming consistency where possible
- separate “current MVP” from “future ideas”
- prefer incremental refactoring over full rewrites

### Good examples of tasks
- improve the current BenchFlow HTML/CSS/JS structure
- refactor JavaScript into smaller modules
- introduce customer and device entities
- replace delete with archive
- add status history
- prepare a Flask backend structure
- define SQLite models
- create realistic demo data for repair workflows

### Output expectation
Whenever possible:
- provide complete code
- keep it readable
- use clear naming
- include short explanations for important decisions
- stay aligned with the BenchFlow roadmap

## Roadmap-Checkliste

### Bereits umgesetzt
- [x] Frontend auf Basis von HTML, CSS und JavaScript angelegt
- [x] Flask-Backend als bevorzugte MVP-Basis eingerichtet
- [x] SQLite als lokale Datenbank eingebunden
- [x] Serviceauftraege als zentrale Werkstatt-Einheit umgesetzt
- [x] Kunden- und Geraetedaten getrennt modelliert
- [x] Realistische Demo-Daten fuer Reparaturworkflows angelegt
- [x] Suche und Filter fuer Auftragslisten integriert
- [x] Detailansicht und Bearbeitung fuer Auftraege eingebaut
- [x] Bestehende CRUD-Ideen aus `Werkstatt.html` und `script_benchflow.js` als Referenz einbezogen
- [x] Import aus der bisherigen JSON-CRUD-Struktur in das Flask-MVP integriert
- [x] JSON-Export als Grundlage fuer Datenaustausch und spaetere PDF-/Dokument-Workflows vorbereitet
- [x] Druckansicht fuer Serviceauftraege als PDF-/Beleg-Grundlage eingebaut
- [x] Formularvalidierung und sichtbares Feld-Feedback im Flask-UI verbessert
- [x] Optionale Bilddokumentation pro Geraet in Annahme, Detailansicht und Druckansicht integriert
- [x] Import um Dubletten-Erkennung und Vorschau erweitert
- [x] Ein-Seiten-Struktur in einen klaren Mehrseiten-Workflow aufgeteilt
- [x] Dashboard als reine Uebersichtsseite mit Schnellzugriffen ausgebaut
- [x] Aktive Auftragsliste als eigener Bereich fuer Suche, Filter und Oeffnen getrennt
- [x] Sortierung in Auftrags- und Archivlisten direkt ueber die Tabellenkoepfe mit ASC/DSC ergaenzt
- [x] Eigene Annahmeseite fuer neue Auftraege eingefuehrt
- [x] Detailseite als zentralen Arbeitsbereich fuer bestehende Auftraege geschaerft
- [x] Archiv als eigener Bereich vom aktiven Tagesgeschaeft getrennt
- [x] Gemeinsame Navigation und konsistente Seitenstruktur fuer Dashboard, Auftraege, Neuer Auftrag und Archiv eingefuehrt
- [x] Weiterleitung nach Auftragserfassung direkt auf die Detailseite umgestellt
- [x] Benennung, Navigation und README nach dem Umbau konsolidiert
- [x] Mehrere Fotos pro Auftrag statt nur eines einzelnen Geraetebilds unterstuetzt
- [x] JSON-Import und JSON-Export aus der Web-App entfernt, um den Werkstattfluss zu fokussieren
- [x] Flash-Meldungen als Toast-Benachrichtigungen umgesetzt
- [x] UI-Theme auf einen technischen Dark-Look mit `Rajdhani` und `Share Tech Mono` umgestellt
- [x] Umschaltbaren Light- und Dark-Mode mit persistentem Theme-Switch eingebaut
- [x] Auftrags- und Archivansicht auf Desktop von Karten auf eine Listenansicht umgestellt
- [x] Kundenbeleg als reduzierte Druckansicht ohne interne Werkstattinformationen geschärft
- [x] Separate interne Druckansicht mit Statushistorie, internen Notizen und Werkstattdetails ergänzt
- [x] Interner Beleg um Label-/Stickerbereich mit Bearbeitungsnummer, Kurzname, Gerätedaten und QR-Code erweitert
- [x] Interne Druckansicht für Regal-/Gerätesticker kompakter organisiert und stärker auf echten Labeldruck ausgerichtet
- [x] QR-Code fuer interne Druckansicht lokal/serverseitig statt ueber CDN erzeugt
- [x] Allgemeine Auftragsanhaenge fuer Bilder und PDF-Dokumente integriert, z. B. fuer externe Kostenvoranschlaege
- [x] PDF-Anhaenge werden ueber eigene Dateiroute ausgeliefert und lassen sich im Browser sauber oeffnen
- [x] PDF-Dokumente koennen beim Upload mit Typen wie Kostenvoranschlag, Rechnung oder Pruefprotokoll versehen werden
- [x] Bilder werden in den Anhaengen klar als Bilddokumentation gekennzeichnet
- [x] Bestehende PDF-Dokumente koennen in der Detailseite nachtraeglich umtypisiert werden
- [x] Theme-Switch farblich an hellen und dunklen Zielmodus angepasst
- [x] Auftrags- und Archivlisten um Filter nach Dokumenttyp erweitert
- [x] Dokumenthinweis in der Listenansicht sowie Datum/Dateigroesse in der Detailansicht ergänzt
- [x] Listenansicht zeigt bei PDF-Unterlagen neben der Anzahl auch den wichtigsten Dokumenttyp oder `gemischt`
- [x] Dashboard zeigt bei zuletzt bearbeiteten Auftraegen ebenfalls Dokumenthinweise an
- [x] PDF-Dokumente koennen einen kurzen Bezug zum Auftrag erhalten und spaeter in der Detailseite gepflegt werden
- [x] Dashboard-Karten und Listenblöcke mit mehr linkem Innenabstand an der Akzentlinie nachgeschärft
- [x] BenchFlow-Logo als lokales SVG-Asset angelegt und in Navigation sowie Kunden- und internen Belegen eingebunden
- [x] Dashboard wieder ohne Logo im Hero gehalten und das Logo-Asset auf eine sauberere Silber-/Blau-Version reduziert
- [x] Logo fuer kleine Darstellungsbreiten weiter vereinfacht, damit es im Header und in Belegen ruhiger und schaerfer wirkt
- [x] Originales PNG-Logo aus dem Projekt eingebunden und fuer Navigation, Kunden-/Interne Belege sowie KVA-PDF verwendet
- [x] Kundendetailansicht auf Desktop um breiteren Adressblock erweitert, damit lange Adressen ruhiger umbrechen
- [x] KVA-Header auf kleineres, nicht gestrecktes Original-Logo und ruhigere Titelgroesse abgestimmt
- [x] KVA-Header vertikal getrennt, damit Logo, Haupttitel und Untertitel nicht mehr kollidieren
- [x] Arbeitsumfang, Teile/Fremdleistungen und Kundenhinweis im KVA-PDF auf zwei Spalten verdichtet, um A4 besser auszunutzen
- [x] KVA-PDF insgesamt kompakter gesetzt, damit Kopf, Kostenblock und Freigabebox wieder eher auf eine Seite passen
- [x] Rechnungslogik mit eigener Rechnungsentitaet, Rechnungsnummer und PDF-Ablage am Auftrag ergänzt
- [x] Rechnungsblock auf der Detailseite eingebunden und Zahlungsstatus mit `Abholbereit` bzw. `Abgeschlossen` verknuepft
- [x] Kundenstammdaten um Firma, Adresse, Kontaktweg und interne Kundennotiz erweitert
- [x] Kundendetails in Auftragserfassung, Detailansicht und Belegansichten eingebunden
- [x] Auftragssuche auch nach Firmenname und Ort erweitert
- [x] Kundensuche in der Auftragserfassung integriert, damit bestehende Kunden uebernommen werden koennen
- [x] Kundenpicker in der Auftragserfassung fuer den Lightmode nachgeschaerft
- [x] Eigene Kundenliste mit Suche sowie Filter fuer aktive und alle Kunden umgesetzt
- [x] Eigene Kundendetailansicht mit Stammdaten und bisherigen Auftraegen umgesetzt
- [x] Demo-Datenbasis auf klar fiktive Namen, Firmen, Adressen, Maildomains und Techniklabels umgestellt
- [x] Bestehende Kundendatensaetze in der SQLite-Datenbank mit realistischen Firmen-, Adress- und Kontaktdetails angereichert
- [x] Kostenvoranschlag als eigener Workflow in der Detailseite mit separatem KVA-Block umgesetzt
- [x] Kostenvoranschlag wird serverseitig als PDF erzeugt und direkt als Dokument am Auftrag abgelegt
- [x] Vorbereiteter KVA-Mailversand aus der Detailseite mit vorausgefuelltem Empfaenger, Betreff und Mailtext ergaenzt
- [x] Freigegebener KVA kann direkt in eine Rechnung uebernommen und als PDF erzeugt werden
- [x] Beim direkten Rechnungsaufbau aus einem freigegebenen KVA wird vor dem Ueberschreiben einer bestehenden Rechnung sichtbar gewarnt und per Bestaetigung abgesichert
- [x] KVA-Mailvorlage fuer Kundenansprache mit klarerem Betreff, Geraetebezug und saubererem Mailtext nachgeschaerft
- [x] KVA-Mailvorlage zusaetzlich auf einen freundlicheren, lockereren Musikladen-Ton angepasst
- [x] Kundennahe Sprache in KVA-PDF, Rechnung und Kundenbeleg leicht auf den freundlich-lockeren Werkstattton abgestimmt
- [x] KVA- und Rechnungsbereich auf der Detailseite sprachlich etwas freundlicher und kundennaeher formuliert
- [x] Rechnungs-PDF gestalterisch an den KVA angeglichen, inklusive Markenblock, strukturierter A4-Boxen und Kundenlayout
- [x] README auf den aktuellen Mehrseiten-, Dokumenten-, KVA- und Rechnungsstand ausfuehrlicher aktualisiert
- [x] Kernpfade in Backend und Datenlogik gezielt mit Wartungskommentaren und Docstrings ergaenzt
- [x] Datenbank-Teardown beim App-Start korrigiert, damit Testlaeufe keine offenen SQLite-Initialverbindungen mehr hinterlassen
- [x] Bereits erzeugte KVA-PDFs sowie der PDF-Builder auf gueltigen Header korrigiert, damit Browser die Dateien sauber oeffnen
- [x] KVA-PDF auf ein strukturierteres DIN-A4-Brieflayout mit Kopf, Adressblock und Kostenuebersicht umgestellt
- [x] KVA-PDF-Farbwerte im Brieflayout nachgeschaerft, damit Inhalte trotz heller Boxen lesbar bleiben
- [x] KVA-PDF-Boxen fuer Kosten und Freigabestatus mit besseren Innenabstaenden und Zeilenpositionen ausbalanciert
- [x] Summenbereich im KVA-PDF mit mehr Abstand unter der Trennlinie nachgeschaerft
- [x] Markenblock im KVA-PDF-Header ergaenzt, damit der Kostenvoranschlag ebenfalls sichtbar gebrandet ist
- [x] Statuslogik fuer Kostenvoranschlaege um `Wartet auf Freigabe`, `Freigegeben` und `Abgelehnt` im Ablauf geschaerft
- [x] Kleine `unittest`-Suite fuer die Kernfluesse Auftrag anlegen, bearbeiten, Anhaenge, Archiv und Druckansichten angelegt
- [x] Bestehende SQLite-Datenbank um 50 zusätzliche fiktive Testaufträge ergänzt
- [x] Detailseite in klarere Werkstatt-Arbeitsblöcke fuer Ueberblick, Kundenkontakt, Annahme, Fehlerangabe, Werkstattbearbeitung, Medien und Verlauf gegliedert
- [x] Wiederverwendete Karten-, Listen- und Formularflaechen im Lightmode zentral nachgeschaerft, damit neue Bereiche nicht mehr dunkel stehen bleiben
- [x] JSON-API parallel zu den HTML-Routen fuer Dashboard, Auftragslisten, Detailansicht, Kundenliste, KVA-, Rechnungs- und Attachment-Workflow aufgebaut
- [x] SwiftUI-App-Struktur fuer iOS 17+ / macOS 14+ mit `APIClient`, `Codable`-Models, `@Observable`-ViewModels und ATS-Ausnahme fuer die lokale HTTP-IP angelegt
- [x] XcodeGen-Scaffold fuer den nativen SwiftUI-Client inklusive `Info.plist`, Asset-Katalog und iOS-17-App-Target vorbereitet
- [x] Xcode-Projekt so nachgeschaerft, dass Ressourcen ueber die normale iOS-`resources`-Phase gebaut und Simulator-Builds als korrekt signiertes `.app` installiert werden koennen
- [x] Native Optik naeher an die BenchFlow-Weboberflaeche gezogen: dunkle Werkstatt-Panels, cyanfarbene Akzente, kompaktere Tab-Navigation und dichtere Inhaltsdarstellung auf iPhone
- [x] Native Screen-Chrome weiter gestrafft: weniger Top-Abstand im Dashboard, Tab-Bar optisch naeher am unteren Rand und reduzierter Blur-/Fade-Bereich an Navigation und Tab-Leiste
- [x] Archiv-Screen nativer aufgeteilt: eigener Kopfbereich im oberen Safe Area, klar gegliederte Filter-/Listen-Panels statt Standard-`List` und eigene kompakte Tab-Leiste dichter am unteren Bildschirmrand
- [x] Das neue Archiv-Layout als gemeinsames Seitenmuster ausgerollt: Dashboard, Auftragsliste, Kundenliste sowie Detail- und Formularseiten nutzen jetzt dieselbe BenchFlow-Kopfzeile und die flachere Screen-Chrome
- [x] Die flaechige Native-Struktur grundsaetzlich nachgeschaerft: versteckte System-`TabView` als Layouttreiber entfernt, zentrale Screens von `Form`/`List` auf `ScrollView`/`LazyVStack` umgestellt und damit deutlich mehr nutzbare Bildschirmhoehe fuer Inhalt freigemacht
- [x] Schwarze Randflaechen in der nativen App als Fullscreen-/Containerproblem behoben: Root-Container und Screen-Hintergruende auf echte Vollflaeche gezogen statt nur inhaltsgross zu rendern, und die Seiten-Chrome auf Inhalts-Insets statt aeussere Gesamt-Paddings umgestellt
- [x] Nativen iOS-Client um einen echten Launch Screen ergaenzt, damit aktuelle iPhones und Simulatoren die App nicht mehr im verkleinerten Kompatibilitaetsmodus mit schwarzen Randflaechen starten
- [x] Native Auftragsliste als kompakteren Quick-Filter umgebaut: ein gemeinsamer Filter fuer Status, Kategorie oder Dokumenttyp statt drei paralleler Dropdowns
- [x] `Todo_Mobile.md` als eigene Mobile-Roadmap angelegt, damit die nativen iPhone-Verbesserungen getrennt vom Flask-Hauptprojekt planbar bleiben
- [x] Native Detailseite als ruhigeren mobilen Arbeitsbereich nachgeschaerft: kompaktere Uebersicht, fruehere Schnellaktionen und konsistent gestylte Eingabebloecke
- [x] Native Kundenliste auf dieselbe reduzierte Filterlogik wie die Auftragsliste umgestellt
- [x] Bestehende Kundenauswahl in der nativen Auftragserfassung auf Suchfeld plus Trefferliste umgebaut statt permanent unruhiger Kandidatenliste
- [x] KVA-, Rechnungs- und Attachment-Fluss in der nativen Detailseite mobiler organisiert: Status/Summen zuerst, Aktionen und Dokumentzugriffe direkter im Blick
- [x] Freigegebenen KVA in der nativen Detailseite per Button direkt in eine Rechnung uebernehmbar gemacht
- [x] KVA- und Rechnungskosten im nativen Detailscreen auf Euro-Eingabe umgestellt; API und Backend speichern intern weiter in Cent, damit Historie und Summen sauber bleiben
- [x] Herstellerliste aus der Web-App in die JSON-API uebernommen und in der nativen Neuauftrag-/Detailansicht wieder als Dropdown angebunden
- [x] Native App gegen aeltere Live-API abgesichert: Hersteller-Dropdown nutzt lokal dieselbe Fallback-Liste wie die Web-App, falls `/api/meta` das neue Feld noch nicht liefert
- [x] Haengenden Kreis im nativen `Druck / Tools`-Block behoben: QR wird serverseitig als SVG geliefert und deshalb in der App nicht mehr per `AsyncImage`, sondern direkt ueber den Browser-Sheet geoeffnet
- [x] Browser-Sheet der nativen App auf eigenen `WKWebView` umgestellt und Theme-Bruecke eingebaut, damit Kundenbeleg und interner Beleg auch im Lightmode hell bleiben

### Aktuell in Arbeit
- [ ] Derzeit kein struktureller Umbau in Arbeit

### Als naechstes sinnvoll
- [ ] Zahlungs- oder Versandvermerk fuer Rechnungen optional ergaenzen
- [ ] Kundenliste bei Bedarf um feinere Firmen-/Ortsfilter oder Schnellaktionen erweitern
- [ ] Dokumentenverwaltung bei Bedarf um weitere Kategorien oder kleine Metadaten wie Bemerkungen/Umbenennen erweitern
- [ ] Such- und Filteransicht spaeter optional um Migrationsmarker erweitern, falls der Altimport wieder relevant wird
- [ ] SwiftUI-App im laufenden Simulator noch fachlich gegen den Live-Server durchtesten (Navigation, Listen, Detail, KVA/Rechnung, PDF-/Print-Links)
