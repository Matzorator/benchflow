import base64
import sqlite3
from pathlib import Path

from flask import current_app, g


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    ensure_schema(db)
    ensure_status_history(db)
    migrate_legacy_order_media(db)
    seed_demo_data(db)
    ensure_status_history(db)
    migrate_legacy_order_media(db)
    db.commit()


def ensure_schema(db):
    """Apply the current schema and bridge older local SQLite versions forward.

    BenchFlow is intentionally SQLite-first and keeps migrations lightweight.
    Instead of a dedicated migration framework, we patch missing columns and
    run targeted legacy upgrades so older local databases remain usable.
    """
    schema_path = Path(__file__).with_name("schema.sql")

    if table_exists(db, "service_orders") and not has_column(db, "service_orders", "customer_id"):
        migrate_legacy_service_orders(db)

    db.executescript(schema_path.read_text(encoding="utf-8"))

    if table_exists(db, "service_orders") and not has_column(db, "service_orders", "archived_at"):
        db.execute("ALTER TABLE service_orders ADD COLUMN archived_at TEXT")
    if table_exists(db, "customers") and not has_column(db, "customers", "company_name"):
        db.execute("ALTER TABLE customers ADD COLUMN company_name TEXT NOT NULL DEFAULT ''")
    if table_exists(db, "customers") and not has_column(db, "customers", "street"):
        db.execute("ALTER TABLE customers ADD COLUMN street TEXT NOT NULL DEFAULT ''")
    if table_exists(db, "customers") and not has_column(db, "customers", "postal_code"):
        db.execute("ALTER TABLE customers ADD COLUMN postal_code TEXT NOT NULL DEFAULT ''")
    if table_exists(db, "customers") and not has_column(db, "customers", "city"):
        db.execute("ALTER TABLE customers ADD COLUMN city TEXT NOT NULL DEFAULT ''")
    if table_exists(db, "customers") and not has_column(db, "customers", "preferred_contact"):
        db.execute("ALTER TABLE customers ADD COLUMN preferred_contact TEXT NOT NULL DEFAULT ''")
    if table_exists(db, "customers") and not has_column(db, "customers", "customer_notes"):
        db.execute("ALTER TABLE customers ADD COLUMN customer_notes TEXT NOT NULL DEFAULT ''")
    if table_exists(db, "service_order_media") and not has_column(db, "service_order_media", "document_type"):
        db.execute("ALTER TABLE service_order_media ADD COLUMN document_type TEXT NOT NULL DEFAULT ''")
    if table_exists(db, "service_order_media") and not has_column(db, "service_order_media", "order_context"):
        db.execute("ALTER TABLE service_order_media ADD COLUMN order_context TEXT NOT NULL DEFAULT ''")


def migrate_legacy_order_media(db):
    """Move historic single-image device data into the normalized media table.

    Older BenchFlow versions stored one image directly on the device record.
    Newer versions support multiple attachments per service order, so we seed
    the first matching media row once and keep existing migrated rows intact.
    """
    if not table_exists(db, "service_order_media"):
        return

    legacy_rows = db.execute(
        """
        SELECT so.id AS service_order_id, d.image_data
        FROM service_orders so
        JOIN devices d ON d.id = so.device_id
        WHERE COALESCE(d.image_data, '') <> ''
        """
    ).fetchall()

    for row in legacy_rows:
        existing = db.execute(
            """
            SELECT id
            FROM service_order_media
            WHERE service_order_id = ?
            LIMIT 1
            """,
            (row["service_order_id"],),
        ).fetchone()
        if existing:
            continue

        mime_type = "image/jpeg"
        image_data = row["image_data"]
        if image_data.startswith("data:image/png"):
            mime_type = "image/png"
        elif image_data.startswith("data:image/webp"):
            mime_type = "image/webp"

        db.execute(
            """
            INSERT INTO service_order_media (service_order_id, filename, mime_type, media_data)
            VALUES (?, ?, ?, ?)
            """,
            (
                row["service_order_id"],
                "legacy-device-image",
                mime_type,
                image_data,
            ),
        )


def migrate_legacy_service_orders(db):
    if table_exists(db, "service_orders_legacy_backup"):
        current_rows = db.execute(
            """
            SELECT
                id,
                order_number,
                customer_name,
                device_name,
                issue_description,
                status,
                technician,
                intake_date,
                internal_notes,
                created_at
            FROM service_orders
            ORDER BY id ASC
            """
        ).fetchall()
        backup_rows = db.execute(
            """
            SELECT
                id,
                order_number,
                customer_name,
                device_name,
                issue_description,
                status,
                technician,
                intake_date,
                internal_notes,
                created_at
            FROM service_orders_legacy_backup
            ORDER BY id ASC
            """
        ).fetchall()
        legacy_rows = backup_rows if len(backup_rows) >= len(current_rows) else current_rows
        db.execute("DROP TABLE service_orders")
    else:
        db.execute("ALTER TABLE service_orders RENAME TO service_orders_legacy_backup")
        legacy_rows = db.execute(
            """
            SELECT
                id,
                order_number,
                customer_name,
                device_name,
                issue_description,
                status,
                technician,
                intake_date,
                internal_notes,
                created_at
            FROM service_orders_legacy_backup
            ORDER BY id ASC
            """
        ).fetchall()

    schema_path = Path(__file__).with_name("schema.sql")
    db.executescript(schema_path.read_text(encoding="utf-8"))

    for row in legacy_rows:
        customer_id = find_or_create_customer(
            db,
            row["customer_name"],
            "",
            "",
        )
        device_id = create_device(
            db,
            category="sonstiges",
            manufacturer="",
            model=row["device_name"],
            serial_number="",
            accessories="",
            condition_notes="",
            image_data="",
        )

        db.execute(
            """
            INSERT INTO service_orders (
                order_number,
                customer_id,
                device_id,
                issue_description,
                status,
                technician,
                intake_date,
                warranty_status,
                quote_required,
                diagnostic_source,
                internal_notes,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (
                row["order_number"],
                customer_id,
                device_id,
                row["issue_description"],
                normalize_status(row["status"]),
                row["technician"],
                row["intake_date"],
                "unbekannt",
                "nein",
                "Werkbank",
                row["internal_notes"] or "",
                row["created_at"] or "CURRENT_TIMESTAMP",
            ),
        )


def seed_demo_data(db):
    existing = db.execute("SELECT COUNT(*) AS count FROM service_orders").fetchone()
    if existing["count"] > 0:
        return
    populate_demo_data(db)


def populate_demo_data(db):
    for order in build_demo_orders():
        existing_order = find_matching_demo_order(db, order)
        if existing_order:
            continue
        insert_demo_order(db, assign_demo_order_number(db, order))


def build_demo_orders():
    demo_orders = [
        {
            "order_number": "SO-1001",
            "customer_name": "Lena Hoffmann",
            "company_name": "",
            "customer_email": "lena.hoffmann@example.de",
            "customer_phone": "+49 151 20000001",
            "street": "Auenweg 14",
            "postal_code": "50674",
            "city": "Koeln",
            "preferred_contact": "email",
            "customer_notes": "Bitte Termine bevorzugt per Mail bestaetigen.",
            "category": "gitarre",
            "manufacturer": "Fender",
            "model": "Player Stratocaster",
            "serial_number": "FEN-PLR-8821",
            "accessories": "Gigbag, Tremolohebel",
            "condition_notes": "Leichte Gebrauchsspuren am Pickguard.",
            "issue_description": "Elektrik brummt, Schalter kratzt.",
            "status": "Diagnose",
            "technician": "Jonas",
            "intake_date": "2026-03-25",
            "warranty_status": "nein",
            "quote_required": "ja",
            "diagnostic_source": "Werkbank",
            "internal_notes": "Signalweg pruefen, Potis reinigen, Abschirmung checken.",
            "quote": {
                "quote_number": "KVA-1001",
                "title": "Kostenvoranschlag SO-1001",
                "work_description": "Fehleranalyse, Reinigung der Elektrik, Nacharbeit am Schalter und Abschirmung testen.",
                "parts_description": "Kontaktreiniger, Abschirmmaterial, Kleinmaterial.",
                "labor_cost_cents": 8900,
                "parts_cost_cents": 2400,
                "external_cost_cents": 0,
                "shipping_cost_cents": 0,
                "total_cost_cents": 11300,
                "valid_until": "2026-04-12",
                "customer_message": "Bitte kurze Rueckmeldung, ob wir die Reparatur auf Basis dieses Kostenvoranschlags freigeben sollen.",
                "approval_status": "offen",
                "pdf_filename": "so-1001-kostenvoranschlag.pdf",
                "pdf_context": "KVA fuer Elektrik- und Abschirmungsarbeit",
            },
        },
        {
            "order_number": "SO-1002",
            "customer_name": "Martin Keller",
            "company_name": "Keller Keys Studio",
            "customer_email": "martin.keller@example.de",
            "customer_phone": "+49 151 20000002",
            "street": "Tonhallenstrasse 8",
            "postal_code": "40211",
            "city": "Duesseldorf",
            "preferred_contact": "telefon",
            "customer_notes": "Vor Ort haeufig schlecht erreichbar, besser spaet nachmittags anrufen.",
            "category": "keyboard",
            "manufacturer": "Yamaha",
            "model": "CP88",
            "serial_number": "YAM-CP88-1202",
            "accessories": "Netzkabel",
            "condition_notes": "Gehause sauber, eine Taste reagiert haengend.",
            "issue_description": "Taste C4 haengt sporadisch.",
            "status": "Warten auf Teile",
            "technician": "Aylin",
            "intake_date": "2026-03-24",
            "warranty_status": "unbekannt",
            "quote_required": "ja",
            "diagnostic_source": "Werkbank",
            "internal_notes": "Keybed geoeffnet, Feder gebrochen, Ersatzteil angefragt.",
            "quote": {
                "quote_number": "KVA-1002",
                "title": "Kostenvoranschlag SO-1002",
                "work_description": "Demontage des Keybeds, Austausch der betroffenen Mechanik und Funktionstest.",
                "parts_description": "Ersatzfeder und Tastenmechanik laut Hersteller.",
                "labor_cost_cents": 11900,
                "parts_cost_cents": 3600,
                "external_cost_cents": 0,
                "shipping_cost_cents": 790,
                "total_cost_cents": 16290,
                "valid_until": "2026-04-15",
                "customer_message": "Wir warten aktuell auf die Rueckmeldung zum Ersatzteil. Sobald das fuer Sie passt, bestellen wir direkt.",
                "approval_status": "offen",
                "pdf_filename": "so-1002-kostenvoranschlag.pdf",
                "pdf_context": "KVA fuer Keybed-Reparatur",
            },
        },
        {
            "order_number": "SO-1003",
            "customer_name": "Sofia Brandt",
            "company_name": "",
            "customer_email": "sofia.brandt@example.de",
            "customer_phone": "+49 151 20000003",
            "street": "Hafenstrasse 27",
            "postal_code": "28195",
            "city": "Bremen",
            "preferred_contact": "telefon",
            "customer_notes": "",
            "category": "amp",
            "manufacturer": "Marshall",
            "model": "DSL40CR",
            "serial_number": "MAR-DSL40-4403",
            "accessories": "Schutzhulle",
            "condition_notes": "Tolex an der Kante leicht eingerissen.",
            "issue_description": "Kein Output nach Transport.",
            "status": "In Reparatur",
            "technician": "Jonas",
            "intake_date": "2026-03-27",
            "warranty_status": "nein",
            "quote_required": "nein",
            "diagnostic_source": "Messgeraet",
            "internal_notes": "Rohrensockel nachloeten, Lautsprecherbuchse testen.",
        },
    ]
    demo_orders.extend(build_generated_demo_orders())
    return demo_orders


def insert_demo_order(db, order):
    customer_id = find_or_create_customer(
        db,
        order["customer_name"],
        order["customer_email"],
        order["customer_phone"],
        order.get("company_name", ""),
        order.get("street", ""),
        order.get("postal_code", ""),
        order.get("city", ""),
        order.get("preferred_contact", ""),
        order.get("customer_notes", ""),
    )
    device_id = create_device(
        db,
        category=order["category"],
        manufacturer=order["manufacturer"],
        model=order["model"],
        serial_number=order["serial_number"],
        accessories=order["accessories"],
        condition_notes=order["condition_notes"],
        image_data="",
    )
    cursor = db.execute(
        """
        INSERT INTO service_orders (
            order_number,
            customer_id,
            device_id,
            issue_description,
            status,
            technician,
            intake_date,
            warranty_status,
            quote_required,
            diagnostic_source,
            internal_notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            order["order_number"],
            customer_id,
            device_id,
            order["issue_description"],
            order["status"],
            order["technician"],
            order["intake_date"],
            order["warranty_status"],
            order["quote_required"],
            order["diagnostic_source"],
            order["internal_notes"],
        ),
    )
    order_id = cursor.lastrowid

    if order.get("status_history"):
        db.execute("DELETE FROM service_order_status_history WHERE service_order_id = ?", (order_id,))
        for history_entry in order["status_history"]:
            add_status_history_entry(
                db,
                order_id,
                history_entry["status"],
                note=history_entry.get("note", ""),
                changed_at=history_entry.get("changed_at"),
            )

    if order.get("quote"):
        quote_media_id = insert_demo_pdf_media(
            db,
            service_order_id=order_id,
            filename=order["quote"]["pdf_filename"],
            document_type="kva",
            order_context=order["quote"]["pdf_context"],
        )
        db.execute(
            """
            INSERT INTO service_order_quotes (
                service_order_id,
                quote_number,
                title,
                work_description,
                parts_description,
                labor_cost_cents,
                parts_cost_cents,
                external_cost_cents,
                shipping_cost_cents,
                total_cost_cents,
                valid_until,
                customer_message,
                approval_status,
                pdf_media_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                order_id,
                order["quote"]["quote_number"],
                order["quote"]["title"],
                order["quote"]["work_description"],
                order["quote"]["parts_description"],
                order["quote"]["labor_cost_cents"],
                order["quote"]["parts_cost_cents"],
                order["quote"]["external_cost_cents"],
                order["quote"]["shipping_cost_cents"],
                order["quote"]["total_cost_cents"],
                order["quote"]["valid_until"],
                order["quote"]["customer_message"],
                order["quote"]["approval_status"],
                quote_media_id,
            ),
        )

    if order.get("invoice"):
        invoice_media_id = insert_demo_pdf_media(
            db,
            service_order_id=order_id,
            filename=order["invoice"]["pdf_filename"],
            document_type="rechnung",
            order_context=order["invoice"]["pdf_context"],
        )
        db.execute(
            """
            INSERT INTO service_order_invoices (
                service_order_id,
                invoice_number,
                title,
                labor_description,
                parts_description,
                labor_cost_cents,
                parts_cost_cents,
                external_cost_cents,
                shipping_cost_cents,
                total_cost_cents,
                invoice_date,
                payment_status,
                internal_note,
                pdf_media_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                order_id,
                order["invoice"]["invoice_number"],
                order["invoice"]["title"],
                order["invoice"]["labor_description"],
                order["invoice"]["parts_description"],
                order["invoice"]["labor_cost_cents"],
                order["invoice"]["parts_cost_cents"],
                order["invoice"]["external_cost_cents"],
                order["invoice"]["shipping_cost_cents"],
                order["invoice"]["total_cost_cents"],
                order["invoice"]["invoice_date"],
                order["invoice"]["payment_status"],
                order["invoice"]["internal_note"],
                invoice_media_id,
            ),
        )


def find_matching_demo_order(db, order):
    return db.execute(
        """
        SELECT so.id
        FROM service_orders so
        JOIN customers c ON c.id = so.customer_id
        JOIN devices d ON d.id = so.device_id
        WHERE c.email = ?
          AND d.serial_number = ?
          AND so.issue_description = ?
        LIMIT 1
        """,
        (
            order["customer_email"],
            order["serial_number"],
            order["issue_description"],
        ),
    ).fetchone()


def assign_demo_order_number(db, order):
    existing_number = db.execute(
        "SELECT 1 FROM service_orders WHERE order_number = ? LIMIT 1",
        (order["order_number"],),
    ).fetchone()
    if not existing_number:
        return order

    old_number = order["order_number"]
    next_number = build_next_order_number(db)
    updated_order = dict(order)
    updated_order["order_number"] = next_number
    if updated_order.get("quote"):
        updated_order["quote"] = remap_quote_numbers(updated_order["quote"], old_number, next_number)
    if updated_order.get("invoice"):
        updated_order["invoice"] = remap_invoice_numbers(updated_order["invoice"], old_number, next_number)
    return updated_order


def build_next_order_number(db):
    rows = db.execute("SELECT order_number FROM service_orders").fetchall()
    max_number = 1000
    for row in rows:
        order_number = row["order_number"]
        if not order_number or not order_number.startswith("SO-"):
            continue
        suffix = order_number[3:]
        if suffix.isdigit():
            max_number = max(max_number, int(suffix))
    return f"SO-{max_number + 1}"


def remap_quote_numbers(quote, old_order_number, new_order_number):
    updated_quote = dict(quote)
    old_suffix = old_order_number.split("-", 1)[1]
    new_suffix = new_order_number.split("-", 1)[1]
    updated_quote["quote_number"] = f"KVA-{new_suffix}"
    updated_quote["title"] = quote["title"].replace(old_order_number, new_order_number)
    updated_quote["pdf_filename"] = quote["pdf_filename"].replace(old_order_number.lower(), new_order_number.lower())
    updated_quote["pdf_context"] = quote["pdf_context"].replace(old_suffix, new_suffix)
    return updated_quote


def remap_invoice_numbers(invoice, old_order_number, new_order_number):
    updated_invoice = dict(invoice)
    old_suffix = old_order_number.split("-", 1)[1]
    new_suffix = new_order_number.split("-", 1)[1]
    updated_invoice["invoice_number"] = f"RE-{new_suffix}"
    updated_invoice["title"] = invoice["title"].replace(old_order_number, new_order_number)
    updated_invoice["pdf_filename"] = invoice["pdf_filename"].replace(old_order_number.lower(), new_order_number.lower())
    updated_invoice["pdf_context"] = invoice["pdf_context"].replace(old_suffix, new_suffix)
    return updated_invoice


def build_generated_demo_orders():
    generated = []
    sample_orders = [
        {
            "order_number": "SO-1004",
            "customer_name": "Nora Weiss",
            "company_name": "Weiss Audio Rental",
            "customer_email": "nora.weiss@example.de",
            "customer_phone": "+49 151 20000004",
            "street": "Industriestrasse 19",
            "postal_code": "44135",
            "city": "Dortmund",
            "preferred_contact": "email",
            "customer_notes": "Bei Freigaben bitte immer kurze Mail plus Anruf.",
            "category": "mischpult",
            "manufacturer": "Allen & Heath",
            "model": "QU-16",
            "serial_number": "AH-QU16-1940",
            "accessories": "Flightcase, Netzleitung",
            "condition_notes": "Oberseite mit Tourspuren, Fader intakt.",
            "issue_description": "Ein Kanal verzerrt bei hohem Gain.",
            "status": "Wartet auf Freigabe",
            "technician": "Mira",
            "intake_date": "2026-03-22",
            "warranty_status": "nein",
            "quote_required": "ja",
            "diagnostic_source": "Messgeraet",
            "internal_notes": "Signalpfad auf Kanal 9 auffaellig, Vorstufe weiter pruefen.",
            "status_history": [
                {"status": "Angenommen", "note": "Auftrag an der Theke erfasst.", "changed_at": "2026-03-22 09:10:00"},
                {"status": "Diagnose", "note": "Pult geoeffnet und Fehler auf Kanal 9 eingegrenzt.", "changed_at": "2026-03-22 13:45:00"},
                {"status": "Wartet auf Freigabe", "note": "KVA fuer Kanalzug-Reparatur vorbereitet.", "changed_at": "2026-03-23 11:15:00"},
            ],
            "quote": {
                "quote_number": "KVA-1004",
                "title": "Kostenvoranschlag SO-1004",
                "work_description": "Fehlerdiagnose, Tausch der betroffenen Kanalzug-Komponenten und abschliessender Dauertest.",
                "parts_description": "ICs, Kondensatoren und Kleinmaterial fuer Kanal 9.",
                "labor_cost_cents": 14900,
                "parts_cost_cents": 5200,
                "external_cost_cents": 0,
                "shipping_cost_cents": 790,
                "total_cost_cents": 20890,
                "valid_until": "2026-04-10",
                "customer_message": "Bitte kurze Freigabe per Mail, dann legen wir direkt los.",
                "approval_status": "offen",
                "pdf_filename": "so-1004-kostenvoranschlag.pdf",
                "pdf_context": "KVA fuer Kanalzug-Reparatur",
            },
        },
        {
            "order_number": "SO-1005",
            "customer_name": "Tom Berger",
            "company_name": "",
            "customer_email": "tom.berger@example.de",
            "customer_phone": "+49 151 20000005",
            "street": "Waldweg 4",
            "postal_code": "80331",
            "city": "Muenchen",
            "preferred_contact": "telefon",
            "customer_notes": "",
            "category": "mikrofon",
            "manufacturer": "Shure",
            "model": "SM7B",
            "serial_number": "SHU-SM7B-3221",
            "accessories": "Schutztasche",
            "condition_notes": "Sauber, Korb ohne Dellen.",
            "issue_description": "Signal ist deutlich leiser als gewohnt.",
            "status": "Abholbereit",
            "technician": "Jonas",
            "intake_date": "2026-03-18",
            "warranty_status": "nein",
            "quote_required": "nein",
            "diagnostic_source": "Werkbank",
            "internal_notes": "Interner XLR-Kontakt nachgeloetet, Pegel wieder stabil.",
            "status_history": [
                {"status": "Angenommen", "note": "Mikrofon mit Pegelproblem aufgenommen.", "changed_at": "2026-03-18 10:00:00"},
                {"status": "In Reparatur", "note": "Kontaktproblem am Ausgang gefunden und nachgeloetet.", "changed_at": "2026-03-18 14:20:00"},
                {"status": "Abholbereit", "note": "Rechnung erstellt und Kunde informiert.", "changed_at": "2026-03-19 09:05:00"},
            ],
            "invoice": {
                "invoice_number": "RE-1005",
                "title": "Rechnung SO-1005",
                "labor_description": "Diagnose des XLR-Ausgangs und Nacharbeit an der Lötstelle.",
                "parts_description": "Kein Materialverbrauch ausser Kleinmaterial.",
                "labor_cost_cents": 4900,
                "parts_cost_cents": 0,
                "external_cost_cents": 0,
                "shipping_cost_cents": 0,
                "total_cost_cents": 4900,
                "invoice_date": "2026-03-19",
                "payment_status": "offen",
                "internal_note": "Zahlung bei Abholung vorgesehen.",
                "pdf_filename": "so-1005-rechnung.pdf",
                "pdf_context": "Rechnung fuer Kontaktreparatur am Mikrofon",
            },
        },
        {
            "order_number": "SO-1006",
            "customer_name": "Clara Neumann",
            "company_name": "Neumann Session Works",
            "customer_email": "clara.neumann@example.de",
            "customer_phone": "+49 151 20000006",
            "street": "Kranhausufer 3",
            "postal_code": "50678",
            "city": "Koeln",
            "preferred_contact": "email",
            "customer_notes": "Abholung meist durch Assistenten.",
            "category": "synthesizer",
            "manufacturer": "Korg",
            "model": "Minilogue XD",
            "serial_number": "KOR-MXD-8130",
            "accessories": "Netzteil, Softcase",
            "condition_notes": "Leichte Kratzer auf Holzseitenteil rechts.",
            "issue_description": "Display flackert und Encoder springt.",
            "status": "Abgeschlossen",
            "technician": "Aylin",
            "intake_date": "2026-03-14",
            "warranty_status": "nein",
            "quote_required": "ja",
            "diagnostic_source": "Werkbank",
            "internal_notes": "Displaystecker neu gesetzt, Encoder ersetzt, Endtest ohne Fehler.",
            "status_history": [
                {"status": "Angenommen", "note": "Synth mit Display- und Encoderproblemen angenommen.", "changed_at": "2026-03-14 11:15:00"},
                {"status": "Wartet auf Freigabe", "note": "KVA fuer Austausch des Encoders erstellt.", "changed_at": "2026-03-15 09:40:00"},
                {"status": "Freigegeben", "note": "Kunde hat Reparatur per Mail freigegeben.", "changed_at": "2026-03-15 14:05:00"},
                {"status": "Abgeschlossen", "note": "Reparatur abgeschlossen und Rechnung bezahlt.", "changed_at": "2026-03-18 16:30:00"},
            ],
            "quote": {
                "quote_number": "KVA-1006",
                "title": "Kostenvoranschlag SO-1006",
                "work_description": "Austausch des Encoders, Kontrolle des Display-Anschlusses und kompletter Funktionstest.",
                "parts_description": "Original-Encoder laut Hersteller und Kleinmaterial.",
                "labor_cost_cents": 7900,
                "parts_cost_cents": 1800,
                "external_cost_cents": 0,
                "shipping_cost_cents": 0,
                "total_cost_cents": 9700,
                "valid_until": "2026-04-05",
                "customer_message": "Display und Encoder lassen sich wirtschaftlich instand setzen.",
                "approval_status": "freigegeben",
                "pdf_filename": "so-1006-kostenvoranschlag.pdf",
                "pdf_context": "KVA fuer Display- und Encoder-Reparatur",
            },
            "invoice": {
                "invoice_number": "RE-1006",
                "title": "Rechnung SO-1006",
                "labor_description": "Austausch des Encoders, Display-Nacharbeit und Endtest.",
                "parts_description": "Original-Encoder und Kleinmaterial.",
                "labor_cost_cents": 7900,
                "parts_cost_cents": 1800,
                "external_cost_cents": 0,
                "shipping_cost_cents": 0,
                "total_cost_cents": 9700,
                "invoice_date": "2026-03-18",
                "payment_status": "bezahlt",
                "internal_note": "Per EC bei Abholung bezahlt.",
                "pdf_filename": "so-1006-rechnung.pdf",
                "pdf_context": "Rechnung fuer abgeschlossene Synth-Reparatur",
            },
        },
    ]

    generated.extend(sample_orders)

    cities = [
        ("Koeln", "50667"),
        ("Duesseldorf", "40213"),
        ("Bremen", "28195"),
        ("Muenster", "48143"),
        ("Leipzig", "04109"),
        ("Hamburg", "20095"),
        ("Berlin", "10115"),
        ("Essen", "45127"),
    ]
    manufacturers = [
        ("Fender", "gitarre", "Player Telecaster"),
        ("Gibson", "gitarre", "Les Paul Studio"),
        ("Yamaha", "keyboard", "MODX8"),
        ("Roland", "synthesizer", "Juno-DS88"),
        ("Shure", "mikrofon", "SM58"),
        ("Marshall", "amp", "JCM800"),
        ("Mesa", "amp", "Boogie Express"),
        ("Allen & Heath", "mischpult", "SQ-5"),
        ("Pioneer DJ", "dj_controller", "DDJ-1000"),
        ("QSC", "lautsprecher", "K12.2"),
    ]
    technicians = ["Jonas", "Aylin", "Mira"]
    statuses = [
        "Angenommen",
        "Diagnose",
        "Wartet auf Freigabe",
        "Warten auf Teile",
        "In Reparatur",
        "Fertig",
        "Abholbereit",
    ]

    for index in range(7, 37):
        manufacturer, category, model = manufacturers[(index - 7) % len(manufacturers)]
        city, postal_code = cities[(index - 7) % len(cities)]
        technician = technicians[(index - 7) % len(technicians)]
        status = statuses[(index - 7) % len(statuses)]
        quote_required = "ja" if status in {"Wartet auf Freigabe", "Warten auf Teile"} else "nein"
        generated.append(
            {
                "order_number": f"SO-{1000 + index}",
                "customer_name": f"Demo Kunde {index:02d}",
                "company_name": "Stage Service" if index % 4 == 0 else "",
                "customer_email": f"demo{index:02d}@example.de",
                "customer_phone": f"+49 151 20000{index:03d}",
                "street": f"Werkstattweg {index}",
                "postal_code": postal_code,
                "city": city,
                "preferred_contact": "telefon" if index % 2 == 0 else "email",
                "customer_notes": "Demo-Datensatz fuer Listen, Suche und Historie.",
                "category": category,
                "manufacturer": manufacturer,
                "model": model,
                "serial_number": f"SN-{index:04d}-{manufacturer[:3].upper()}",
                "accessories": "Netzteil, Tasche" if category in {"keyboard", "synthesizer", "dj_controller"} else "Case",
                "condition_notes": "Normale Gebrauchsspuren, Demoauftrag.",
                "issue_description": f"Demo-Fehlerbild {index:02d}: Aussetzer unter Last und sporadische Kontaktprobleme.",
                "status": status,
                "technician": technician,
                "intake_date": f"2026-03-{(index % 26) + 1:02d}",
                "warranty_status": "nein" if index % 3 else "unbekannt",
                "quote_required": quote_required,
                "diagnostic_source": "Werkbank" if index % 2 else "Messgeraet",
                "internal_notes": "Automatisch erzeugter Demodatensatz fuer realistischere Projektpraesentation.",
            }
        )

    return generated


def insert_demo_pdf_media(db, service_order_id, filename, document_type, order_context):
    cursor = db.execute(
        """
        INSERT INTO service_order_media (service_order_id, filename, mime_type, document_type, order_context, media_data)
        VALUES (?, ?, 'application/pdf', ?, ?, ?)
        """,
        (
            service_order_id,
            filename,
            document_type,
            order_context,
            encode_demo_pdf_data(filename, order_context),
        ),
    )
    return cursor.lastrowid


def encode_demo_pdf_data(filename, order_context):
    pdf_bytes = (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Count 1 /Kids [3 0 R] >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 200] /Contents 4 0 R >>\nendobj\n"
        b"4 0 obj\n<< /Length 56 >>\nstream\n"
        + f"BT /F1 12 Tf 24 160 Td ({filename[:40]}) Tj ET\n".encode("latin-1", "ignore")
        + f"BT /F1 10 Tf 24 140 Td ({order_context[:50]}) Tj ET\n".encode("latin-1", "ignore")
        + b"endstream\nendobj\nxref\n0 5\n0000000000 65535 f \n"
        b"0000000010 00000 n \n0000000060 00000 n \n0000000117 00000 n \n0000000204 00000 n \n"
        b"trailer\n<< /Root 1 0 R /Size 5 >>\nstartxref\n320\n%%EOF"
    )
    encoded = base64.b64encode(pdf_bytes).decode("ascii")
    return f"data:application/pdf;base64,{encoded}"


def ensure_status_history(db):
    if not table_exists(db, "service_order_status_history"):
        return

    orders_without_history = db.execute(
        """
        SELECT so.id, so.status, so.created_at
        FROM service_orders so
        LEFT JOIN service_order_status_history sh ON sh.service_order_id = so.id
        WHERE sh.id IS NULL
        """
    ).fetchall()

    for order in orders_without_history:
        add_status_history_entry(
            db,
            order["id"],
            order["status"],
            note="Initialer Status aus bestehendem Auftrag uebernommen.",
            changed_at=order["created_at"],
        )


def find_or_create_customer(
    db,
    name,
    email,
    phone,
    company_name="",
    street="",
    postal_code="",
    city="",
    preferred_contact="",
    customer_notes="",
):
    """Reuse an identical customer record instead of creating duplicates.

    For the MVP we keep customer matching intentionally conservative:
    name, mail, phone and company must match. This avoids accidental merges
    between similar contacts while still preventing obvious duplicates during
    rapid intake work.
    """
    existing = db.execute(
        """
        SELECT id
        FROM customers
        WHERE name = ? AND email = ? AND phone = ? AND company_name = ?
        LIMIT 1
        """,
        (name, email, phone, company_name),
    ).fetchone()

    if existing:
        return existing["id"]

    cursor = db.execute(
        """
        INSERT INTO customers (name, company_name, email, phone, street, postal_code, city, preferred_contact, customer_notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (name, company_name, email, phone, street, postal_code, city, preferred_contact, customer_notes),
    )
    return cursor.lastrowid


def create_device(db, category, manufacturer, model, serial_number, accessories, condition_notes, image_data):
    cursor = db.execute(
        """
        INSERT INTO devices (
            category,
            manufacturer,
            model,
            serial_number,
            accessories,
            condition_notes,
            image_data
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            category,
            manufacturer,
            model,
            serial_number,
            accessories,
            condition_notes,
            image_data,
        ),
    )
    return cursor.lastrowid


def add_status_history_entry(db, order_id, status, note="", changed_at=None):
    db.execute(
        """
        INSERT INTO service_order_status_history (
            service_order_id,
            status,
            note,
            changed_at
        )
        VALUES (?, ?, ?, COALESCE(?, CURRENT_TIMESTAMP))
        """,
        (order_id, status, note, changed_at),
    )


def table_exists(db, table_name):
    row = db.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def has_column(db, table_name, column_name):
    columns = db.execute(f"PRAGMA table_info({table_name})").fetchall()
    return any(column["name"] == column_name for column in columns)


def normalize_status(status):
    mapping = {
        "angenommen": "Angenommen",
        "in_pruefung": "Diagnose",
        "wartet_freigabe": "Wartet auf Freigabe",
        "wartet_teile": "Warten auf Teile",
        "in_reparatur": "In Reparatur",
        "fertig": "Fertig",
        "abholbereit": "Abholbereit",
        "abgeschlossen": "Abgeschlossen",
    }
    return mapping.get(status, status or "Diagnose")


def init_app(app):
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    with app.app_context():
        init_db()
