import base64
from io import BytesIO
from datetime import date, timedelta
import textwrap
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote
import zlib

from flask import Blueprint, abort, flash, redirect, render_template, request, send_file, url_for
from PIL import Image
import qrcode
from qrcode.image.svg import SvgPathImage

from .db import (
    add_status_history_entry,
    create_device,
    find_or_create_customer,
    get_db,
)

bp = Blueprint("benchflow", __name__)

TECHNICIANS = ["Jonas", "Aylin", "Mira", "Werkstatt extern"]
ORDER_STATUSES = [
    "Angenommen",
    "Diagnose",
    "Wartet auf Freigabe",
    "Freigegeben",
    "Abgelehnt",
    "Warten auf Teile",
    "In Reparatur",
    "Fertig",
    "Abholbereit",
    "Abgeschlossen",
    "Archiviert",
]
CATEGORIES = [
    ("gitarre", "Gitarre"),
    ("bass", "Bass"),
    ("keyboard", "Keyboard"),
    ("synthesizer", "Synthesizer"),
    ("mischpult", "Mischpult"),
    ("dj_controller", "DJ-Controller"),
    ("amp", "Amp"),
    ("lautsprecher", "Lautsprecher"),
    ("mikrofon", "Mikrofon"),
    ("sonstiges", "Sonstiges"),
]
WARRANTY_OPTIONS = [("ja", "Ja"), ("nein", "Nein"), ("unbekannt", "Unbekannt")]
QUOTE_OPTIONS = [("ja", "Ja"), ("nein", "Nein")]
DIAGNOSTIC_SOURCES = ["Werkbank", "Messgerät", "EC-Lesetool", "Externes Labor"]
PREFERRED_CONTACT_OPTIONS = [("telefon", "Telefon"), ("email", "E-Mail"), ("egal", "Egal")]
MANUFACTURER_OPTIONS = [
    "AKG",
    "Allen & Heath",
    "Ampeg",
    "Arturia",
    "Audio-Technica",
    "Beyerdynamic",
    "Behringer",
    "Boss",
    "Casio",
    "Cort",
    "D'Addario",
    "Duesenberg",
    "Electro-Voice",
    "Epiphone",
    "ESP",
    "EVH",
    "Fender",
    "Focusrite",
    "Fractal Audio",
    "G&L",
    "Gallien-Krueger",
    "Gibson",
    "Gretsch",
    "Headrush",
    "HK Audio",
    "Hughes & Kettner",
    "Ibanez",
    "Jackson",
    "JBL",
    "Kawai",
    "Kemper",
    "Korg",
    "KRK",
    "Kurzweil",
    "Laney",
    "Line 6",
    "Mackie",
    "Marshall",
    "Martin",
    "Mesa",
    "Music Man",
    "Native Instruments",
    "Neumann",
    "Nord",
    "Novation",
    "Orange",
    "PRS",
    "Pioneer DJ",
    "PreSonus",
    "QSC",
    "RCF",
    "RME",
    "Rode",
    "Roland",
    "Sadowsky",
    "Sennheiser",
    "Shure",
    "Sigma",
    "Soundcraft",
    "Squier",
    "Steinberg",
    "Sterling",
    "Tama",
    "Tascam",
    "Taylor",
    "TC Electronic",
    "Teenage Engineering",
    "Yamaha",
    "Zoom",
]
QUOTE_APPROVAL_OPTIONS = [
    ("offen", "Offen / wartet auf Freigabe"),
    ("freigegeben", "Freigegeben"),
    ("abgelehnt", "Abgelehnt"),
]
INVOICE_PAYMENT_OPTIONS = [
    ("offen", "Offen"),
    ("bezahlt", "Bezahlt"),
]
DOCUMENT_TYPES = [
    ("", "Allgemeines Dokument"),
    ("kva", "Kostenvoranschlag"),
    ("rechnung", "Rechnung"),
    ("pruefprotokoll", "Prüfprotokoll"),
    ("hersteller", "Herstellerunterlage"),
    ("lieferschein", "Lieferschein"),
    ("servicebericht", "Servicebericht"),
    ("garantie", "Garantiebeleg"),
]


@bp.route("/")
def dashboard():
    return redirect(url_for("benchflow.dashboard_page"))


@bp.route("/dashboard")
def dashboard_page():
    db = get_db()
    active_orders = fetch_orders(where_clause="WHERE so.archived_at IS NULL")
    ready_statuses = {"Fertig", "Abholbereit"}
    blocked_statuses = {"Wartet auf Freigabe", "Warten auf Teile"}
    status_summary = db.execute(
        """
        SELECT status, COUNT(*) AS total
        FROM service_orders
        WHERE archived_at IS NULL
        GROUP BY status
        ORDER BY total DESC, status ASC
        """
    ).fetchall()
    ready_count = sum(item["total"] for item in status_summary if item["status"] in ready_statuses)
    blocked_count = sum(item["total"] for item in status_summary if item["status"] in blocked_statuses)
    archived_count = db.execute(
        """
        SELECT COUNT(*) AS total
        FROM service_orders
        WHERE archived_at IS NOT NULL
        """
    ).fetchone()["total"]
    recent_orders = db.execute(
        """
        SELECT
            so.id,
            so.order_number,
            so.customer_id,
            c.name AS customer_name,
            d.manufacturer,
            d.model,
            so.status,
            so.updated_at,
            (
                SELECT COUNT(*)
                FROM service_order_media som
                WHERE som.service_order_id = so.id
                  AND som.mime_type = 'application/pdf'
            ) AS document_count,
            (
                SELECT COUNT(DISTINCT COALESCE(NULLIF(som.document_type, ''), 'allgemein'))
                FROM service_order_media som
                WHERE som.service_order_id = so.id
                  AND som.mime_type = 'application/pdf'
            ) AS document_type_count,
            (
                SELECT COALESCE(NULLIF(som.document_type, ''), 'allgemein')
                FROM service_order_media som
                WHERE som.service_order_id = so.id
                  AND som.mime_type = 'application/pdf'
                ORDER BY datetime(som.created_at) ASC, som.id ASC
                LIMIT 1
            ) AS primary_document_type
        FROM service_orders so
        JOIN customers c ON c.id = so.customer_id
        JOIN devices d ON d.id = so.device_id
        WHERE so.archived_at IS NULL
        ORDER BY datetime(so.updated_at) DESC, so.id DESC
        LIMIT 5
        """
    ).fetchall()
    recent_orders = [dict(row) for row in recent_orders]
    for order in recent_orders:
        order["document_hint"] = build_order_document_hint(order)
    return render_template(
        "dashboard.html",
        status_summary=status_summary,
        active_order_count=len(active_orders),
        ready_count=ready_count,
        blocked_count=blocked_count,
        archived_count=archived_count,
        recent_orders=recent_orders,
    )


@bp.route("/datenschutz")
def privacy_page():
    return render_template("legal/privacy.html")


@bp.route("/impressum")
def legal_notice_page():
    return render_template("legal/imprint.html")


@bp.route("/orders")
def orders():
    filters = {
        "q": request.args.get("q", "").strip(),
        "status": request.args.get("status", "").strip(),
        "category": request.args.get("category", "").strip(),
        "document_type": request.args.get("document_type", "").strip(),
    }
    return render_order_list(filters=filters, archived=False)


@bp.route("/archive")
def archive():
    filters = {
        "q": request.args.get("q", "").strip(),
        "status": request.args.get("status", "").strip(),
        "category": request.args.get("category", "").strip(),
        "document_type": request.args.get("document_type", "").strip(),
    }
    return render_order_list(filters=filters, archived=True)


@bp.route("/orders/new")
def new_order():
    return render_order_form()


@bp.route("/orders", methods=["POST"])
def create_order():
    form_data = extract_order_form()
    media_items, media_error = process_uploaded_order_media()
    if media_items:
        first_image = next((item for item in media_items if item["is_image"]), None)
        form_data["image_data"] = first_image["media_data"] if first_image else ""
        form_data["media_items"] = media_items

    errors, field_errors = validate_order_form(form_data)
    if media_error:
        field_errors["order_files"] = media_error
        errors.append(media_error)

    if errors:
        return render_order_form(
            form_data=form_data,
            errors=errors,
            field_errors=field_errors,
        ), 400

    db = get_db()
    customer_id = find_or_create_customer(
        db,
        form_data["customer_name"],
        form_data["customer_email"],
        form_data["customer_phone"],
        form_data["company_name"],
        form_data["street"],
        form_data["postal_code"],
        form_data["city"],
        form_data["preferred_contact"],
        form_data["customer_notes"],
    )
    device_id = create_device(
        db,
        category=form_data["category"],
        manufacturer=form_data["manufacturer"],
        model=form_data["model"],
        serial_number=form_data["serial_number"],
        accessories=form_data["accessories"],
        condition_notes=form_data["condition_notes"],
        image_data=form_data["image_data"],
    )
    order_number = next_order_number(db)
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
            order_number,
            customer_id,
            device_id,
            form_data["issue_description"],
            "Angenommen",
            form_data["technician"],
            form_data["intake_date"],
            form_data["warranty_status"],
            form_data["quote_required"],
            form_data["diagnostic_source"],
            form_data["internal_notes"],
        ),
    )
    order_id = cursor.lastrowid
    add_status_history_entry(
        db,
        order_id,
        "Angenommen",
        note="Auftrag neu angelegt.",
    )
    if media_items:
        add_order_media_entries(db, order_id, media_items)
    db.commit()
    flash(f"Auftrag {order_number} erfolgreich angelegt.", "success")
    return redirect(url_for("benchflow.order_detail", order_id=order_id))


@bp.route("/orders/<int:order_id>")
def order_detail(order_id):
    order = fetch_order(order_id)
    return render_order_detail_page(order)


@bp.route("/customers/<int:customer_id>")
def customer_detail(customer_id):
    customer = fetch_customer(customer_id)
    customer_orders = fetch_orders(
        where_clause="WHERE so.customer_id = ?",
        params=[customer_id],
    )
    return render_template(
        "customers/detail.html",
        customer=customer,
        orders=customer_orders,
        order_count=len(customer_orders),
    )


@bp.route("/orders/<int:order_id>/attachments/<int:media_id>")
def order_attachment(order_id, media_id):
    media_item = fetch_order_media_item(order_id, media_id)
    payload = decode_media_data(media_item["media_data"])
    filename = media_item["filename"] or "anhang"
    response = send_file(
        BytesIO(payload),
        mimetype=media_item["mime_type"],
        download_name=filename,
        as_attachment=False,
    )
    response.headers["Content-Disposition"] = f'inline; filename="{filename}"'
    return response


@bp.route("/orders/<int:order_id>/print")
def order_print(order_id):
    order = fetch_order(order_id)
    status_history = fetch_status_history(order_id)
    order_media = fetch_order_media(order_id, fallback_image=order["image_data"])
    media_groups = split_media_items(order_media)
    return render_template(
        "order_print.html",
        order=order,
        order_media=media_groups["images"],
        status_history=status_history,
    )


@bp.route("/orders/<int:order_id>/print/internal")
def order_print_internal(order_id):
    order = fetch_order(order_id)
    status_history = fetch_status_history(order_id)
    order_media = fetch_order_media(order_id, fallback_image=order["image_data"])
    media_groups = split_media_items(order_media)
    qr_payload = build_internal_qr_payload(order)
    return render_template(
        "order_print_internal.html",
        order=order,
        order_media=media_groups["images"],
        status_history=status_history,
        label_customer_short=build_customer_short_label(order["customer_name"]),
        label_device_text=build_device_label_text(order),
        qr_payload=qr_payload,
        qr_image_data=build_internal_qr_svg_data(qr_payload),
    )


@bp.route("/orders/<int:order_id>/quote", methods=["POST"])
def save_order_quote(order_id):
    """Persist the quote form, regenerate its PDF and sync the order status.

    Quotes are not treated as detached exports. They are first-class workflow
    objects linked to the order, stored as normalized data and mirrored as a
    PDF attachment so the workshop always has one current document version.
    """
    order = fetch_order(order_id)
    existing_quote = fetch_order_quote(order_id, required=False)
    quote_form_data = extract_quote_form(existing_quote=existing_quote, order=order)
    quote_errors = validate_quote_form(quote_form_data)

    if quote_errors:
        flash("Kostenvoranschlag konnte nicht gespeichert werden.", "error")
        return render_order_detail_page(
            order,
            quote_errors=quote_errors,
            quote_form_data=quote_form_data,
            quote=merge_quote_for_render(existing_quote, quote_form_data),
        ), 400

    db = get_db()
    quote_number = existing_quote["quote_number"] if existing_quote else build_quote_number(order)
    total_cost_cents = compute_quote_total_cents(quote_form_data)
    approval_status = quote_form_data["approval_status"]
    pdf_filename = f"{order['order_number'].lower()}-kostenvoranschlag.pdf"
    pdf_context = quote_form_data["title"] or "Kostenvoranschlag"
    pdf_bytes = build_quote_pdf(order, quote_form_data, quote_number, total_cost_cents)
    pdf_media_data = encode_pdf_bytes(pdf_bytes)

    if existing_quote:
        db.execute(
            """
            UPDATE service_order_quotes
            SET title = ?,
                work_description = ?,
                parts_description = ?,
                labor_cost_cents = ?,
                parts_cost_cents = ?,
                external_cost_cents = ?,
                shipping_cost_cents = ?,
                total_cost_cents = ?,
                valid_until = ?,
                customer_message = ?,
                approval_status = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE service_order_id = ?
            """,
            (
                quote_form_data["title"],
                quote_form_data["work_description"],
                quote_form_data["parts_description"],
                quote_form_data["labor_cost_cents"],
                quote_form_data["parts_cost_cents"],
                quote_form_data["external_cost_cents"],
                quote_form_data["shipping_cost_cents"],
                total_cost_cents,
                quote_form_data["valid_until"],
                quote_form_data["customer_message"],
                approval_status,
                order_id,
            ),
        )
        quote_id = existing_quote["id"]
        pdf_media_id = existing_quote.get("pdf_media_id")
    else:
        cursor = db.execute(
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
                approval_status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                order_id,
                quote_number,
                quote_form_data["title"],
                quote_form_data["work_description"],
                quote_form_data["parts_description"],
                quote_form_data["labor_cost_cents"],
                quote_form_data["parts_cost_cents"],
                quote_form_data["external_cost_cents"],
                quote_form_data["shipping_cost_cents"],
                total_cost_cents,
                quote_form_data["valid_until"],
                quote_form_data["customer_message"],
                approval_status,
            ),
        )
        quote_id = cursor.lastrowid
        pdf_media_id = None

    if pdf_media_id:
        db.execute(
            """
            UPDATE service_order_media
            SET filename = ?,
                mime_type = 'application/pdf',
                document_type = 'kva',
                order_context = ?,
                media_data = ?,
                created_at = CURRENT_TIMESTAMP
            WHERE id = ?
              AND service_order_id = ?
            """,
            (pdf_filename, pdf_context[:220], pdf_media_data, pdf_media_id, order_id),
        )
    else:
        media_cursor = db.execute(
            """
            INSERT INTO service_order_media (service_order_id, filename, mime_type, document_type, order_context, media_data)
            VALUES (?, ?, 'application/pdf', 'kva', ?, ?)
            """,
            (order_id, pdf_filename, pdf_context[:220], pdf_media_data),
        )
        pdf_media_id = media_cursor.lastrowid
        db.execute(
            "UPDATE service_order_quotes SET pdf_media_id = ? WHERE id = ?",
            (pdf_media_id, quote_id),
        )

    new_status = build_order_status_from_quote_approval(approval_status)
    history_note = build_quote_history_note(existing_quote, approval_status, total_cost_cents)
    db.execute(
        """
        UPDATE service_orders
        SET quote_required = 'ja',
            status = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (new_status, order_id),
    )
    if order["status"] != new_status or not existing_quote:
        add_status_history_entry(db, order_id, new_status, note=history_note)

    db.commit()
    flash("Kostenvoranschlag gespeichert und als PDF am Auftrag abgelegt.", "success")
    return redirect(url_for("benchflow.order_detail", order_id=order_id, _anchor="kva-workflow"))


@bp.route("/orders/<int:order_id>/invoice", methods=["POST"])
def save_order_invoice(order_id):
    """Persist the invoice form, regenerate its PDF and advance order state.

    Invoice payment state directly influences the workshop status so the team
    can see whether a device is only ready for pickup or already completed.
    """
    order = fetch_order(order_id)
    existing_invoice = fetch_order_invoice(order_id, required=False)
    invoice_form_data = extract_invoice_form(existing_invoice=existing_invoice, order=order)
    invoice_errors = validate_invoice_form(invoice_form_data)

    if invoice_errors:
        flash("Rechnung konnte nicht gespeichert werden.", "error")
        return render_order_detail_page(
            order,
            invoice_errors=invoice_errors,
            invoice_form_data=invoice_form_data,
            invoice=merge_invoice_for_render(existing_invoice, invoice_form_data),
        ), 400

    db = get_db()
    invoice_number = existing_invoice["invoice_number"] if existing_invoice else build_invoice_number(order)
    total_cost_cents = compute_invoice_total_cents(invoice_form_data)
    pdf_filename = f"{order['order_number'].lower()}-rechnung.pdf"
    pdf_context = invoice_form_data["title"] or "Rechnung"
    pdf_bytes = build_invoice_pdf(order, invoice_form_data, invoice_number, total_cost_cents)
    pdf_media_data = encode_pdf_bytes(pdf_bytes)

    if existing_invoice:
        db.execute(
            """
            UPDATE service_order_invoices
            SET title = ?,
                labor_description = ?,
                parts_description = ?,
                labor_cost_cents = ?,
                parts_cost_cents = ?,
                external_cost_cents = ?,
                shipping_cost_cents = ?,
                total_cost_cents = ?,
                invoice_date = ?,
                payment_status = ?,
                internal_note = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE service_order_id = ?
            """,
            (
                invoice_form_data["title"],
                invoice_form_data["labor_description"],
                invoice_form_data["parts_description"],
                invoice_form_data["labor_cost_cents"],
                invoice_form_data["parts_cost_cents"],
                invoice_form_data["external_cost_cents"],
                invoice_form_data["shipping_cost_cents"],
                total_cost_cents,
                invoice_form_data["invoice_date"],
                invoice_form_data["payment_status"],
                invoice_form_data["internal_note"],
                order_id,
            ),
        )
        invoice_id = existing_invoice["id"]
        pdf_media_id = existing_invoice.get("pdf_media_id")
    else:
        cursor = db.execute(
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
                internal_note
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                order_id,
                invoice_number,
                invoice_form_data["title"],
                invoice_form_data["labor_description"],
                invoice_form_data["parts_description"],
                invoice_form_data["labor_cost_cents"],
                invoice_form_data["parts_cost_cents"],
                invoice_form_data["external_cost_cents"],
                invoice_form_data["shipping_cost_cents"],
                total_cost_cents,
                invoice_form_data["invoice_date"],
                invoice_form_data["payment_status"],
                invoice_form_data["internal_note"],
            ),
        )
        invoice_id = cursor.lastrowid
        pdf_media_id = None

    if pdf_media_id:
        db.execute(
            """
            UPDATE service_order_media
            SET filename = ?,
                mime_type = 'application/pdf',
                document_type = 'rechnung',
                order_context = ?,
                media_data = ?,
                created_at = CURRENT_TIMESTAMP
            WHERE id = ?
              AND service_order_id = ?
            """,
            (pdf_filename, pdf_context[:220], pdf_media_data, pdf_media_id, order_id),
        )
    else:
        media_cursor = db.execute(
            """
            INSERT INTO service_order_media (service_order_id, filename, mime_type, document_type, order_context, media_data)
            VALUES (?, ?, 'application/pdf', 'rechnung', ?, ?)
            """,
            (order_id, pdf_filename, pdf_context[:220], pdf_media_data),
        )
        pdf_media_id = media_cursor.lastrowid
        db.execute(
            "UPDATE service_order_invoices SET pdf_media_id = ? WHERE id = ?",
            (pdf_media_id, invoice_id),
        )

    invoice_status = "Abgeschlossen" if invoice_form_data["payment_status"] == "bezahlt" else "Abholbereit"
    history_note = build_invoice_history_note(existing_invoice, invoice_form_data["payment_status"], total_cost_cents)
    db.execute(
        """
        UPDATE service_orders
        SET status = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (invoice_status, order_id),
    )
    if order["status"] != invoice_status or not existing_invoice:
        add_status_history_entry(db, order_id, invoice_status, note=history_note)

    db.commit()
    flash("Rechnung gespeichert und als PDF am Auftrag abgelegt.", "success")
    return redirect(url_for("benchflow.order_detail", order_id=order_id, _anchor="invoice-workflow"))


@bp.route("/orders/<int:order_id>/quote/email")
def prepare_quote_email(order_id):
    """Prepare a local mail client draft for the current quote PDF.

    This stays deliberately lightweight for the MVP: no SMTP, no background
    jobs, just a reliable prefilled `mailto:` flow plus a history note that
    documents the communication step inside the order timeline.
    """
    order = fetch_order(order_id)
    quote_data = fetch_order_quote(order_id, required=False)
    if quote_data is None or not quote_data.get("pdf_media_id"):
        flash("Es ist noch kein Kostenvoranschlag als PDF vorhanden.", "error")
        return redirect(url_for("benchflow.order_detail", order_id=order_id, _anchor="kva-workflow"))
    if not order.get("customer_email"):
        flash("Beim Kunden ist keine E-Mail-Adresse hinterlegt.", "error")
        return redirect(url_for("benchflow.order_detail", order_id=order_id, _anchor="kva-workflow"))

    db = get_db()
    add_status_history_entry(
        db,
        order_id,
        order["status"],
        note=f"KVA-Mail an {order['customer_email']} vorbereitet.",
    )
    db.commit()

    device_label = " ".join(part for part in [order.get("manufacturer", ""), order.get("model", "")] if part).strip() or "Gerät"
    subject = f"Ihr Kostenvoranschlag {quote_data['quote_number']} zu Auftrag {order['order_number']}"
    body_lines = [
        f"Hallo {order['customer_name']},",
        "",
        "danke für Ihren Auftrag bei uns.",
        "",
        "anbei finden Sie den Kostenvoranschlag zu Ihrem Serviceauftrag.",
        f"Bearbeitungsnummer: {order['order_number']}",
        f"KVA-Nummer: {quote_data['quote_number']}",
        f"Gerät: {device_label}",
        f"Gesamtbetrag: {quote_data['total_cost_label']}",
    ]
    if quote_data.get("valid_until"):
        body_lines.append(f"Gültig bis: {quote_data['valid_until']}")
    if quote_data.get("customer_message"):
        body_lines.extend(
            [
                "",
                "Hinweis:",
                *wrap_pdf_lines(quote_data["customer_message"], width=72),
            ]
        )
    body_lines.extend(
        [
            "",
            "Wenn der Kostenvoranschlag für Sie passt, geben Sie uns einfach kurz Bescheid.",
            "Eine kurze Antwort per E-Mail oder ein kurzer Anruf reicht voellig aus.",
            "",
            "Viele Grüße aus der Werkstatt",
            "Ihr BenchFlow Service Team",
        ]
    )
    mailto_url = f"mailto:{quote(order['customer_email'])}?subject={quote(subject)}&body={quote(chr(10).join(body_lines))}"
    return redirect(mailto_url)


@bp.route("/orders/<int:order_id>/update", methods=["POST"])
def update_order(order_id):
    existing_order = fetch_order(order_id)
    existing_status = existing_order["status"]
    form_data = extract_order_form(include_status=True)
    media_items, media_error = process_uploaded_order_media()
    existing_media = fetch_order_media(order_id, fallback_image=existing_order["image_data"])
    existing_images = split_media_items(existing_media)["images"]
    form_data["image_data"] = existing_images[0]["media_data"] if existing_images else ""
    form_data["media_items"] = existing_media

    errors, field_errors = validate_order_form(form_data, require_status=True)
    if media_error:
        field_errors["order_files"] = media_error
        errors.append(media_error)

    if errors:
        merged = {**dict(existing_order), **form_data}
        merged["customer_street"] = form_data["street"]
        merged["customer_postal_code"] = form_data["postal_code"]
        merged["customer_city"] = form_data["city"]
        merged["customer_preferred_contact"] = form_data["preferred_contact"]
        merged["customer_preferred_contact_label"] = build_preferred_contact_label(form_data["preferred_contact"])
        return render_order_detail_page(
            merged,
            errors=errors,
            field_errors=field_errors,
            order_media=existing_media,
        ), 400

    db = get_db()
    remove_media_ids = [value for value in request.form.getlist("remove_media_ids") if value.isdigit()]
    document_updates = extract_document_updates(request.form)
    db.execute(
        """
        UPDATE customers
        SET name = ?,
            email = ?,
            phone = ?,
            company_name = ?,
            street = ?,
            postal_code = ?,
            city = ?,
            preferred_contact = ?,
            customer_notes = ?
        WHERE id = ?
        """,
        (
            form_data["customer_name"],
            form_data["customer_email"],
            form_data["customer_phone"],
            form_data["company_name"],
            form_data["street"],
            form_data["postal_code"],
            form_data["city"],
            form_data["preferred_contact"],
            form_data["customer_notes"],
            existing_order["customer_id"],
        ),
    )
    db.execute(
        """
        UPDATE devices
        SET category = ?,
            manufacturer = ?,
            model = ?,
            serial_number = ?,
            accessories = ?,
            condition_notes = ?,
            image_data = ?
        WHERE id = ?
        """,
        (
            form_data["category"],
            form_data["manufacturer"],
            form_data["model"],
            form_data["serial_number"],
            form_data["accessories"],
            form_data["condition_notes"],
            existing_order["image_data"],
            existing_order["device_id"],
        ),
    )
    db.execute(
        """
        UPDATE service_orders
        SET issue_description = ?,
            status = ?,
            technician = ?,
            intake_date = ?,
            warranty_status = ?,
            quote_required = ?,
            diagnostic_source = ?,
            internal_notes = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            form_data["issue_description"],
            form_data["status"],
            form_data["technician"],
            form_data["intake_date"],
            form_data["warranty_status"],
            form_data["quote_required"],
            form_data["diagnostic_source"],
            form_data["internal_notes"],
            order_id,
        ),
    )
    if form_data["status"] != existing_status:
        add_status_history_entry(
            db,
            order_id,
            form_data["status"],
            note=f"Statuswechsel von {existing_status} zu {form_data['status']}.",
        )
    if remove_media_ids:
        db.execute(
            f"DELETE FROM service_order_media WHERE service_order_id = ? AND id IN ({','.join(['?'] * len(remove_media_ids))})",
            [order_id, *remove_media_ids],
        )
    existing_media_by_id = {int(item["id"]): item for item in existing_media if str(item["id"]).isdigit()}
    for media_id, payload in document_updates.items():
        existing_item = existing_media_by_id.get(media_id, {})
        db.execute(
            """
            UPDATE service_order_media
            SET filename = ?,
                document_type = ?,
                order_context = ?
            WHERE service_order_id = ?
              AND id = ?
              AND mime_type = 'application/pdf'
            """,
            (
                normalize_media_filename(payload["filename"], existing_item.get("filename", "")),
                payload["document_type"],
                payload["order_context"],
                order_id,
                media_id,
            ),
        )
    if media_items:
        add_order_media_entries(db, order_id, media_items)
    sync_order_primary_image(db, order_id, existing_order["device_id"])
    db.commit()
    flash("Auftrag erfolgreich aktualisiert.", "success")

    return redirect(url_for("benchflow.order_detail", order_id=order_id))


@bp.route("/orders/<int:order_id>/archive", methods=["POST"])
def archive_order(order_id):
    order = fetch_order(order_id)
    db = get_db()
    db.execute(
        """
        UPDATE service_orders
        SET archived_at = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (order_id,),
    )
    add_status_history_entry(
        db,
        order_id,
        order["status"],
        note="Auftrag archiviert.",
    )
    db.commit()
    return redirect(back_to_order_or_dashboard(order_id))


@bp.route("/orders/<int:order_id>/restore", methods=["POST"])
def restore_order(order_id):
    order = fetch_order(order_id)
    db = get_db()
    db.execute(
        """
        UPDATE service_orders
        SET archived_at = NULL,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (order_id,),
    )
    add_status_history_entry(
        db,
        order_id,
        order["status"],
        note="Auftrag aus dem Archiv wiederhergestellt.",
    )
    db.commit()
    return redirect(back_to_order_or_dashboard(order_id))


def render_order_form(form_data=None, errors=None, field_errors=None):
    default_form_data = default_order_form()
    if form_data:
        default_form_data.update(form_data)
    media_groups = split_media_items(default_form_data["media_items"])
    customer_directory = fetch_customer_directory()

    return render_template(
        "orders/new.html",
        technicians=TECHNICIANS,
        categories=CATEGORIES,
        statuses=ORDER_STATUSES,
        warranty_options=WARRANTY_OPTIONS,
        quote_options=QUOTE_OPTIONS,
        diagnostic_sources=DIAGNOSTIC_SOURCES,
        manufacturer_options=build_manufacturer_options(default_form_data["manufacturer"]),
        preferred_contact_options=PREFERRED_CONTACT_OPTIONS,
        document_types=DOCUMENT_TYPES,
        form_data=default_form_data,
        customer_directory=customer_directory,
        image_media=media_groups["images"],
        document_media=media_groups["documents"],
        errors=errors or [],
        field_errors=field_errors or {},
    )


def render_order_detail_page(order, errors=None, field_errors=None, order_media=None, quote=None, quote_errors=None, quote_form_data=None, invoice=None, invoice_errors=None, invoice_form_data=None):
    """Render the main workstation view with all secondary workflow blocks.

    The detail page is the operational center of BenchFlow. To keep route
    handlers simpler, this helper assembles media, history, quote and invoice
    state in one place and always returns a fully hydrated template context.
    """
    status_history = fetch_status_history(order["id"])
    order_media = order_media if order_media is not None else fetch_order_media(order["id"], fallback_image=order["image_data"])
    media_groups = split_media_items(order_media)
    quote = quote if quote is not None else fetch_order_quote(order["id"], required=False)
    quote_form_data = quote_form_data if quote_form_data is not None else build_quote_form_data(order, quote=quote)
    invoice = invoice if invoice is not None else fetch_order_invoice(order["id"], required=False)
    invoice_form_data = invoice_form_data if invoice_form_data is not None else build_invoice_form_data(order, invoice=invoice)
    return render_template(
        "order_detail.html",
        order=order,
        order_media=order_media,
        image_media=media_groups["images"],
        document_media=media_groups["documents"],
        status_history=status_history,
        technicians=TECHNICIANS,
        statuses=ORDER_STATUSES,
        categories=CATEGORIES,
        manufacturer_options=build_manufacturer_options(order["manufacturer"]),
        warranty_options=WARRANTY_OPTIONS,
        quote_options=QUOTE_OPTIONS,
        diagnostic_sources=DIAGNOSTIC_SOURCES,
        preferred_contact_options=PREFERRED_CONTACT_OPTIONS,
        document_types=DOCUMENT_TYPES,
        quote_approval_options=QUOTE_APPROVAL_OPTIONS,
        invoice_payment_options=INVOICE_PAYMENT_OPTIONS,
        quote=quote,
        quote_form_data=quote_form_data,
        quote_errors=quote_errors or [],
        invoice=invoice,
        invoice_form_data=invoice_form_data,
        invoice_errors=invoice_errors or [],
        errors=errors or [],
        field_errors=field_errors or {},
    )


def render_order_list(filters=None, archived=False):
    db = get_db()
    filters = filters or {"q": "", "status": "", "category": "", "document_type": ""}
    conditions = []
    params = []
    conditions.append("so.archived_at IS NOT NULL" if archived else "so.archived_at IS NULL")

    if filters["q"]:
        search = f"%{filters['q'].lower()}%"
        conditions.append(
            """
            (
                LOWER(so.order_number) LIKE ?
                OR LOWER(c.name) LIKE ?
                OR LOWER(c.company_name) LIKE ?
                OR LOWER(c.city) LIKE ?
                OR LOWER(d.manufacturer) LIKE ?
                OR LOWER(d.model) LIKE ?
                OR LOWER(d.serial_number) LIKE ?
            )
            """
        )
        params.extend([search, search, search, search, search, search, search])

    if filters["status"]:
        conditions.append("so.status = ?")
        params.append(filters["status"])

    if filters["category"]:
        conditions.append("d.category = ?")
        params.append(filters["category"])

    if filters["document_type"]:
        conditions.append(
            """
            EXISTS (
                SELECT 1
                FROM service_order_media som
                WHERE som.service_order_id = so.id
                  AND som.document_type = ?
            )
            """
        )
        params.append(filters["document_type"])

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    orders = fetch_orders(where_clause=where_clause, params=params)

    archived_count = db.execute(
        """
        SELECT COUNT(*) AS total
        FROM service_orders
        WHERE archived_at IS NOT NULL
        """
    ).fetchone()["total"]

    return render_template(
        "orders/archive.html" if archived else "orders/list.html",
        orders=orders,
        order_count=len(orders),
        categories=CATEGORIES,
        statuses=ORDER_STATUSES,
        document_types=DOCUMENT_TYPES,
        filters=filters,
        archived_count=archived_count,
    )


def fetch_orders(where_clause="", params=None, include_archived=False):
    db = get_db()
    params = params or []
    if include_archived and not where_clause:
        where_clause = ""

    rows = db.execute(
        f"""
        SELECT
            so.id,
            so.order_number,
            so.customer_id,
            so.device_id,
            c.name AS customer_name,
            c.company_name AS company_name,
            c.email AS customer_email,
            c.phone AS customer_phone,
            c.street AS customer_street,
            c.postal_code AS customer_postal_code,
            c.city AS customer_city,
            c.preferred_contact AS customer_preferred_contact,
            c.customer_notes AS customer_notes,
            d.category,
            d.manufacturer,
            d.model,
            d.serial_number,
            d.accessories,
            d.condition_notes,
            d.image_data,
            so.issue_description,
            so.status,
            so.technician,
            so.intake_date,
            so.warranty_status,
            so.quote_required,
            so.diagnostic_source,
            so.internal_notes,
            so.archived_at,
            so.created_at,
            (
                SELECT COUNT(*)
                FROM service_order_media som
                WHERE som.service_order_id = so.id
                  AND som.mime_type = 'application/pdf'
            ) AS document_count,
            (
                SELECT COUNT(DISTINCT COALESCE(NULLIF(som.document_type, ''), 'allgemein'))
                FROM service_order_media som
                WHERE som.service_order_id = so.id
                  AND som.mime_type = 'application/pdf'
            ) AS document_type_count,
            (
                SELECT COALESCE(NULLIF(som.document_type, ''), 'allgemein')
                FROM service_order_media som
                WHERE som.service_order_id = so.id
                  AND som.mime_type = 'application/pdf'
                ORDER BY datetime(som.created_at) ASC, som.id ASC
                LIMIT 1
            ) AS primary_document_type
        FROM service_orders so
        JOIN customers c ON c.id = so.customer_id
        JOIN devices d ON d.id = so.device_id
        {where_clause}
        ORDER BY
            CASE so.status
                WHEN 'Angenommen' THEN 1
                WHEN 'Diagnose' THEN 2
                WHEN 'Wartet auf Freigabe' THEN 3
                WHEN 'Freigegeben' THEN 4
                WHEN 'Abgelehnt' THEN 5
                WHEN 'Warten auf Teile' THEN 6
                WHEN 'In Reparatur' THEN 7
                WHEN 'Fertig' THEN 8
                WHEN 'Abholbereit' THEN 9
                WHEN 'Abgeschlossen' THEN 10
                ELSE 11
            END,
            so.intake_date ASC,
            so.id ASC
        """,
        params,
    ).fetchall()
    orders = [dict(row) for row in rows]
    for order in orders:
        order["document_hint"] = build_order_document_hint(order)
    return orders


def fetch_customer_directory():
    rows = get_db().execute(
        """
        SELECT
            id,
            name,
            company_name,
            email,
            phone,
            street,
            postal_code,
            city,
            preferred_contact,
            customer_notes
        FROM customers
        ORDER BY LOWER(name) ASC, LOWER(company_name) ASC, id ASC
        """
    ).fetchall()
    directory = []
    for row in rows:
        customer = dict(row)
        label_parts = [customer["name"]]
        if customer["company_name"]:
            label_parts.append(customer["company_name"])
        if customer["phone"]:
            label_parts.append(customer["phone"])
        elif customer["email"]:
            label_parts.append(customer["email"])
        customer["search_label"] = " | ".join(label_parts)
        directory.append(customer)
    return directory


def next_order_number(db):
    latest = db.execute(
        """
        SELECT order_number
        FROM service_orders
        WHERE order_number LIKE 'SO-%'
        ORDER BY id DESC
        LIMIT 1
        """
    ).fetchone()

    if latest is None:
        return "SO-1001"

    current_value = int(latest["order_number"].split("-")[1])
    return f"SO-{current_value + 1:04d}"


def normalize_category(value):
    valid_categories = {category for category, _label in CATEGORIES}
    return value if value in valid_categories else "sonstiges"


def fetch_order(order_id):
    order = get_db().execute(
        """
        SELECT
            so.id,
            so.order_number,
            so.customer_id,
            so.device_id,
            c.name AS customer_name,
            c.company_name AS company_name,
            c.email AS customer_email,
            c.phone AS customer_phone,
            c.street AS customer_street,
            c.postal_code AS customer_postal_code,
            c.city AS customer_city,
            c.preferred_contact AS customer_preferred_contact,
            c.customer_notes AS customer_notes,
            d.category,
            d.manufacturer,
            d.model,
            d.serial_number,
            d.accessories,
            d.condition_notes,
            d.image_data,
            so.issue_description,
            so.status,
            so.technician,
            so.intake_date,
            so.warranty_status,
            so.quote_required,
            so.diagnostic_source,
            so.internal_notes,
            so.archived_at,
            so.created_at,
            so.updated_at
        FROM service_orders so
        JOIN customers c ON c.id = so.customer_id
        JOIN devices d ON d.id = so.device_id
        WHERE so.id = ?
        """,
        (order_id,),
    ).fetchone()

    if order is None:
        abort(404)

    order = dict(order)
    order["customer_preferred_contact_label"] = build_preferred_contact_label(order.get("customer_preferred_contact", ""))
    return order


def fetch_order_quote(order_id, required=False):
    row = get_db().execute(
        """
        SELECT
            id,
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
            pdf_media_id,
            created_at,
            updated_at
        FROM service_order_quotes
        WHERE service_order_id = ?
        """,
        (order_id,),
    ).fetchone()
    if row is None:
        if required:
            abort(404)
        return None
    return annotate_quote(dict(row))


def fetch_order_invoice(order_id, required=False):
    row = get_db().execute(
        """
        SELECT
            id,
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
            pdf_media_id,
            created_at,
            updated_at
        FROM service_order_invoices
        WHERE service_order_id = ?
        """,
        (order_id,),
    ).fetchone()
    if row is None:
        if required:
            abort(404)
        return None
    return annotate_invoice(dict(row))


def fetch_customer(customer_id):
    customer = get_db().execute(
        """
        SELECT
            id,
            name,
            company_name,
            email,
            phone,
            street,
            postal_code,
            city,
            preferred_contact,
            customer_notes,
            created_at
        FROM customers
        WHERE id = ?
        """,
        (customer_id,),
    ).fetchone()
    if customer is None:
        abort(404)
    customer = dict(customer)
    customer["preferred_contact_label"] = build_preferred_contact_label(customer.get("preferred_contact", ""))
    return customer


def fetch_order_media(order_id, fallback_image=""):
    media_rows = get_db().execute(
        """
        SELECT id, filename, mime_type, document_type, order_context, media_data, created_at
        FROM service_order_media
        WHERE service_order_id = ?
        ORDER BY datetime(created_at) ASC, id ASC
        """,
        (order_id,),
    ).fetchall()
    media_items = [annotate_media_item(dict(row)) for row in media_rows]

    if not media_items and fallback_image:
        media_items.append(
            annotate_media_item({
                "id": "legacy-image",
                "filename": "legacy-device-image",
                "mime_type": "image/jpeg",
                "document_type": "",
                "order_context": "",
                "media_data": fallback_image,
                "created_at": "",
            })
        )

    return media_items


def fetch_order_media_item(order_id, media_id):
    media_item = get_db().execute(
        """
        SELECT id, filename, mime_type, document_type, order_context, media_data, created_at
        FROM service_order_media
        WHERE service_order_id = ?
          AND id = ?
        """,
        (order_id, media_id),
    ).fetchone()
    if media_item is None:
        abort(404)
    return annotate_media_item(dict(media_item))


def fetch_status_history(order_id):
    return get_db().execute(
        """
        SELECT id, status, note, changed_at
        FROM service_order_status_history
        WHERE service_order_id = ?
        ORDER BY datetime(changed_at) DESC, id DESC
        """,
        (order_id,),
    ).fetchall()


def back_to_order_or_dashboard(order_id):
    next_target = request.form.get("next", "").strip()
    if next_target == "detail":
        return url_for("benchflow.order_detail", order_id=order_id)
    if next_target == "archive":
        return url_for("benchflow.archive")
    return url_for("benchflow.orders")


def extract_order_form(include_status=False):
    form_data = {
        "customer_name": request.form.get("customer_name", "").strip(),
        "customer_email": request.form.get("customer_email", "").strip(),
        "customer_phone": request.form.get("customer_phone", "").strip(),
        "company_name": request.form.get("company_name", "").strip(),
        "street": request.form.get("street", "").strip(),
        "postal_code": request.form.get("postal_code", "").strip(),
        "city": request.form.get("city", "").strip(),
        "preferred_contact": request.form.get("preferred_contact", "").strip() or "telefon",
        "customer_notes": request.form.get("customer_notes", "").strip(),
        "category": request.form.get("category", "").strip(),
        "manufacturer": request.form.get("manufacturer", "").strip(),
        "model": request.form.get("model", "").strip(),
        "serial_number": request.form.get("serial_number", "").strip(),
        "accessories": request.form.get("accessories", "").strip(),
        "condition_notes": request.form.get("condition_notes", "").strip(),
        "issue_description": request.form.get("issue_description", "").strip(),
        "technician": request.form.get("technician", "").strip(),
        "intake_date": request.form.get("intake_date", "").strip() or date.today().isoformat(),
        "warranty_status": request.form.get("warranty_status", "").strip(),
        "quote_required": request.form.get("quote_required", "").strip(),
        "diagnostic_source": request.form.get("diagnostic_source", "").strip() or "Werkbank",
        "document_type": request.form.get("document_type", "").strip(),
        "document_context": request.form.get("document_context", "").strip(),
        "internal_notes": request.form.get("internal_notes", "").strip(),
        "image_data": "",
        "media_items": [],
    }

    if include_status:
        form_data["status"] = request.form.get("status", "").strip()

    return form_data


def default_order_form():
    return {
        "customer_name": "",
        "customer_email": "",
        "customer_phone": "",
        "company_name": "",
        "street": "",
        "postal_code": "",
        "city": "",
        "preferred_contact": "telefon",
        "customer_notes": "",
        "category": "",
        "manufacturer": "",
        "model": "",
        "serial_number": "",
        "accessories": "",
        "condition_notes": "",
        "issue_description": "",
        "technician": "",
        "intake_date": date.today().isoformat(),
        "warranty_status": "unbekannt",
        "quote_required": "nein",
        "diagnostic_source": "Werkbank",
        "document_type": "",
        "document_context": "",
        "internal_notes": "",
        "image_data": "",
        "media_items": [],
        "status": "Angenommen",
    }


def build_quote_form_data(order, quote=None):
    if quote:
        return {
            "title": quote["title"],
            "work_description": quote["work_description"],
            "parts_description": quote["parts_description"],
            "labor_cost": cents_to_input(quote["labor_cost_cents"]),
            "parts_cost": cents_to_input(quote["parts_cost_cents"]),
            "external_cost": cents_to_input(quote["external_cost_cents"]),
            "shipping_cost": cents_to_input(quote["shipping_cost_cents"]),
            "valid_until": quote["valid_until"],
            "customer_message": quote["customer_message"],
            "approval_status": quote["approval_status"],
            "labor_cost_cents": quote["labor_cost_cents"],
            "parts_cost_cents": quote["parts_cost_cents"],
            "external_cost_cents": quote["external_cost_cents"],
            "shipping_cost_cents": quote["shipping_cost_cents"],
        }
    return {
        "title": f"Kostenvoranschlag {order['order_number']}",
        "work_description": "",
        "parts_description": "",
        "labor_cost": "0,00",
        "parts_cost": "0,00",
        "external_cost": "0,00",
        "shipping_cost": "0,00",
        "valid_until": (date.today() + timedelta(days=14)).isoformat(),
        "customer_message": "",
        "approval_status": "offen",
        "labor_cost_cents": 0,
        "parts_cost_cents": 0,
        "external_cost_cents": 0,
        "shipping_cost_cents": 0,
    }


def build_invoice_form_data(order, invoice=None):
    if invoice:
        return {
            "title": invoice["title"],
            "labor_description": invoice["labor_description"],
            "parts_description": invoice["parts_description"],
            "labor_cost": cents_to_input(invoice["labor_cost_cents"]),
            "parts_cost": cents_to_input(invoice["parts_cost_cents"]),
            "external_cost": cents_to_input(invoice["external_cost_cents"]),
            "shipping_cost": cents_to_input(invoice["shipping_cost_cents"]),
            "invoice_date": invoice["invoice_date"],
            "payment_status": invoice["payment_status"],
            "internal_note": invoice["internal_note"],
            "labor_cost_cents": invoice["labor_cost_cents"],
            "parts_cost_cents": invoice["parts_cost_cents"],
            "external_cost_cents": invoice["external_cost_cents"],
            "shipping_cost_cents": invoice["shipping_cost_cents"],
        }
    return {
        "title": f"Rechnung {order['order_number']}",
        "labor_description": "",
        "parts_description": "",
        "labor_cost": "0,00",
        "parts_cost": "0,00",
        "external_cost": "0,00",
        "shipping_cost": "0,00",
        "invoice_date": date.today().isoformat(),
        "payment_status": "offen",
        "internal_note": "",
        "labor_cost_cents": 0,
        "parts_cost_cents": 0,
        "external_cost_cents": 0,
        "shipping_cost_cents": 0,
    }


def extract_quote_form(existing_quote=None, order=None):
    order = order or {}
    quote_form = build_quote_form_data(order, quote=existing_quote) if order else {}
    quote_form.update(
        {
            "title": request.form.get("quote_title", "").strip() or quote_form.get("title", ""),
            "work_description": request.form.get("quote_work_description", "").strip(),
            "parts_description": request.form.get("quote_parts_description", "").strip(),
            "labor_cost": request.form.get("quote_labor_cost", "").strip() or quote_form.get("labor_cost", "0,00"),
            "parts_cost": request.form.get("quote_parts_cost", "").strip() or quote_form.get("parts_cost", "0,00"),
            "external_cost": request.form.get("quote_external_cost", "").strip() or quote_form.get("external_cost", "0,00"),
            "shipping_cost": request.form.get("quote_shipping_cost", "").strip() or quote_form.get("shipping_cost", "0,00"),
            "valid_until": request.form.get("quote_valid_until", "").strip(),
            "customer_message": request.form.get("quote_customer_message", "").strip(),
            "approval_status": request.form.get("quote_approval_status", "").strip() or "offen",
        }
    )
    quote_form["labor_cost_cents"] = parse_currency_to_cents(quote_form["labor_cost"])
    quote_form["parts_cost_cents"] = parse_currency_to_cents(quote_form["parts_cost"])
    quote_form["external_cost_cents"] = parse_currency_to_cents(quote_form["external_cost"])
    quote_form["shipping_cost_cents"] = parse_currency_to_cents(quote_form["shipping_cost"])
    return quote_form


def validate_quote_form(quote_form_data):
    errors = []
    if not quote_form_data["title"]:
        errors.append("Bitte einen Titel für den Kostenvoranschlag eintragen.")
    if len(quote_form_data["title"]) > 120:
        errors.append("Der KVA-Titel ist zu lang.")
    if not quote_form_data["work_description"]:
        errors.append("Bitte den Arbeitsumfang für den Kostenvoranschlag beschreiben.")
    if len(quote_form_data["work_description"]) > 1200:
        errors.append("Der Arbeitsumfang ist zu lang.")
    if len(quote_form_data["parts_description"]) > 1200:
        errors.append("Die Teilebeschreibung ist zu lang.")
    if len(quote_form_data["customer_message"]) > 600:
        errors.append("Die Kundennachricht ist zu lang.")
    if quote_form_data["approval_status"] not in {value for value, _label in QUOTE_APPROVAL_OPTIONS}:
        errors.append("Der Freigabestatus für den Kostenvoranschlag ist ungültig.")
    for field_name in ("labor_cost", "parts_cost", "external_cost", "shipping_cost"):
        if parse_currency_to_cents(quote_form_data[field_name]) is None:
            errors.append("Bitte für alle KVA-Beträge gültige Zahlen verwenden.")
            break
    if quote_form_data["valid_until"]:
        try:
            date.fromisoformat(quote_form_data["valid_until"])
        except ValueError:
            errors.append("Das Gültig-bis-Datum ist ungültig.")
    return errors


def extract_invoice_form(existing_invoice=None, order=None):
    order = order or {}
    invoice_form = build_invoice_form_data(order, invoice=existing_invoice) if order else {}
    invoice_form.update(
        {
            "title": request.form.get("invoice_title", "").strip() or invoice_form.get("title", ""),
            "labor_description": request.form.get("invoice_labor_description", "").strip(),
            "parts_description": request.form.get("invoice_parts_description", "").strip(),
            "labor_cost": request.form.get("invoice_labor_cost", "").strip() or invoice_form.get("labor_cost", "0,00"),
            "parts_cost": request.form.get("invoice_parts_cost", "").strip() or invoice_form.get("parts_cost", "0,00"),
            "external_cost": request.form.get("invoice_external_cost", "").strip() or invoice_form.get("external_cost", "0,00"),
            "shipping_cost": request.form.get("invoice_shipping_cost", "").strip() or invoice_form.get("shipping_cost", "0,00"),
            "invoice_date": request.form.get("invoice_date", "").strip() or date.today().isoformat(),
            "payment_status": request.form.get("invoice_payment_status", "").strip() or "offen",
            "internal_note": request.form.get("invoice_internal_note", "").strip(),
        }
    )
    invoice_form["labor_cost_cents"] = parse_currency_to_cents(invoice_form["labor_cost"])
    invoice_form["parts_cost_cents"] = parse_currency_to_cents(invoice_form["parts_cost"])
    invoice_form["external_cost_cents"] = parse_currency_to_cents(invoice_form["external_cost"])
    invoice_form["shipping_cost_cents"] = parse_currency_to_cents(invoice_form["shipping_cost"])
    return invoice_form


def validate_invoice_form(invoice_form_data):
    errors = []
    if not invoice_form_data["title"]:
        errors.append("Bitte einen Titel für die Rechnung eintragen.")
    if len(invoice_form_data["title"]) > 120:
        errors.append("Der Rechnungstitel ist zu lang.")
    if not invoice_form_data["labor_description"]:
        errors.append("Bitte die berechnete Leistung beschreiben.")
    if len(invoice_form_data["labor_description"]) > 1200:
        errors.append("Die Leistungsbeschreibung ist zu lang.")
    if len(invoice_form_data["parts_description"]) > 1200:
        errors.append("Die Teilebeschreibung der Rechnung ist zu lang.")
    if len(invoice_form_data["internal_note"]) > 600:
        errors.append("Die interne Rechnungsnotiz ist zu lang.")
    if invoice_form_data["payment_status"] not in {value for value, _label in INVOICE_PAYMENT_OPTIONS}:
        errors.append("Der Zahlungsstatus ist ungültig.")
    for field_name in ("labor_cost", "parts_cost", "external_cost", "shipping_cost"):
        if parse_currency_to_cents(invoice_form_data[field_name]) is None:
            errors.append("Bitte für alle Rechnungsbeträge gültige Zahlen verwenden.")
            break
    if invoice_form_data["invoice_date"]:
        try:
            date.fromisoformat(invoice_form_data["invoice_date"])
        except ValueError:
            errors.append("Das Rechnungsdatum ist ungültig.")
    return errors


def validate_order_form(form_data, require_status=False):
    field_errors = {}

    def add_error(field_name, message):
        if field_name not in field_errors:
            field_errors[field_name] = message

    if not form_data["customer_name"]:
        add_error("customer_name", "Bitte einen Kundennamen eintragen.")
    elif len(form_data["customer_name"]) < 2:
        add_error("customer_name", "Der Kundenname ist zu kurz.")

    if not form_data["customer_phone"]:
        add_error("customer_phone", "Bitte eine Telefonnummer erfassen.")

    if form_data["customer_email"] and "@" not in form_data["customer_email"]:
        add_error("customer_email", "Bitte eine gültige E-Mail-Adresse eintragen.")
    if form_data["postal_code"] and len(form_data["postal_code"]) < 4:
        add_error("postal_code", "Die PLZ ist zu kurz.")
    if form_data["preferred_contact"] and form_data["preferred_contact"] not in {value for value, _label in PREFERRED_CONTACT_OPTIONS}:
        add_error("preferred_contact", "Der bevorzugte Kontaktweg ist ungültig.")

    if not form_data["category"]:
        add_error("category", "Bitte eine Gerätekategorie auswählen.")
    elif form_data["category"] not in {value for value, _label in CATEGORIES}:
        add_error("category", "Die ausgewählte Kategorie ist ungültig.")

    if not form_data["manufacturer"]:
        add_error("manufacturer", "Bitte einen Hersteller eintragen.")
    elif len(form_data["manufacturer"]) < 2:
        add_error("manufacturer", "Der Hersteller ist zu kurz.")

    if not form_data["model"]:
        add_error("model", "Bitte ein Modell eintragen.")
    elif len(form_data["model"]) < 2:
        add_error("model", "Das Modell ist zu kurz.")

    if not form_data["issue_description"]:
        add_error("issue_description", "Bitte das Fehlerbild kurz beschreiben.")
    elif len(form_data["issue_description"]) < 5:
        add_error("issue_description", "Die Fehlerbeschreibung ist noch zu knapp.")

    if not form_data["technician"]:
        add_error("technician", "Bitte eine zuständige Person auswählen.")
    elif form_data["technician"] not in TECHNICIANS:
        add_error("technician", "Die ausgewählte Technik ist ungültig.")

    if form_data["warranty_status"] and form_data["warranty_status"] not in {value for value, _label in WARRANTY_OPTIONS}:
        add_error("warranty_status", "Die Garantieangabe ist ungültig.")
    if form_data["quote_required"] and form_data["quote_required"] not in {value for value, _label in QUOTE_OPTIONS}:
        add_error("quote_required", "Die KV-Angabe ist ungültig.")
    if form_data["diagnostic_source"] and form_data["diagnostic_source"] not in DIAGNOSTIC_SOURCES:
        add_error("diagnostic_source", "Die Diagnosequelle ist ungültig.")
    if form_data["document_type"] and form_data["document_type"] not in {value for value, _label in DOCUMENT_TYPES if value}:
        add_error("document_type", "Der Dokumenttyp ist ungültig.")
    if len(form_data["document_context"]) > 220:
        add_error("document_context", "Der Bezug zum Auftrag ist zu lang.")
    if require_status and not form_data.get("status"):
        add_error("status", "Bitte einen Status setzen.")
    elif require_status and form_data.get("status") and form_data["status"] not in ORDER_STATUSES:
        add_error("status", "Der ausgewählte Status ist ungültig.")

    errors = list(field_errors.values())
    return errors, field_errors


def process_uploaded_order_media():
    """Validate uploads once and normalize them into media-table payloads.

    Images and PDFs share one attachment pipeline, but only PDFs receive a
    document type and an optional order context. The result is pre-annotated
    so failed form submissions can re-render without losing attachment state.
    """
    uploads = [upload for upload in request.files.getlist("order_files") if upload and upload.filename]
    if not uploads:
        uploads = [upload for upload in request.files.getlist("device_images") if upload and upload.filename]
    if not uploads:
        return [], ""
    requested_document_type = request.form.get("document_type", "").strip()
    requested_document_context = request.form.get("document_context", "").strip()
    allowed_types = {
        "image/jpeg": {"extension": "jpeg", "max_size": 2 * 1024 * 1024},
        "image/png": {"extension": "png", "max_size": 2 * 1024 * 1024},
        "image/webp": {"extension": "webp", "max_size": 2 * 1024 * 1024},
        "application/pdf": {"extension": "pdf", "max_size": 5 * 1024 * 1024},
    }
    media_items = []

    for upload in uploads:
        if upload.mimetype not in allowed_types:
            return [], "Bitte nur JPG-, PNG-, WEBP-Bilder oder PDF-Dokumente hochladen."

        raw_bytes = upload.read()
        if not raw_bytes:
            continue
        size_limit = allowed_types[upload.mimetype]["max_size"]
        if len(raw_bytes) > size_limit:
            if upload.mimetype == "application/pdf":
                return [], "Jedes PDF darf maximal 5 MB gross sein."
            return [], "Jede Bilddatei darf maximal 2 MB gross sein."

        encoded = base64.b64encode(raw_bytes).decode("ascii")
        media_items.append(
            annotate_media_item({
                "filename": upload.filename,
                "mime_type": upload.mimetype,
                "document_type": requested_document_type if upload.mimetype == "application/pdf" else "",
                "order_context": requested_document_context if upload.mimetype == "application/pdf" else "",
                "media_data": f"data:{upload.mimetype};base64,{encoded}",
                "created_at": "",
            })
        )

    return media_items, ""


def guess_mime_type(media_data):
    if media_data.startswith("data:image/png"):
        return "image/png"
    if media_data.startswith("data:image/webp"):
        return "image/webp"
    if media_data.startswith("data:application/pdf"):
        return "application/pdf"
    return "image/jpeg"


def decode_media_data(media_data):
    if "," not in media_data:
        abort(404)
    _prefix, encoded = media_data.split(",", 1)
    return base64.b64decode(encoded)


def extract_document_updates(form):
    valid_types = {value for value, _label in DOCUMENT_TYPES}
    updates = {}
    for key in form.keys():
        if not key.startswith("document_type_"):
            continue
        media_id = key.removeprefix("document_type_")
        if not media_id.isdigit():
            continue
        selected_type = form.get(key, "").strip()
        if selected_type in valid_types:
            updates[int(media_id)] = {
                "filename": form.get(f"document_name_{media_id}", "").strip(),
                "document_type": selected_type,
                "order_context": form.get(f"document_context_{media_id}", "").strip()[:220],
            }
    return updates


def normalize_media_filename(raw_value, existing_filename=""):
    filename = Path((raw_value or "").strip()).name
    existing_filename = Path((existing_filename or "").strip()).name
    if not filename:
        return existing_filename

    if "." not in filename and existing_filename:
        existing_suffix = Path(existing_filename).suffix
        if existing_suffix:
            filename = f"{filename}{existing_suffix}"

    return filename[:160]


def annotate_media_item(media_item):
    mime_type = media_item.get("mime_type") or guess_mime_type(media_item.get("media_data", ""))
    media_item["mime_type"] = mime_type
    media_item["is_image"] = mime_type.startswith("image/")
    media_item["is_document"] = not media_item["is_image"]
    media_item["display_name"] = media_item.get("filename") or ("Dokumentationsbild" if media_item["is_image"] else "Dokument")
    media_item["document_type"] = media_item.get("document_type", "")
    media_item["order_context"] = media_item.get("order_context", "")
    media_item["document_type_label"] = "Bilddokumentation" if media_item["is_image"] else build_document_type_label(media_item["document_type"])
    media_item["size_label"] = format_media_size(media_item.get("media_data", ""))
    media_item["created_label"] = format_created_timestamp(media_item.get("created_at", ""))
    return media_item


def split_media_items(media_items):
    return {
        "images": [item for item in media_items if item["is_image"]],
        "documents": [item for item in media_items if item["is_document"]],
    }


def build_customer_short_label(customer_name):
    cleaned = " ".join((customer_name or "").split())
    if not cleaned:
        return "Unbekannt"
    parts = cleaned.split(" ")
    if len(parts) == 1:
        return parts[0][:12]
    first = parts[0][:1].upper()
    last = parts[-1][:12]
    return f"{first}. {last}"


def build_device_label_text(order):
    serial = order["serial_number"] or "ohne SN"
    category_label = dict(CATEGORIES).get(order["category"], order["category"])
    return f"{category_label} | {serial}"


def build_document_type_label(document_type):
    return dict(DOCUMENT_TYPES).get(document_type, "Allgemeines Dokument")


def build_preferred_contact_label(value):
    return dict(PREFERRED_CONTACT_OPTIONS).get(value, value or "-")


def build_manufacturer_options(selected_value=""):
    options = list(MANUFACTURER_OPTIONS)
    selected_value = (selected_value or "").strip()
    if selected_value and selected_value not in options:
        options.insert(0, selected_value)
    return options


def build_quote_approval_label(value):
    return dict(QUOTE_APPROVAL_OPTIONS).get(value, value or "-")


def annotate_quote(quote):
    quote["approval_status_label"] = build_quote_approval_label(quote["approval_status"])
    quote["labor_cost_label"] = format_currency_cents(quote["labor_cost_cents"])
    quote["parts_cost_label"] = format_currency_cents(quote["parts_cost_cents"])
    quote["external_cost_label"] = format_currency_cents(quote["external_cost_cents"])
    quote["shipping_cost_label"] = format_currency_cents(quote["shipping_cost_cents"])
    quote["total_cost_label"] = format_currency_cents(quote["total_cost_cents"])
    return quote


def annotate_invoice(invoice):
    invoice["payment_status_label"] = dict(INVOICE_PAYMENT_OPTIONS).get(invoice["payment_status"], invoice["payment_status"])
    invoice["labor_cost_label"] = format_currency_cents(invoice["labor_cost_cents"])
    invoice["parts_cost_label"] = format_currency_cents(invoice["parts_cost_cents"])
    invoice["external_cost_label"] = format_currency_cents(invoice["external_cost_cents"])
    invoice["shipping_cost_label"] = format_currency_cents(invoice["shipping_cost_cents"])
    invoice["total_cost_label"] = format_currency_cents(invoice["total_cost_cents"])
    return invoice


def merge_quote_for_render(existing_quote, quote_form_data):
    payload = dict(existing_quote) if existing_quote else {}
    payload.update(
        {
            "title": quote_form_data["title"],
            "work_description": quote_form_data["work_description"],
            "parts_description": quote_form_data["parts_description"],
            "labor_cost_cents": quote_form_data["labor_cost_cents"] or 0,
            "parts_cost_cents": quote_form_data["parts_cost_cents"] or 0,
            "external_cost_cents": quote_form_data["external_cost_cents"] or 0,
            "shipping_cost_cents": quote_form_data["shipping_cost_cents"] or 0,
            "total_cost_cents": compute_quote_total_cents(quote_form_data),
            "valid_until": quote_form_data["valid_until"],
            "customer_message": quote_form_data["customer_message"],
            "approval_status": quote_form_data["approval_status"],
        }
    )
    payload.setdefault("quote_number", "")
    payload.setdefault("pdf_media_id", None)
    return annotate_quote(payload)


def merge_invoice_for_render(existing_invoice, invoice_form_data):
    payload = dict(existing_invoice) if existing_invoice else {}
    payload.update(
        {
            "title": invoice_form_data["title"],
            "labor_description": invoice_form_data["labor_description"],
            "parts_description": invoice_form_data["parts_description"],
            "labor_cost_cents": invoice_form_data["labor_cost_cents"] or 0,
            "parts_cost_cents": invoice_form_data["parts_cost_cents"] or 0,
            "external_cost_cents": invoice_form_data["external_cost_cents"] or 0,
            "shipping_cost_cents": invoice_form_data["shipping_cost_cents"] or 0,
            "total_cost_cents": compute_invoice_total_cents(invoice_form_data),
            "invoice_date": invoice_form_data["invoice_date"],
            "payment_status": invoice_form_data["payment_status"],
            "internal_note": invoice_form_data["internal_note"],
        }
    )
    payload.setdefault("invoice_number", "")
    payload.setdefault("pdf_media_id", None)
    return annotate_invoice(payload)


def build_order_document_hint(order):
    document_count = order.get("document_count", 0) or 0
    if not document_count:
        return ""

    if (order.get("document_type_count", 0) or 0) > 1:
        document_type_label = "gemischt"
    else:
        document_type_label = build_document_type_label(order.get("primary_document_type", ""))

    document_label = "Dokument" if document_count == 1 else "Dokumente"
    return f"{document_count} {document_label} · {document_type_label}"


def format_media_size(media_data):
    if "," not in media_data:
        return ""
    _prefix, encoded = media_data.split(",", 1)
    raw_size = len(base64.b64decode(encoded))
    if raw_size < 1024:
        return f"{raw_size} B"
    if raw_size < 1024 * 1024:
        return f"{raw_size / 1024:.0f} KB"
    return f"{raw_size / (1024 * 1024):.1f} MB"


def format_created_timestamp(timestamp):
    if not timestamp:
        return ""
    return timestamp[:10]


def parse_currency_to_cents(raw_value):
    normalized = (raw_value or "").strip().replace("EUR", "").replace("eur", "").replace(" ", "")
    if not normalized:
        return 0
    normalized = normalized.replace(".", "").replace(",", ".")
    if normalized.count(".") > 1:
        return None
    try:
        value = float(normalized)
    except ValueError:
        return None
    if value < 0:
        return None
    return int(round(value * 100))


def cents_to_input(value):
    euros = (value or 0) / 100
    return f"{euros:.2f}".replace(".", ",")


def format_currency_cents(value):
    euros = (value or 0) / 100
    return f"{euros:,.2f} EUR".replace(",", "X").replace(".", ",").replace("X", ".")


def compute_quote_total_cents(quote_form_data):
    return sum(
        quote_form_data.get(key, 0) or 0
        for key in ("labor_cost_cents", "parts_cost_cents", "external_cost_cents", "shipping_cost_cents")
    )


def compute_invoice_total_cents(invoice_form_data):
    return sum(
        invoice_form_data.get(key, 0) or 0
        for key in ("labor_cost_cents", "parts_cost_cents", "external_cost_cents", "shipping_cost_cents")
    )


def build_quote_number(order):
    return f"KVA-{order['order_number'].replace('-', '')}"


def build_invoice_number(order):
    return f"RE-{order['order_number'].replace('-', '')}"


def build_order_status_from_quote_approval(approval_status):
    mapping = {
        "offen": "Wartet auf Freigabe",
        "freigegeben": "Freigegeben",
        "abgelehnt": "Abgelehnt",
    }
    return mapping.get(approval_status, "Wartet auf Freigabe")


def build_quote_history_note(existing_quote, approval_status, total_cost_cents):
    total_label = format_currency_cents(total_cost_cents)
    if not existing_quote:
        return f"Kostenvoranschlag erstellt ({total_label})."
    if approval_status == "freigegeben":
        return f"Kostenvoranschlag freigegeben ({total_label})."
    if approval_status == "abgelehnt":
        return f"Kostenvoranschlag abgelehnt ({total_label})."
    return f"Kostenvoranschlag aktualisiert ({total_label})."


def build_invoice_history_note(existing_invoice, payment_status, total_cost_cents):
    total_label = format_currency_cents(total_cost_cents)
    if not existing_invoice:
        return f"Rechnung erstellt ({total_label})."
    if payment_status == "bezahlt":
        return f"Rechnung als bezahlt markiert ({total_label})."
    return f"Rechnung aktualisiert ({total_label})."


def encode_pdf_bytes(pdf_bytes):
    encoded = base64.b64encode(pdf_bytes).decode("ascii")
    return f"data:application/pdf;base64,{encoded}"


def wrap_pdf_lines(text, width=82):
    lines = []
    for raw_line in (text or "").splitlines():
        raw_line = raw_line.strip()
        if not raw_line:
            lines.append("")
            continue
        lines.extend(textwrap.wrap(raw_line, width=width) or [""])
    return lines


def pdf_escape(text):
    return (
        (text or "")
        .replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
    )


def build_quote_pdf(order, quote_form_data, quote_number, total_cost_cents):
    """Build the branded A4 quote PDF with the current BenchFlow layout.

    This is kept server-side and dependency-light on purpose. The generated PDF
    uses a small custom drawing layer so quote output stays deterministic even
    without HTML-to-PDF tooling in local workshop setups.
    """
    customer_lines = [order["customer_name"]]
    if order.get("company_name"):
        customer_lines.append(order["company_name"])
    address_line = " ".join(part for part in [order.get("customer_postal_code", ""), order.get("customer_city", "")] if part)
    if order.get("customer_street"):
        customer_lines.append(order["customer_street"])
    if address_line:
        customer_lines.append(address_line)
    left = 48
    right = 547
    page_height = 842
    bottom_margin = 56
    logo_image = load_logo_pdf_image()
    page_commands = []
    current_page = []
    page_commands.append(current_page)
    y = 792

    def start_new_page():
        nonlocal current_page, y
        current_page = []
        page_commands.append(current_page)
        y = 792
        draw_page_header(compact=True)

    def ensure_space(height):
        nonlocal y
        if y - height < bottom_margin:
            start_new_page()

    def draw_text(x, current_y, text, font="F1", size=11, gray=0.08):
        safe = pdf_escape(text)
        current_page.append(f"BT {gray:.2f} g /{font} {size} Tf 1 0 0 1 {x} {current_y} Tm ({safe}) Tj ET")

    def draw_line(x1, y1, x2, y2, width=1, gray=0.78):
        current_page.append(f"{gray:.2f} G {width} w {x1} {y1} m {x2} {y2} l S")

    def draw_rect(x, rect_y, width, height, stroke_gray=0.82, fill_gray=None):
        if fill_gray is not None:
            current_page.append(f"{fill_gray:.2f} g")
            current_page.append(f"{x} {rect_y} {width} {height} re f")
        current_page.append(f"{stroke_gray:.2f} G 1 w {x} {rect_y} {width} {height} re S")

    def draw_image(name, x, bottom_y, width, height):
        current_page.append(f"q {width} 0 0 {height} {x} {bottom_y} cm /{name} Do Q")

    def draw_wrapped_block(label, text, width=62):
        nonlocal y
        wrapped = wrap_pdf_lines(text, width=width) or [""]
        needed = 22 + (len(wrapped) * 12)
        ensure_space(needed)
        draw_text(left, y, label, font="F2", size=12)
        y -= 16
        for line in wrapped:
            draw_text(left, y, line, size=11)
            y -= 12
        y -= 8

    def draw_two_column_sections(sections):
        nonlocal y
        column_gap = 24
        column_width = (right - left - column_gap) / 2
        # These sections are the main compaction lever so the quote typically
        # stays on one A4 page even after adding logo and workflow meta data.
        rows = [sections[index:index + 2] for index in range(0, len(sections), 2)]
        for row in rows:
            prepared = []
            row_height = 0
            for label, text in row:
                wrapped = wrap_pdf_lines(text, width=34) or [""]
                block_height = 20 + (len(wrapped) * 12) + 6
                prepared.append((label, wrapped, block_height))
                row_height = max(row_height, block_height)
            ensure_space(row_height + 6)
            row_top = y
            for column_index, (label, wrapped, _block_height) in enumerate(prepared):
                column_x = left + column_index * (column_width + column_gap)
                draw_text(column_x, row_top, label, font="F2", size=12)
                line_y = row_top - 16
                for line in wrapped:
                    draw_text(column_x, line_y, line, size=11)
                    line_y -= 12
            y -= row_height + 6

    def draw_page_header(compact=False):
        nonlocal y
        title_size = 18 if not compact else 15
        subtitle_size = 10 if not compact else 9
        logo_width = 150 if not compact else 124
        logo_height = logo_width * (logo_image["height"] / logo_image["width"])
        draw_image("ImLogo", left, y - logo_height + 2, logo_width, logo_height)
        title_y = y - logo_height - 16
        subtitle_y = title_y - 16
        draw_text(left, title_y, "KOSTENVORANSCHLAG", font="F2", size=title_size, gray=0.05)
        draw_text(left, subtitle_y, quote_form_data["title"], size=subtitle_size, gray=0.12)
        draw_text(405, y, quote_number, font="F2", size=12, gray=0.05)
        draw_text(405, y - 18, f"Datum  {date.today().isoformat()}", size=10, gray=0.15)
        draw_text(405, y - 32, f"Gültig bis  {quote_form_data['valid_until'] or '-'}", size=10, gray=0.15)
        draw_text(405, y - 46, f"Auftrag  {order['order_number']}", size=10, gray=0.15)
        divider_y = subtitle_y - 14
        draw_line(left, divider_y, right, divider_y)
        y = divider_y - 18

    draw_page_header()

    draw_text(left, y, "Kunde", font="F2", size=11)
    for idx, line in enumerate(customer_lines, start=1):
        draw_text(left, y - (idx * 14), line, size=11)

    meta_x = 305
    draw_rect(meta_x - 12, y - 82, 254, 94, fill_gray=0.96)
    draw_text(meta_x, y, "Gerät", font="F2", size=11)
    draw_text(meta_x, y - 18, f"{order['manufacturer']} {order['model']}", size=11)
    draw_text(meta_x, y - 36, f"Kategorie  {dict(CATEGORIES).get(order['category'], order['category'])}", size=10)
    draw_text(meta_x, y - 50, f"Seriennummer  {order['serial_number'] or '-'}", size=10)
    draw_text(meta_x, y - 64, f"Kontaktweg  {order['customer_preferred_contact_label']}", size=10)
    y -= 104

    draw_line(left, y, right, y, gray=0.88)
    y -= 18
    detail_sections = [("Arbeitsumfang", quote_form_data["work_description"])]
    if quote_form_data["parts_description"]:
        detail_sections.append(("Teile und Fremdleistungen", quote_form_data["parts_description"]))
    if quote_form_data["customer_message"]:
        detail_sections.append(("Hinweis für den Kunden", quote_form_data["customer_message"]))
    draw_two_column_sections(detail_sections)

    ensure_space(150)
    draw_text(left, y, "Kostenübersicht", font="F2", size=12)
    y -= 14
    cost_box_height = 128
    draw_rect(left, y - cost_box_height + 10, right - left, cost_box_height, fill_gray=0.97)
    cost_rows = [
        ("Arbeitskosten", format_currency_cents(quote_form_data["labor_cost_cents"])),
        ("Teilekosten", format_currency_cents(quote_form_data["parts_cost_cents"])),
        ("Fremdleistung", format_currency_cents(quote_form_data["external_cost_cents"])),
        ("Versand / Sonstiges", format_currency_cents(quote_form_data["shipping_cost_cents"])),
    ]
    row_y = y - 14
    for label, value in cost_rows:
        draw_text(left + 14, row_y, label, size=11)
        draw_text(430, row_y, value, font="F2", size=11)
        row_y -= 18
    total_line_y = row_y
    draw_line(left + 14, total_line_y, right - 14, total_line_y, gray=0.80)
    draw_text(left + 14, total_line_y - 22, "Gesamt", font="F2", size=12)
    draw_text(430, total_line_y - 22, format_currency_cents(total_cost_cents), font="F2", size=12)
    y = y - cost_box_height - 10

    ensure_space(92)
    draw_rect(left, y - 66, right - left, 76, fill_gray=0.95)
    draw_text(left + 14, y - 14, "Freigabestatus", font="F2", size=11)
    draw_text(left + 14, y - 36, build_quote_approval_label(quote_form_data["approval_status"]), size=11)
    draw_text(300, y - 30, "Wenn alles für Sie passt,", size=10, gray=0.16)
    draw_text(300, y - 44, "geben Sie uns einfach kurz Bescheid.", size=10, gray=0.16)
    y -= 88

    ensure_space(58)
    draw_line(left, y, right, y, gray=0.86)
    draw_text(left, y - 20, "Rückfragen", font="F2", size=10)
    draw_text(left, y - 36, "Melden Sie sich gern mit Ihrer Bearbeitungsnummer bei uns.", size=10)
    draw_text(395, y - 20, f"Bearbeitungsnummer  {order['order_number']}", font="F2", size=10)

    return build_pdf_document(page_commands, page_height=page_height, image_objects={"ImLogo": load_logo_pdf_image()})


def build_invoice_pdf(order, invoice_form_data, invoice_number, total_cost_cents):
    """Build the invoice PDF.

    The invoice mirrors the quote layout closely so both customer-facing
    documents feel like one coherent system instead of two separate exports.
    """
    customer_lines = [order["customer_name"]]
    if order.get("company_name"):
        customer_lines.append(order["company_name"])
    address_line = " ".join(part for part in [order.get("customer_postal_code", ""), order.get("customer_city", "")] if part)
    if order.get("customer_street"):
        customer_lines.append(order["customer_street"])
    if address_line:
        customer_lines.append(address_line)

    left = 48
    right = 547
    page_height = 842
    bottom_margin = 56
    logo_image = load_logo_pdf_image()
    page_commands = []
    current_page = []
    page_commands.append(current_page)
    y = 792

    def start_new_page():
        nonlocal current_page, y
        current_page = []
        page_commands.append(current_page)
        y = 792
        draw_page_header(compact=True)

    def ensure_space(height):
        nonlocal y
        if y - height < bottom_margin:
            start_new_page()

    def draw_text(x, current_y, text, font="F1", size=11, gray=0.08):
        safe = pdf_escape(text)
        current_page.append(f"BT {gray:.2f} g /{font} {size} Tf 1 0 0 1 {x} {current_y} Tm ({safe}) Tj ET")

    def draw_line(x1, y1, x2, y2, width=1, gray=0.78):
        current_page.append(f"{gray:.2f} G {width} w {x1} {y1} m {x2} {y2} l S")

    def draw_rect(x, rect_y, width, height, stroke_gray=0.82, fill_gray=None):
        if fill_gray is not None:
            current_page.append(f"{fill_gray:.2f} g")
            current_page.append(f"{x} {rect_y} {width} {height} re f")
        current_page.append(f"{stroke_gray:.2f} G 1 w {x} {rect_y} {width} {height} re S")

    def draw_image(name, x, bottom_y, width, height):
        current_page.append(f"q {width} 0 0 {height} {x} {bottom_y} cm /{name} Do Q")

    def draw_two_column_sections(sections):
        nonlocal y
        column_gap = 24
        column_width = (right - left - column_gap) / 2
        rows = [sections[index:index + 2] for index in range(0, len(sections), 2)]
        for row in rows:
            prepared = []
            row_height = 0
            for label, text in row:
                wrapped = wrap_pdf_lines(text, width=34) or [""]
                block_height = 20 + (len(wrapped) * 12) + 6
                prepared.append((label, wrapped, block_height))
                row_height = max(row_height, block_height)
            ensure_space(row_height + 6)
            row_top = y
            for column_index, (label, wrapped, _block_height) in enumerate(prepared):
                column_x = left + column_index * (column_width + column_gap)
                draw_text(column_x, row_top, label, font="F2", size=12)
                line_y = row_top - 16
                for line in wrapped:
                    draw_text(column_x, line_y, line, size=11)
                    line_y -= 12
            y -= row_height + 6

    def draw_page_header(compact=False):
        nonlocal y
        title_size = 18 if not compact else 15
        subtitle_size = 10 if not compact else 9
        logo_width = 150 if not compact else 124
        logo_height = logo_width * (logo_image["height"] / logo_image["width"])
        draw_image("ImLogo", left, y - logo_height + 2, logo_width, logo_height)
        title_y = y - logo_height - 16
        subtitle_y = title_y - 16
        draw_text(left, title_y, "RECHNUNG", font="F2", size=title_size, gray=0.05)
        draw_text(left, subtitle_y, invoice_form_data["title"], size=subtitle_size, gray=0.12)
        draw_text(405, y, invoice_number, font="F2", size=12, gray=0.05)
        draw_text(405, y - 18, f"Datum  {invoice_form_data['invoice_date'] or date.today().isoformat()}", size=10, gray=0.15)
        draw_text(405, y - 32, f"Auftrag  {order['order_number']}", size=10, gray=0.15)
        draw_text(405, y - 46, f"Status  {dict(INVOICE_PAYMENT_OPTIONS).get(invoice_form_data['payment_status'], invoice_form_data['payment_status'])}", size=10, gray=0.15)
        divider_y = subtitle_y - 14
        draw_line(left, divider_y, right, divider_y)
        y = divider_y - 18

    draw_page_header()

    draw_text(left, y, "Kunde", font="F2", size=11)
    for idx, line in enumerate(customer_lines, start=1):
        draw_text(left, y - (idx * 14), line, size=11)

    meta_x = 305
    draw_rect(meta_x - 12, y - 82, 254, 94, fill_gray=0.96)
    draw_text(meta_x, y, "Gerät", font="F2", size=11)
    draw_text(meta_x, y - 18, f"{order['manufacturer']} {order['model']}", size=11)
    draw_text(meta_x, y - 36, f"Kategorie  {dict(CATEGORIES).get(order['category'], order['category'])}", size=10)
    draw_text(meta_x, y - 50, f"Seriennummer  {order['serial_number'] or '-'}", size=10)
    draw_text(meta_x, y - 64, f"Kontaktweg  {order['customer_preferred_contact_label']}", size=10)
    y -= 104

    draw_line(left, y, right, y, gray=0.88)
    y -= 18
    detail_sections = [("Leistung", invoice_form_data["labor_description"])]
    if invoice_form_data["parts_description"]:
        detail_sections.append(("Teile / Zusatzkosten", invoice_form_data["parts_description"]))
    draw_two_column_sections(detail_sections)

    ensure_space(150)
    draw_text(left, y, "Kostenübersicht", font="F2", size=12)
    y -= 14
    cost_box_height = 128
    draw_rect(left, y - cost_box_height + 10, right - left, cost_box_height, fill_gray=0.97)
    cost_rows = [
        ("Arbeitskosten", format_currency_cents(invoice_form_data["labor_cost_cents"])),
        ("Teilekosten", format_currency_cents(invoice_form_data["parts_cost_cents"])),
        ("Fremdleistung", format_currency_cents(invoice_form_data["external_cost_cents"])),
        ("Versand / Sonstiges", format_currency_cents(invoice_form_data["shipping_cost_cents"])),
    ]
    row_y = y - 14
    for label, value in cost_rows:
        draw_text(left + 14, row_y, label, size=11)
        draw_text(430, row_y, value, font="F2", size=11)
        row_y -= 18
    total_line_y = row_y
    draw_line(left + 14, total_line_y, right - 14, total_line_y, gray=0.80)
    draw_text(left + 14, total_line_y - 22, "Gesamt", font="F2", size=12)
    draw_text(430, total_line_y - 22, format_currency_cents(total_cost_cents), font="F2", size=12)
    y = y - cost_box_height - 10

    ensure_space(92)
    draw_rect(left, y - 66, right - left, 76, fill_gray=0.95)
    draw_text(left + 14, y - 14, "Zahlungsstatus", font="F2", size=11)
    draw_text(left + 14, y - 36, dict(INVOICE_PAYMENT_OPTIONS).get(invoice_form_data["payment_status"], invoice_form_data["payment_status"]), size=11)
    draw_text(300, y - 30, "Danke für Ihren Auftrag", size=10, gray=0.16)
    draw_text(300, y - 44, "und viele Grüße aus der Werkstatt.", size=10, gray=0.16)
    y -= 88

    ensure_space(58)
    draw_line(left, y, right, y, gray=0.86)
    draw_text(left, y - 20, "Rückfragen", font="F2", size=10)
    draw_text(left, y - 36, "Melden Sie sich gern mit Ihrer Bearbeitungsnummer bei uns.", size=10)
    draw_text(395, y - 20, f"Bearbeitungsnummer  {order['order_number']}", font="F2", size=10)

    return build_pdf_document(page_commands, page_height=page_height, image_objects={"ImLogo": load_logo_pdf_image()})


def build_simple_document_pdf(lines):
    page_height = 842
    max_lines = 48
    chunks = [lines[index:index + max_lines] for index in range(0, len(lines), max_lines)] or [[]]
    page_commands = []
    for chunk in chunks:
        commands = []
        y = 790
        for idx, line in enumerate(chunk):
            font = "F2" if idx in (0, 1) or line.endswith(":") or line.startswith("Gesamt") else "F1"
            size = 12 if idx == 0 else 11
            safe = pdf_escape(line)
            commands.append(f"BT 0.08 g /{font} {size} Tf 1 0 0 1 48 {y} Tm ({safe}) Tj ET")
            y -= 15
        page_commands.append(commands)
    return build_pdf_document(page_commands, page_height=page_height, image_objects=None)


def build_pdf_document(page_commands, page_height=842, image_objects=None):
    """Serialize low-level PDF drawing commands into a minimal valid document.

    BenchFlow only needs a narrow subset of PDF features: text, lines, boxes
    and optional embedded images. Keeping that builder local avoids an extra
    rendering dependency and makes output reproducible in the offline MVP.
    """
    objects = [None, None]
    regular_font_obj = len(objects) + 1
    objects.append("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    bold_font_obj = len(objects) + 1
    objects.append("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")
    image_refs = {}
    for image_name, image_payload in (image_objects or {}).items():
        image_obj = len(objects) + 1
        image_refs[image_name] = image_obj
        objects.append(
            f"<< /Type /XObject /Subtype /Image /Width {image_payload['width']} /Height {image_payload['height']} "
            f"/ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /FlateDecode /Length {len(image_payload['data'])} >>\n"
            f"stream\n{image_payload['data'].decode('latin-1')}\nendstream"
        )
    page_refs = []

    for commands in page_commands:
        stream = "\n".join(commands)
        content_obj = len(objects) + 1
        objects.append(f"<< /Length {len(stream.encode('latin-1', 'replace'))} >>\nstream\n{stream}\nendstream")
        page_obj = len(objects) + 1
        page_refs.append(page_obj)
        xobject_part = ""
        if image_refs:
            xobject_part = " /XObject << " + " ".join(f"/{name} {ref} 0 R" for name, ref in image_refs.items()) + " >>"
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 {page_height}] "
            f"/Resources << /Font << /F1 {regular_font_obj} 0 R /F2 {bold_font_obj} 0 R >>{xobject_part} >> "
            f"/Contents {content_obj} 0 R >>"
        )

    objects[1] = f"<< /Type /Pages /Kids [{' '.join(f'{page_ref} 0 R' for page_ref in page_refs)}] /Count {len(page_refs)} >>"
    objects[0] = "<< /Type /Catalog /Pages 2 0 R >>"

    output = ["%PDF-1.4\n"]
    offsets = []
    current = len(output[0].encode("latin-1"))
    for index, obj in enumerate(objects, start=1):
        offsets.append(current)
        chunk = f"{index} 0 obj\n{obj}\nendobj\n"
        output.append(chunk)
        current += len(chunk.encode("latin-1", "replace"))

    xref_position = current
    xref_lines = ["xref", f"0 {len(objects) + 1}", "0000000000 65535 f "]
    xref_lines.extend(f"{offset:010d} 00000 n " for offset in offsets)
    trailer = f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_position}\n%%EOF"
    output.append("\n".join(xref_lines) + "\n" + trailer)
    return "".join(output).encode("latin-1", "replace")


@lru_cache(maxsize=1)
def load_logo_pdf_image():
    image_path = Path(__file__).with_name("static") / "Benchflow_Logo.png"
    image = Image.open(image_path).convert("RGBA")
    alpha = image.getchannel("A")
    bbox = alpha.getbbox()
    if bbox:
        image = image.crop(bbox)
        alpha = image.getchannel("A")
    background = Image.new("RGB", image.size, "white")
    background.paste(image, mask=alpha)
    max_width = 900
    if background.width > max_width:
        ratio = max_width / background.width
        background = background.resize((int(background.width * ratio), int(background.height * ratio)), Image.LANCZOS)
    return {
        "width": background.width,
        "height": background.height,
        "data": zlib.compress(background.tobytes()),
    }


def build_internal_qr_payload(order):
    return "\n".join(
        [
            f"Bearbeitungsnummer: {order['order_number']}",
            f"Kunde: {order['customer_name']}",
            f"Gerät: {order['manufacturer']} {order['model']}",
            f"Seriennummer: {order['serial_number'] or '-'}",
            f"Status: {order['status']}",
            f"Annahme: {order['intake_date']}",
        ]
    )


def build_internal_qr_svg_data(payload):
    qr_image = qrcode.make(payload, image_factory=SvgPathImage, border=2, box_size=6)
    buffer = BytesIO()
    qr_image.save(buffer)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def add_order_media_entries(db, order_id, media_items):
    for item in media_items:
        db.execute(
            """
            INSERT INTO service_order_media (service_order_id, filename, mime_type, document_type, order_context, media_data)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                order_id,
                item["filename"],
                item["mime_type"],
                item.get("document_type", ""),
                item.get("order_context", ""),
                item["media_data"],
            ),
        )


def sync_order_primary_image(db, order_id, device_id):
    first_media = db.execute(
        """
        SELECT media_data
        FROM service_order_media
        WHERE service_order_id = ?
          AND mime_type LIKE 'image/%'
        ORDER BY datetime(created_at) ASC, id ASC
        LIMIT 1
        """,
        (order_id,),
    ).fetchone()
    db.execute(
        """
        UPDATE devices
        SET image_data = ?
        WHERE id = ?
        """,
        (first_media["media_data"] if first_media else "", device_id),
    )
