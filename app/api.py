from base64 import b64decode
from datetime import date
from urllib.parse import quote

from flask import Blueprint, Response, jsonify, request, url_for

from .db import add_status_history_entry, create_device, find_or_create_customer, get_db
from .routes import (
    CATEGORIES,
    DIAGNOSTIC_SOURCES,
    DOCUMENT_TYPES,
    INVOICE_PAYMENT_OPTIONS,
    ORDER_STATUSES,
    PREFERRED_CONTACT_OPTIONS,
    QUOTE_APPROVAL_OPTIONS,
    QUOTE_OPTIONS,
    TECHNICIANS,
    WARRANTY_OPTIONS,
    add_order_media_entries,
    annotate_invoice,
    annotate_media_item,
    annotate_quote,
    back_to_order_or_dashboard,
    build_customer_short_label,
    build_device_label_text,
    build_document_type_label,
    build_internal_qr_payload,
    build_internal_qr_svg_data,
    build_invoice_history_note,
    build_invoice_number,
    build_invoice_pdf,
    build_order_document_hint,
    build_order_status_from_quote_approval,
    build_preferred_contact_label,
    build_quote_approval_label,
    build_quote_history_note,
    build_quote_number,
    build_quote_pdf,
    compute_invoice_total_cents,
    compute_quote_total_cents,
    decode_media_data,
    encode_pdf_bytes,
    fetch_customer,
    fetch_customers,
    fetch_order,
    fetch_order_invoice,
    fetch_order_media,
    fetch_order_media_item,
    fetch_order_quote,
    fetch_orders,
    fetch_status_history,
    format_currency_cents,
    next_order_number,
    process_uploaded_order_media,
    split_media_items,
    sync_order_primary_image,
    validate_order_form,
)

bp = Blueprint("benchflow_api", __name__, url_prefix="/api")


def json_error(message, status_code=400, field_errors=None):
    payload = {"error": message}
    if field_errors:
        payload["field_errors"] = field_errors
    response = jsonify(payload)
    response.status_code = status_code
    return response


def stringify(value, default=""):
    if value is None:
        return default
    return str(value).strip()


def ensure_json_payload():
    payload = request.get_json(silent=True)
    if isinstance(payload, dict):
        return payload
    return None


def bool_query_arg(name):
    value = request.args.get(name, "").strip().lower()
    return value in {"1", "true", "yes", "ja", "on"}


def get_nested_mapping(payload, key):
    nested = payload.get(key, {})
    return nested if isinstance(nested, dict) else {}


def fetch_device(device_id):
    row = get_db().execute(
        """
        SELECT
            id,
            category,
            manufacturer,
            model,
            serial_number,
            accessories,
            condition_notes,
            image_data,
            created_at
        FROM devices
        WHERE id = ?
        """,
        (device_id,),
    ).fetchone()
    if row is None:
        return None
    return dict(row)


def serialize_option_pairs(option_pairs):
    return [{"value": value, "label": label} for value, label in option_pairs]


def serialize_customer(customer):
    if customer is None:
        return None
    return {
        "id": customer["id"],
        "name": customer["name"],
        "company_name": customer.get("company_name", ""),
        "email": customer.get("email", ""),
        "phone": customer.get("phone", ""),
        "street": customer.get("street", ""),
        "postal_code": customer.get("postal_code", ""),
        "city": customer.get("city", ""),
        "preferred_contact": customer.get("preferred_contact", ""),
        "customer_notes": customer.get("customer_notes", ""),
        "created_at": customer.get("created_at", ""),
        "preferred_contact_label": customer.get(
            "preferred_contact_label",
            build_preferred_contact_label(customer.get("preferred_contact", "")),
        ),
        "location_label": customer.get(
            "location_label",
            " ".join(
                part
                for part in [customer.get("postal_code", "").strip(), customer.get("city", "").strip()]
                if part
            ),
        ),
        "order_count": customer.get("order_count"),
        "active_order_count": customer.get("active_order_count"),
        "latest_order_number": customer.get("latest_order_number"),
        "latest_order_status": customer.get("latest_order_status"),
        "latest_order_updated_at": customer.get("latest_order_updated_at"),
    }


def serialize_device(device):
    if device is None:
        return None
    return {
        "id": device["id"],
        "category": device["category"],
        "manufacturer": device["manufacturer"],
        "model": device["model"],
        "serial_number": device["serial_number"],
        "accessories": device["accessories"],
        "condition_notes": device["condition_notes"],
        "image_data": device["image_data"],
        "created_at": device["created_at"],
    }


def serialize_attachment(order_id, item):
    attachment = {
        "id": item["id"],
        "service_order_id": order_id,
        "filename": item["filename"],
        "mime_type": item["mime_type"],
        "document_type": item.get("document_type", ""),
        "order_context": item.get("order_context", ""),
        "created_at": item.get("created_at", ""),
        "is_image": item["is_image"],
        "is_document": item["is_document"],
        "display_name": item["display_name"],
        "document_type_label": item["document_type_label"],
        "size_label": item["size_label"],
        "created_label": item["created_label"],
    }
    if item["id"] != "legacy-image":
        attachment["file_url"] = url_for(
            "benchflow.order_attachment",
            order_id=order_id,
            media_id=item["id"],
            _external=True,
        )
    else:
        attachment["file_url"] = None
    return attachment


def serialize_history_entry(order_id, row):
    return {
        "id": row["id"],
        "service_order_id": order_id,
        "status": row["status"],
        "note": row["note"],
        "changed_at": row["changed_at"],
    }


def serialize_quote(order_id, quote_data):
    if quote_data is None:
        return None
    payload = dict(quote_data)
    pdf_media_id = payload.get("pdf_media_id")
    payload["pdf_url"] = (
        url_for("benchflow.order_attachment", order_id=order_id, media_id=pdf_media_id, _external=True)
        if pdf_media_id
        else None
    )
    return payload


def serialize_invoice(order_id, invoice_data):
    if invoice_data is None:
        return None
    payload = dict(invoice_data)
    pdf_media_id = payload.get("pdf_media_id")
    payload["pdf_url"] = (
        url_for("benchflow.order_attachment", order_id=order_id, media_id=pdf_media_id, _external=True)
        if pdf_media_id
        else None
    )
    return payload


def serialize_order(order, include_related=False):
    customer = fetch_customer(order["customer_id"])
    device = fetch_device(order["device_id"])
    payload = {
        "id": order["id"],
        "order_number": order["order_number"],
        "customer_id": order["customer_id"],
        "device_id": order["device_id"],
        "issue_description": order["issue_description"],
        "status": order["status"],
        "technician": order["technician"],
        "intake_date": order["intake_date"],
        "warranty_status": order["warranty_status"],
        "quote_required": order["quote_required"],
        "diagnostic_source": order["diagnostic_source"],
        "internal_notes": order["internal_notes"],
        "archived_at": order.get("archived_at"),
        "created_at": order["created_at"],
        "updated_at": order.get("updated_at"),
        "document_count": order.get("document_count", 0) or 0,
        "document_type_count": order.get("document_type_count", 0) or 0,
        "primary_document_type": order.get("primary_document_type") or "",
        "document_hint": order.get("document_hint", ""),
        "customer": serialize_customer(customer),
        "device": serialize_device(device),
        "print_url": url_for("benchflow.order_print", order_id=order["id"], _external=True),
        "internal_print_url": url_for("benchflow.order_print_internal", order_id=order["id"], _external=True),
        "qr_url": url_for("benchflow_api.order_qr", order_id=order["id"], _external=True),
    }

    if include_related:
        media_items = fetch_order_media(order["id"], fallback_image=device["image_data"] if device else "")
        payload["attachments"] = [serialize_attachment(order["id"], item) for item in media_items]
        payload["quote"] = serialize_quote(order["id"], fetch_order_quote(order["id"], required=False))
        payload["invoice"] = serialize_invoice(order["id"], fetch_order_invoice(order["id"], required=False))
        payload["status_history"] = [
            serialize_history_entry(order["id"], row)
            for row in fetch_status_history(order["id"])
        ]

    return payload


def serialize_orders(orders, include_related=False):
    return [serialize_order(order, include_related=include_related) for order in orders]


def parse_order_payload(payload, include_status=False):
    customer = get_nested_mapping(payload, "customer")
    device = get_nested_mapping(payload, "device")
    form_data = {
        "customer_name": stringify(customer.get("name")),
        "customer_email": stringify(customer.get("email")),
        "customer_phone": stringify(customer.get("phone")),
        "company_name": stringify(customer.get("company_name")),
        "street": stringify(customer.get("street")),
        "postal_code": stringify(customer.get("postal_code")),
        "city": stringify(customer.get("city")),
        "preferred_contact": stringify(customer.get("preferred_contact"), "telefon") or "telefon",
        "customer_notes": stringify(customer.get("customer_notes")),
        "category": stringify(device.get("category")),
        "manufacturer": stringify(device.get("manufacturer")),
        "model": stringify(device.get("model")),
        "serial_number": stringify(device.get("serial_number")),
        "accessories": stringify(device.get("accessories")),
        "condition_notes": stringify(device.get("condition_notes")),
        "issue_description": stringify(payload.get("issue_description")),
        "technician": stringify(payload.get("technician")),
        "intake_date": stringify(payload.get("intake_date"), date.today().isoformat()) or date.today().isoformat(),
        "warranty_status": stringify(payload.get("warranty_status"), "unbekannt") or "unbekannt",
        "quote_required": stringify(payload.get("quote_required"), "nein") or "nein",
        "diagnostic_source": stringify(payload.get("diagnostic_source"), "Werkbank") or "Werkbank",
        "document_type": "",
        "document_context": "",
        "internal_notes": stringify(payload.get("internal_notes")),
        "image_data": "",
        "media_items": [],
    }
    if include_status:
        form_data["status"] = stringify(payload.get("status"))
    return form_data


def parse_non_negative_int(payload, key, label, errors):
    value = payload.get(key, 0)
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        errors.append(f"{label} muss eine ganze Zahl in Cent sein.")
        return 0
    if parsed < 0:
        errors.append(f"{label} darf nicht negativ sein.")
        return 0
    return parsed


def validate_iso_date(raw_value, label, errors):
    value = stringify(raw_value)
    if not value:
        return value
    try:
        date.fromisoformat(value)
    except ValueError:
        errors.append(f"{label} ist ungueltig.")
    return value


def parse_quote_payload(payload, default_title):
    errors = []
    quote_data = {
        "title": stringify(payload.get("title"), default_title) or default_title,
        "work_description": stringify(payload.get("work_description")),
        "parts_description": stringify(payload.get("parts_description")),
        "labor_cost_cents": parse_non_negative_int(payload, "labor_cost_cents", "Arbeitskosten", errors),
        "parts_cost_cents": parse_non_negative_int(payload, "parts_cost_cents", "Teilekosten", errors),
        "external_cost_cents": parse_non_negative_int(payload, "external_cost_cents", "Fremdleistung", errors),
        "shipping_cost_cents": parse_non_negative_int(payload, "shipping_cost_cents", "Versand", errors),
        "valid_until": validate_iso_date(payload.get("valid_until"), "Gueltig-bis-Datum", errors),
        "customer_message": stringify(payload.get("customer_message")),
        "approval_status": stringify(payload.get("approval_status"), "offen") or "offen",
    }
    if not quote_data["title"]:
        errors.append("Bitte einen Titel fuer den Kostenvoranschlag eintragen.")
    if len(quote_data["title"]) > 120:
        errors.append("Der KVA-Titel ist zu lang.")
    if not quote_data["work_description"]:
        errors.append("Bitte den Arbeitsumfang fuer den Kostenvoranschlag beschreiben.")
    if len(quote_data["work_description"]) > 1200:
        errors.append("Der Arbeitsumfang ist zu lang.")
    if len(quote_data["parts_description"]) > 1200:
        errors.append("Die Teilebeschreibung ist zu lang.")
    if len(quote_data["customer_message"]) > 600:
        errors.append("Die Kundennachricht ist zu lang.")
    if quote_data["approval_status"] not in {value for value, _label in QUOTE_APPROVAL_OPTIONS}:
        errors.append("Der Freigabestatus fuer den Kostenvoranschlag ist ungueltig.")
    return quote_data, errors


def parse_invoice_payload(payload, default_title):
    errors = []
    invoice_data = {
        "title": stringify(payload.get("title"), default_title) or default_title,
        "labor_description": stringify(payload.get("labor_description")),
        "parts_description": stringify(payload.get("parts_description")),
        "labor_cost_cents": parse_non_negative_int(payload, "labor_cost_cents", "Arbeitskosten", errors),
        "parts_cost_cents": parse_non_negative_int(payload, "parts_cost_cents", "Teilekosten", errors),
        "external_cost_cents": parse_non_negative_int(payload, "external_cost_cents", "Fremdleistung", errors),
        "shipping_cost_cents": parse_non_negative_int(payload, "shipping_cost_cents", "Versand", errors),
        "invoice_date": validate_iso_date(payload.get("invoice_date"), "Rechnungsdatum", errors),
        "payment_status": stringify(payload.get("payment_status"), "offen") or "offen",
        "internal_note": stringify(payload.get("internal_note")),
    }
    if not invoice_data["title"]:
        errors.append("Bitte einen Titel fuer die Rechnung eintragen.")
    if len(invoice_data["title"]) > 120:
        errors.append("Der Rechnungstitel ist zu lang.")
    if not invoice_data["labor_description"]:
        errors.append("Bitte die berechnete Leistung beschreiben.")
    if len(invoice_data["labor_description"]) > 1200:
        errors.append("Die Leistungsbeschreibung ist zu lang.")
    if len(invoice_data["parts_description"]) > 1200:
        errors.append("Die Teilebeschreibung der Rechnung ist zu lang.")
    if len(invoice_data["internal_note"]) > 600:
        errors.append("Die interne Rechnungsnotiz ist zu lang.")
    if invoice_data["payment_status"] not in {value for value, _label in INVOICE_PAYMENT_OPTIONS}:
        errors.append("Der Zahlungsstatus ist ungueltig.")
    return invoice_data, errors


@bp.get("/meta")
def meta():
    return jsonify(
        {
            "base_url": request.host_url.rstrip("/"),
            "technicians": TECHNICIANS,
            "statuses": ORDER_STATUSES,
            "categories": serialize_option_pairs(CATEGORIES),
            "warranty_options": serialize_option_pairs(WARRANTY_OPTIONS),
            "quote_options": serialize_option_pairs(QUOTE_OPTIONS),
            "diagnostic_sources": DIAGNOSTIC_SOURCES,
            "preferred_contact_options": serialize_option_pairs(PREFERRED_CONTACT_OPTIONS),
            "document_types": serialize_option_pairs(DOCUMENT_TYPES),
            "quote_approval_options": serialize_option_pairs(QUOTE_APPROVAL_OPTIONS),
            "invoice_payment_options": serialize_option_pairs(INVOICE_PAYMENT_OPTIONS),
        }
    )


@bp.get("/dashboard")
def dashboard():
    db = get_db()
    active_orders = fetch_orders(where_clause="WHERE so.archived_at IS NULL")
    ready_statuses = {"Fertig", "Abholbereit"}
    blocked_statuses = {"Wartet auf Freigabe", "Warten auf Teile"}
    status_summary = [
        {"status": row["status"], "total": row["total"]}
        for row in db.execute(
            """
            SELECT status, COUNT(*) AS total
            FROM service_orders
            WHERE archived_at IS NULL
            GROUP BY status
            ORDER BY total DESC, status ASC
            """
        ).fetchall()
    ]
    ready_count = sum(item["total"] for item in status_summary if item["status"] in ready_statuses)
    blocked_count = sum(item["total"] for item in status_summary if item["status"] in blocked_statuses)
    archived_count = db.execute(
        "SELECT COUNT(*) AS total FROM service_orders WHERE archived_at IS NOT NULL"
    ).fetchone()["total"]
    pending_quotes_count = db.execute(
        "SELECT COUNT(*) AS total FROM service_order_quotes WHERE approval_status = 'offen'"
    ).fetchone()["total"]
    unpaid_invoices_count = db.execute(
        "SELECT COUNT(*) AS total FROM service_order_invoices WHERE payment_status = 'offen'"
    ).fetchone()["total"]

    recent_rows = db.execute(
        """
        SELECT
            so.id,
            so.order_number,
            so.customer_id,
            so.device_id,
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
        WHERE so.archived_at IS NULL
        ORDER BY datetime(so.updated_at) DESC, so.id DESC
        LIMIT 5
        """
    ).fetchall()
    recent_orders = []
    for row in recent_rows:
        order = dict(row)
        order["document_hint"] = build_order_document_hint(order)
        recent_orders.append(serialize_order(order, include_related=False))

    return jsonify(
        {
            "active_order_count": len(active_orders),
            "pending_quotes_count": pending_quotes_count,
            "unpaid_invoices_count": unpaid_invoices_count,
            "ready_count": ready_count,
            "blocked_count": blocked_count,
            "archived_count": archived_count,
            "status_summary": status_summary,
            "recent_orders": recent_orders,
        }
    )


@bp.get("/orders")
def orders():
    archived = bool_query_arg("archived")
    filters = {
        "q": request.args.get("q", "").strip(),
        "status": request.args.get("status", "").strip(),
        "category": request.args.get("category", "").strip(),
        "document_type": request.args.get("document_type", "").strip(),
    }
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

    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
    orders_list = serialize_orders(fetch_orders(where_clause=where_clause, params=params))
    return jsonify(
        {
            "orders": orders_list,
            "order_count": len(orders_list),
            "archived": archived,
            "filters": filters,
        }
    )


@bp.get("/archive")
def archive():
    return orders()


@bp.get("/orders/<int:order_id>")
def order_detail(order_id):
    return jsonify(serialize_order(fetch_order(order_id), include_related=True))


@bp.post("/orders")
def create_order():
    payload = ensure_json_payload()
    if payload is None:
        return json_error("Der Auftrag muss als JSON gesendet werden.")

    form_data = parse_order_payload(payload)
    errors, field_errors = validate_order_form(form_data)
    if errors:
        return json_error("Auftrag konnte nicht angelegt werden.", 400, field_errors=field_errors)

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
            next_order_number(db),
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
    add_status_history_entry(db, order_id, "Angenommen", note="Auftrag neu angelegt.")
    db.commit()
    response = jsonify(serialize_order(fetch_order(order_id), include_related=True))
    response.status_code = 201
    return response


@bp.put("/orders/<int:order_id>")
@bp.patch("/orders/<int:order_id>")
def update_order(order_id):
    existing_order = fetch_order(order_id)
    payload = ensure_json_payload()
    if payload is None:
        return json_error("Der Auftrag muss als JSON gesendet werden.")

    form_data = parse_order_payload(payload, include_status=True)
    errors, field_errors = validate_order_form(form_data, require_status=True)
    if errors:
        return json_error("Auftrag konnte nicht aktualisiert werden.", 400, field_errors=field_errors)

    db = get_db()
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
            condition_notes = ?
        WHERE id = ?
        """,
        (
            form_data["category"],
            form_data["manufacturer"],
            form_data["model"],
            form_data["serial_number"],
            form_data["accessories"],
            form_data["condition_notes"],
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
    if form_data["status"] != existing_order["status"]:
        add_status_history_entry(
            db,
            order_id,
            form_data["status"],
            note=f"Statuswechsel von {existing_order['status']} zu {form_data['status']}.",
        )
    db.commit()
    return jsonify(serialize_order(fetch_order(order_id), include_related=True))


@bp.post("/orders/<int:order_id>/attachments")
def upload_order_attachments(order_id):
    order = fetch_order(order_id)
    media_items, media_error = process_uploaded_order_media()
    if media_error:
        return json_error(media_error)
    if not media_items:
        return json_error("Es wurden keine Dateien hochgeladen.")

    db = get_db()
    add_order_media_entries(db, order_id, media_items)
    sync_order_primary_image(db, order_id, order["device_id"])
    db.execute(
        "UPDATE service_orders SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (order_id,),
    )
    db.commit()

    current_media = fetch_order_media(order_id, fallback_image=fetch_order(order_id)["image_data"])
    return jsonify(
        {
            "attachments": [serialize_attachment(order_id, item) for item in current_media],
            "added_count": len(media_items),
        }
    )


@bp.delete("/orders/<int:order_id>/attachments/<int:media_id>")
def delete_order_attachment(order_id, media_id):
    order = fetch_order(order_id)
    fetch_order_media_item(order_id, media_id)
    db = get_db()
    db.execute(
        "DELETE FROM service_order_media WHERE service_order_id = ? AND id = ?",
        (order_id, media_id),
    )
    sync_order_primary_image(db, order_id, order["device_id"])
    db.execute(
        "UPDATE service_orders SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (order_id,),
    )
    db.commit()
    return jsonify({"deleted_media_id": media_id})


@bp.post("/orders/<int:order_id>/quote")
def save_quote(order_id):
    order = fetch_order(order_id)
    payload = ensure_json_payload()
    if payload is None:
        return json_error("Der Kostenvoranschlag muss als JSON gesendet werden.")

    existing_quote = fetch_order_quote(order_id, required=False)
    quote_data, errors = parse_quote_payload(payload, default_title=f"Kostenvoranschlag {order['order_number']}")
    if errors:
        return json_error("Kostenvoranschlag konnte nicht gespeichert werden.", 400, {"quote": "; ".join(errors)})

    db = get_db()
    quote_number = existing_quote["quote_number"] if existing_quote else build_quote_number(order)
    total_cost_cents = compute_quote_total_cents(quote_data)
    approval_status = quote_data["approval_status"]
    pdf_filename = f"{order['order_number'].lower()}-kostenvoranschlag.pdf"
    pdf_context = quote_data["title"] or "Kostenvoranschlag"
    pdf_bytes = build_quote_pdf(order, quote_data, quote_number, total_cost_cents)
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
                quote_data["title"],
                quote_data["work_description"],
                quote_data["parts_description"],
                quote_data["labor_cost_cents"],
                quote_data["parts_cost_cents"],
                quote_data["external_cost_cents"],
                quote_data["shipping_cost_cents"],
                total_cost_cents,
                quote_data["valid_until"],
                quote_data["customer_message"],
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
                quote_data["title"],
                quote_data["work_description"],
                quote_data["parts_description"],
                quote_data["labor_cost_cents"],
                quote_data["parts_cost_cents"],
                quote_data["external_cost_cents"],
                quote_data["shipping_cost_cents"],
                total_cost_cents,
                quote_data["valid_until"],
                quote_data["customer_message"],
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
    return jsonify(serialize_order(fetch_order(order_id), include_related=True))


@bp.post("/orders/<int:order_id>/invoice")
def save_invoice(order_id):
    order = fetch_order(order_id)
    payload = ensure_json_payload()
    if payload is None:
        return json_error("Die Rechnung muss als JSON gesendet werden.")

    existing_invoice = fetch_order_invoice(order_id, required=False)
    invoice_data, errors = parse_invoice_payload(payload, default_title=f"Rechnung {order['order_number']}")
    if errors:
        return json_error("Rechnung konnte nicht gespeichert werden.", 400, {"invoice": "; ".join(errors)})

    db = get_db()
    invoice_number = existing_invoice["invoice_number"] if existing_invoice else build_invoice_number(order)
    total_cost_cents = compute_invoice_total_cents(invoice_data)
    pdf_filename = f"{order['order_number'].lower()}-rechnung.pdf"
    pdf_context = invoice_data["title"] or "Rechnung"
    pdf_bytes = build_invoice_pdf(order, invoice_data, invoice_number, total_cost_cents)
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
                invoice_data["title"],
                invoice_data["labor_description"],
                invoice_data["parts_description"],
                invoice_data["labor_cost_cents"],
                invoice_data["parts_cost_cents"],
                invoice_data["external_cost_cents"],
                invoice_data["shipping_cost_cents"],
                total_cost_cents,
                invoice_data["invoice_date"],
                invoice_data["payment_status"],
                invoice_data["internal_note"],
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
                invoice_data["title"],
                invoice_data["labor_description"],
                invoice_data["parts_description"],
                invoice_data["labor_cost_cents"],
                invoice_data["parts_cost_cents"],
                invoice_data["external_cost_cents"],
                invoice_data["shipping_cost_cents"],
                total_cost_cents,
                invoice_data["invoice_date"],
                invoice_data["payment_status"],
                invoice_data["internal_note"],
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

    invoice_status = "Abgeschlossen" if invoice_data["payment_status"] == "bezahlt" else "Abholbereit"
    history_note = build_invoice_history_note(existing_invoice, invoice_data["payment_status"], total_cost_cents)
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
    return jsonify(serialize_order(fetch_order(order_id), include_related=True))


@bp.post("/orders/<int:order_id>/archive")
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
    add_status_history_entry(db, order_id, order["status"], note="Auftrag archiviert.")
    db.commit()
    return jsonify(serialize_order(fetch_order(order_id), include_related=True))


@bp.post("/orders/<int:order_id>/restore")
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
    add_status_history_entry(db, order_id, order["status"], note="Auftrag aus dem Archiv wiederhergestellt.")
    db.commit()
    return jsonify(serialize_order(fetch_order(order_id), include_related=True))


@bp.get("/orders/<int:order_id>/quote/email")
def prepare_quote_email(order_id):
    order = fetch_order(order_id)
    quote_data = fetch_order_quote(order_id, required=False)
    if quote_data is None or not quote_data.get("pdf_media_id"):
        return json_error("Es ist noch kein Kostenvoranschlag als PDF vorhanden.", 409)
    if not order.get("customer_email"):
        return json_error("Beim Kunden ist keine E-Mail-Adresse hinterlegt.", 409)

    db = get_db()
    add_status_history_entry(
        db,
        order_id,
        order["status"],
        note=f"KVA-Mail an {order['customer_email']} vorbereitet.",
    )
    db.commit()

    device_label = " ".join(
        part for part in [order.get("manufacturer", ""), order.get("model", "")] if part
    ).strip() or "Geraet"
    subject = f"Ihr Kostenvoranschlag {quote_data['quote_number']} zu Auftrag {order['order_number']}"
    body_lines = [
        f"Hallo {order['customer_name']},",
        "",
        "danke fuer Ihren Auftrag bei uns.",
        "",
        "anbei finden Sie den Kostenvoranschlag zu Ihrem Serviceauftrag.",
        f"Bearbeitungsnummer: {order['order_number']}",
        f"KVA-Nummer: {quote_data['quote_number']}",
        f"Geraet: {device_label}",
        f"Gesamtbetrag: {quote_data['total_cost_label']}",
    ]
    if quote_data.get("valid_until"):
        body_lines.append(f"Gueltig bis: {quote_data['valid_until']}")
    if quote_data.get("customer_message"):
        body_lines.extend(["", "Hinweis:", quote_data["customer_message"]])
    body_lines.extend(
        [
            "",
            "Wenn der Kostenvoranschlag fuer Sie passt, geben Sie uns einfach kurz Bescheid.",
            "Eine kurze Antwort per E-Mail oder ein kurzer Anruf reicht voellig aus.",
            "",
            "Viele Gruesse aus der Werkstatt",
            "Ihr BenchFlow Service Team",
        ]
    )
    mailto_url = f"mailto:{quote(order['customer_email'])}?subject={quote(subject)}&body={quote(chr(10).join(body_lines))}"
    return jsonify({"mailto_url": mailto_url})


@bp.get("/orders/<int:order_id>/qr")
def order_qr(order_id):
    order = fetch_order(order_id)
    image_data = build_internal_qr_svg_data(build_internal_qr_payload(order))
    _prefix, encoded = image_data.split(",", 1)
    return Response(b64decode(encoded), mimetype="image/svg+xml")


@bp.get("/customers")
def customers():
    filters = {
        "q": request.args.get("q", "").strip(),
        "scope": request.args.get("scope", "active").strip() or "active",
    }
    customer_rows = fetch_customers(filters=filters)
    return jsonify(
        {
            "customers": [serialize_customer(customer) for customer in customer_rows],
            "customer_count": len(customer_rows),
            "filters": filters,
        }
    )


@bp.get("/customers/<int:customer_id>")
def customer_detail(customer_id):
    customer = fetch_customer(customer_id)
    orders = fetch_orders(
        where_clause="WHERE so.customer_id = ?",
        params=[customer_id],
    )
    return jsonify(
        {
            "customer": serialize_customer(customer),
            "orders": serialize_orders(orders),
            "order_count": len(orders),
        }
    )
