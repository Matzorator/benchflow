# BenchFlowNative in Xcode

Die SwiftUI-App liegt bewusst als quelloffene App-Struktur im Repo und ist auf die Live-API unter `http://192.168.178.31` ausgerichtet.

## Enthalten

- `Sources/`: SwiftUI-App, Models, `APIClient`, ViewModels und Views
- `Info.plist`: ATS-Ausnahme nur fuer `192.168.178.31`
- `project.yml`: XcodeGen-Spezifikation fuer ein iOS-17-App-Target

## Projekt erzeugen

Mit installiertem XcodeGen:

```bash
cd BenchFlowNative
xcodegen generate
open BenchFlowNative.xcodeproj
```

## In Xcode pruefen

1. Zielgeraet oder Simulator mit iOS 17+ waehlen
2. Build-Settings pruefen: `Info.plist` muss eingebunden sein
3. App starten und gegen die Live-API testen:
   - Dashboard
   - Auftragsliste
   - Kundensuche
   - Auftragsdetail
   - KVA/Rechnung
   - Print-/PDF-Links

## Hinweise

- Die App nutzt keine lokale Persistenz; Flask bleibt die einzige Datenquelle.
- Wenn der Simulator die lokale Netz-IP nicht erreicht, zuerst pruefen, ob sich Mac und Server im selben Netz befinden.
- Fuer einen spaeteren macOS-Target-Ausbau koennen dieselben `Sources/` weiterverwendet werden. Der aktuelle Scaffold ist iOS-first gehalten, damit der Einstieg in Xcode moeglichst direkt funktioniert.
