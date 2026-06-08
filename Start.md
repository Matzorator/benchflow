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
- [x] Eigene Kundendetailansicht mit Stammdaten und bisherigen Auftraegen umgesetzt
- [x] Bestehende Kundendatensaetze in der SQLite-Datenbank mit realistischen Firmen-, Adress- und Kontaktdetails angereichert
- [x] Kostenvoranschlag als eigener Workflow in der Detailseite mit separatem KVA-Block umgesetzt
- [x] Kostenvoranschlag wird serverseitig als PDF erzeugt und direkt als Dokument am Auftrag abgelegt
- [x] Vorbereiteter KVA-Mailversand aus der Detailseite mit vorausgefuelltem Empfaenger, Betreff und Mailtext ergaenzt
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
- [x] Auftragsdetailseite prozessnäher umsortiert, sodass KVA und Rechnung erst in einer klaren Abschlussphase unterhalb der Werkstattbearbeitung erscheinen
- [x] Detailseite visuell in Abschlussphasen fuer Dokumente/Verlauf und Abrechnung getrennt und die alte Zwei-Spalten-Logik im Arbeitsbereich zugunsten eines ruhigeren Einspalten-Layouts entfernt
- [x] Auftragskopf auf der Detailseite zu einem kompakteren Ueberblick mit fokussierten Kennzahlen und reduzierter Redundanz verdichtet
- [x] Kundenkontakt und Geraeteannahme auf der Detailseite zu einem gemeinsamen Annahme-Block zusammengefuehrt
- [x] Fehlerbild und Werkstattsteuerung auf der Detailseite zu einem gemeinsamen Arbeitsblock zusammengezogen und auf Desktop zweispaltig organisiert
- [x] Herstellerfeld in Auftragserfassung und Detailseite auf eine feste Markenauswahl umgestellt, um Tippfehler in Geraetemarken zu vermeiden
- [x] PDF-Dokumente auf der Detailseite um direkt pflegbaren Dateinamen und kurze interne Dokumentnotiz erweitert
- [x] Sichtbare deutsche UI-Texte in Navigation, Listen, Detailseite, Druckansichten und Meldungen auf echte Umlaute umgestellt
- [x] Deployment um `wsgi.py` und ein robustes Restart-Skript erweitert, damit Server-Updates den laufenden BenchFlow-Prozess reproduzierbar neu laden
- [x] Server-Umgebung und `benchflow.service` auf den korrekten `.venv`-Pfad repariert, damit Gunicorn wieder stabil ueber systemd startet

### Aktuell in Arbeit
- [ ] Derzeit kein struktureller Umbau in Arbeit

### Als naechstes sinnvoll
- [ ] Zahlungs- oder Versandvermerk fuer Rechnungen optional ergaenzen
- [ ] Kundenliste als eigener Bereich mit schneller Suche und direktem Zugriff auf laufende Vorgänge ergaenzen
- [ ] Dokumentenverwaltung bei Bedarf ueber die neuen Dateinamen/Kurznotizen hinaus um weitere Kategorien oder Freigabe-Metadaten erweitern
- [ ] Such- und Filteransicht spaeter optional um Migrationsmarker erweitern, falls der Altimport wieder relevant wird
