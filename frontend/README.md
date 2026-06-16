# BenchFlow React Frontend

Dieses Verzeichnis ist der erste React-Migrationsschritt fuer BenchFlow.

Der Flask-Teil bleibt zunaechst Backend und stellt die bestehende JSON-API unter `/api` bereit. Das React-Frontend laeuft separat ueber Vite und nutzt einen Dev-Proxy zu Flask.

## Lokal starten

Im Projektstamm:

```bash
. .venv/bin/activate
python app.py
```

In einem zweiten Terminal:

```bash
cd frontend
npm install
npm run dev
```

Vite zeigt danach die lokale React-URL an, normalerweise `http://localhost:5173`.

## Aktueller React-Umfang

- Dashboard ueber `/api/dashboard`
- Aktive Auftraege und Archiv ueber `/api/orders`
- Kundenliste und Kundendetail ueber `/api/customers`
- Auftragsdetail inklusive Drucklinks, Anhaenge, KVA, Rechnung und Statusverlauf
- Neuer Auftrag per `POST /api/orders`

Die alte Flask-Template-Oberflaeche bleibt vorerst parallel erhalten.
