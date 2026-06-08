import tempfile
import unittest
from contextlib import contextmanager
from io import BytesIO
import os
from pathlib import Path

from app import create_app
from app.db import close_db, get_db, init_db


class BenchFlowFlowsTestCase(unittest.TestCase):
    @contextmanager
    def app_db_context(self):
        with self.app.app_context():
            try:
                yield
            finally:
                close_db()

    def setUp(self):
        fd, db_path = tempfile.mkstemp(suffix=".sqlite")
        os.close(fd)
        Path(db_path).unlink(missing_ok=True)
        self.addCleanup(lambda: Path(db_path).unlink(missing_ok=True))

        self.app = create_app()
        self.app.config.update(TESTING=True, DATABASE=db_path)
        with self.app_db_context():
            init_db()
        self.client = self.app.test_client()

    def tearDown(self):
        context_stack = getattr(self.client, "_context_stack", None)
        if context_stack is not None:
            context_stack.close()

    def get(self, *args, **kwargs):
        response = self.client.get(*args, **kwargs)
        self.addCleanup(response.close)
        return response

    def post(self, *args, **kwargs):
        response = self.client.post(*args, **kwargs)
        self.addCleanup(response.close)
        return response

    def create_order(self, extra_files=None):
        payload = {
            "customer_name": "Demo Kundin Blau",
            "customer_phone": "+49 171 5550000",
            "customer_email": "kundin.blau@benchflow.invalid",
            "category": "amp",
            "manufacturer": "Mesa",
            "model": "Boogie",
            "serial_number": "MB-123",
            "accessories": "Netzkabel",
            "condition_notes": "gebraucht",
            "issue_description": "Aussetzer im Betrieb",
            "technician": "Bank 1",
            "intake_date": "2026-03-29",
            "warranty_status": "nein",
            "quote_required": "ja",
            "diagnostic_source": "Werkbank",
            "document_type": "",
            "document_context": "",
            "internal_notes": "Externer KVA erwartet.",
        }
        if extra_files:
            payload["order_files"] = extra_files
        return self.post(
            "/orders",
            data=payload,
            content_type="multipart/form-data",
            follow_redirects=False,
        )

    def test_create_order_redirects_to_detail_page(self):
        response = self.create_order()

        self.assertEqual(response.status_code, 302)
        self.assertRegex(response.headers["Location"], r"/orders/\d+$")

    def test_extended_customer_details_are_saved_and_rendered(self):
        response = self.post(
            "/orders",
            data={
                "customer_name": "Demo Kundin Blau",
                "company_name": "Atelier Nord Demo",
                "customer_phone": "+49 171 5550000",
                "customer_email": "kundin.blau@benchflow.invalid",
                "street": "Musterweg 12",
                "postal_code": "40549",
                "city": "Teststadt",
                "preferred_contact": "email",
                "customer_notes": "Bitte Demo-Freigaben zuerst per Mail bestaetigen.",
                "category": "amp",
                "manufacturer": "Mesa",
                "model": "Boogie",
                "serial_number": "MB-123",
                "accessories": "Netzkabel",
                "condition_notes": "gebraucht",
                "issue_description": "Aussetzer im Betrieb",
                "technician": "Bank 1",
                "intake_date": "2026-03-29",
                "warranty_status": "nein",
                "quote_required": "ja",
                "diagnostic_source": "Werkbank",
                "document_type": "",
                "document_context": "",
                "internal_notes": "Externer KVA erwartet.",
            },
            follow_redirects=False,
        )

        order_id = int(response.headers["Location"].rsplit("/", 1)[-1])
        detail = self.get(f"/orders/{order_id}").get_data(as_text=True)
        print_view = self.get(f"/orders/{order_id}/print").get_data(as_text=True)

        self.assertIn("Atelier Nord Demo", detail)
        self.assertIn("Musterweg 12", detail)
        self.assertIn("40549", detail)
        self.assertIn("Teststadt", detail)
        self.assertIn("Bitte Demo-Freigaben zuerst per Mail bestaetigen.", detail)
        self.assertIn("Atelier Nord Demo", print_view)
        self.assertIn("Musterweg 12", print_view)

    def test_new_order_page_renders_customer_lookup_with_existing_customers(self):
        self.post(
            "/orders",
            data={
                "customer_name": "Demo Kundin Blau",
                "company_name": "Atelier Nord Demo",
                "customer_phone": "+49 171 5550000",
                "customer_email": "kundin.blau@benchflow.invalid",
                "street": "Musterweg 12",
                "postal_code": "40549",
                "city": "Teststadt",
                "preferred_contact": "email",
                "customer_notes": "Bitte Demo-Freigaben zuerst per Mail bestaetigen.",
                "category": "amp",
                "manufacturer": "Mesa",
                "model": "Boogie",
                "serial_number": "MB-123",
                "accessories": "Netzkabel",
                "condition_notes": "gebraucht",
                "issue_description": "Aussetzer im Betrieb",
                "technician": "Bank 1",
                "intake_date": "2026-03-29",
                "warranty_status": "nein",
                "quote_required": "ja",
                "diagnostic_source": "Werkbank",
                "document_type": "",
                "document_context": "",
                "internal_notes": "Externer KVA erwartet.",
            },
            follow_redirects=False,
        )

        new_order_page = self.get("/orders/new").get_data(as_text=True)
        self.assertIn("Bestehenden Kunden suchen", new_order_page)
        self.assertIn("Demo Kundin Blau | Atelier Nord Demo | +49 171 5550000", new_order_page)

    def test_customer_list_page_shows_existing_customer_with_active_orders(self):
        self.post(
            "/orders",
            data={
                "customer_name": "Demo Kundin Blau",
                "company_name": "Atelier Nord Demo",
                "customer_phone": "+49 171 5550000",
                "customer_email": "kundin.blau@benchflow.invalid",
                "street": "Musterweg 12",
                "postal_code": "40549",
                "city": "Teststadt",
                "preferred_contact": "email",
                "customer_notes": "Bitte Demo-Freigaben zuerst per Mail bestaetigen.",
                "category": "amp",
                "manufacturer": "Mesa",
                "model": "Boogie",
                "serial_number": "MB-123",
                "accessories": "Netzkabel",
                "condition_notes": "gebraucht",
                "issue_description": "Aussetzer im Betrieb",
                "technician": "Bank 1",
                "intake_date": "2026-03-29",
                "warranty_status": "nein",
                "quote_required": "ja",
                "diagnostic_source": "Werkbank",
                "document_type": "",
                "document_context": "",
                "internal_notes": "Externer KVA erwartet.",
            },
            follow_redirects=False,
        )

        customer_list_page = self.get("/customers").get_data(as_text=True)

        self.assertIn("Kundenliste", customer_list_page)
        self.assertIn("Atelier Nord Demo", customer_list_page)
        self.assertIn("1 offen", customer_list_page)
        self.assertIn("/customers/", customer_list_page)

    def test_customer_list_page_can_filter_for_archived_only_customer_via_all_scope(self):
        response = self.post(
            "/orders",
            data={
                "customer_name": "Archiv Kunde",
                "company_name": "",
                "customer_phone": "+49 171 5550001",
                "customer_email": "archiv@benchflow.invalid",
                "street": "Beispielpfad 3",
                "postal_code": "40210",
                "city": "Musterstadt",
                "preferred_contact": "telefon",
                "customer_notes": "",
                "category": "amp",
                "manufacturer": "Mesa",
                "model": "Studio",
                "serial_number": "ST-1",
                "accessories": "",
                "condition_notes": "",
                "issue_description": "Brummen",
                "technician": "Bank 1",
                "intake_date": "2026-03-29",
                "warranty_status": "nein",
                "quote_required": "nein",
                "diagnostic_source": "Werkbank",
                "document_type": "",
                "document_context": "",
                "internal_notes": "",
            },
            follow_redirects=False,
        )

        order_id = int(response.headers["Location"].rsplit("/", 1)[-1])
        self.post(f"/orders/{order_id}/archive", data={}, follow_redirects=False)

        active_scope_page = self.get("/customers").get_data(as_text=True)
        all_scope_page = self.get("/customers?scope=all&q=Archiv").get_data(as_text=True)

        self.assertNotIn("Archiv Kunde", active_scope_page)
        self.assertIn("Archiv Kunde", all_scope_page)
        self.assertIn("0 offen", all_scope_page)

    def test_customer_detail_page_shows_customer_data_and_orders(self):
        response = self.post(
            "/orders",
            data={
                "customer_name": "Demo Kundin Blau",
                "company_name": "Atelier Nord Demo",
                "customer_phone": "+49 171 5550000",
                "customer_email": "kundin.blau@benchflow.invalid",
                "street": "Musterweg 12",
                "postal_code": "40549",
                "city": "Teststadt",
                "preferred_contact": "email",
                "customer_notes": "Bitte Demo-Freigaben zuerst per Mail bestaetigen.",
                "category": "amp",
                "manufacturer": "Mesa",
                "model": "Boogie",
                "serial_number": "MB-123",
                "accessories": "Netzkabel",
                "condition_notes": "gebraucht",
                "issue_description": "Aussetzer im Betrieb",
                "technician": "Bank 1",
                "intake_date": "2026-03-29",
                "warranty_status": "nein",
                "quote_required": "ja",
                "diagnostic_source": "Werkbank",
                "document_type": "",
                "document_context": "",
                "internal_notes": "Externer KVA erwartet.",
            },
            follow_redirects=False,
        )

        order_id = int(response.headers["Location"].rsplit("/", 1)[-1])
        detail_page = self.get(f"/orders/{order_id}").get_data(as_text=True)
        self.assertIn("/customers/", detail_page)

        with self.app_db_context():
            db = get_db()
            customer_id = db.execute(
                "SELECT customer_id FROM service_orders WHERE id = ?",
                (order_id,),
            ).fetchone()["customer_id"]

        customer_page = self.get(f"/customers/{customer_id}")
        body = customer_page.get_data(as_text=True)

        self.assertEqual(customer_page.status_code, 200)
        self.assertIn("Atelier Nord Demo", body)
        self.assertIn("Musterweg 12", body)
        self.assertIn("Bitte Demo-Freigaben zuerst per Mail bestaetigen.", body)
        self.assertIn(f"/orders/{order_id}", body)

    def test_quote_workflow_creates_pdf_and_sets_waiting_status(self):
        create_response = self.create_order()
        order_id = int(create_response.headers["Location"].rsplit("/", 1)[-1])

        quote_response = self.post(
            f"/orders/{order_id}/quote",
            data={
                "quote_title": "KVA Endstufentausch",
                "quote_work_description": "Fehleranalyse, Ausbau der defekten Endstufe und Funktionstest.",
                "quote_parts_description": "Endstufenmodul inkl. Beschaffung.",
                "quote_labor_cost": "89,00",
                "quote_parts_cost": "129,00",
                "quote_external_cost": "0,00",
                "quote_shipping_cost": "7,90",
                "quote_valid_until": "2026-04-12",
                "quote_customer_message": "Bitte kurze Freigabe per Mail oder Telefon.",
                "quote_approval_status": "offen",
            },
            follow_redirects=False,
        )

        self.assertEqual(quote_response.status_code, 302)
        with self.app_db_context():
            db = get_db()
            quote = db.execute(
                """
                SELECT quote_number, total_cost_cents, approval_status, pdf_media_id
                FROM service_order_quotes
                WHERE service_order_id = ?
                """,
                (order_id,),
            ).fetchone()
            order = db.execute(
                "SELECT status, quote_required FROM service_orders WHERE id = ?",
                (order_id,),
            ).fetchone()
            media = db.execute(
                "SELECT filename, document_type, mime_type FROM service_order_media WHERE id = ?",
                (quote["pdf_media_id"],),
            ).fetchone()

        self.assertEqual(order["status"], "Wartet auf Freigabe")
        self.assertEqual(order["quote_required"], "ja")
        self.assertEqual(quote["approval_status"], "offen")
        self.assertEqual(quote["total_cost_cents"], 22590)
        self.assertTrue(quote["quote_number"].startswith("KVA-"))
        self.assertEqual(media["document_type"], "kva")
        self.assertEqual(media["mime_type"], "application/pdf")
        self.assertTrue(media["filename"].endswith("kostenvoranschlag.pdf"))

    def test_quote_can_be_marked_as_approved_and_renders_in_detail(self):
        create_response = self.create_order()
        order_id = int(create_response.headers["Location"].rsplit("/", 1)[-1])

        self.post(
            f"/orders/{order_id}/quote",
            data={
                "quote_title": "KVA Netzteilreparatur",
                "quote_work_description": "Netzteil instandsetzen und Lasttest durchfuehren.",
                "quote_parts_description": "Kondensatorensatz und Sicherung.",
                "quote_labor_cost": "95,00",
                "quote_parts_cost": "38,00",
                "quote_external_cost": "0,00",
                "quote_shipping_cost": "0,00",
                "quote_valid_until": "2026-04-15",
                "quote_customer_message": "",
                "quote_approval_status": "freigegeben",
            },
            follow_redirects=False,
        )

        with self.app_db_context():
            db = get_db()
            order = db.execute(
                "SELECT status FROM service_orders WHERE id = ?",
                (order_id,),
            ).fetchone()
            history = db.execute(
                """
                SELECT COUNT(*) AS total
                FROM service_order_status_history
                WHERE service_order_id = ? AND status = 'Freigegeben'
                """,
                (order_id,),
            ).fetchone()

        detail = self.get(f"/orders/{order_id}").get_data(as_text=True)
        self.assertEqual(order["status"], "Freigegeben")
        self.assertGreaterEqual(history["total"], 1)
        self.assertIn("KVA-PDF ansehen", detail)
        self.assertIn("133,00 EUR", detail)

    def test_invoice_workflow_creates_pdf_and_marks_order_ready(self):
        create_response = self.create_order()
        order_id = int(create_response.headers["Location"].rsplit("/", 1)[-1])

        invoice_response = self.post(
            f"/orders/{order_id}/invoice",
            data={
                "invoice_title": "Rechnung Endstufentausch",
                "invoice_labor_description": "Endstufe ausgetauscht und Funktionstest durchgefuehrt.",
                "invoice_parts_description": "Endstufenmodul",
                "invoice_labor_cost": "120,00",
                "invoice_parts_cost": "349,00",
                "invoice_external_cost": "0,00",
                "invoice_shipping_cost": "15,00",
                "invoice_date": "2026-03-29",
                "invoice_payment_status": "offen",
                "invoice_internal_note": "Zahlung bei Abholung.",
            },
            follow_redirects=False,
        )

        self.assertEqual(invoice_response.status_code, 302)
        with self.app_db_context():
            db = get_db()
            invoice = db.execute(
                """
                SELECT invoice_number, total_cost_cents, payment_status, pdf_media_id
                FROM service_order_invoices
                WHERE service_order_id = ?
                """,
                (order_id,),
            ).fetchone()
            order = db.execute("SELECT status FROM service_orders WHERE id = ?", (order_id,)).fetchone()
            media = db.execute(
                "SELECT document_type, mime_type FROM service_order_media WHERE id = ?",
                (invoice["pdf_media_id"],),
            ).fetchone()

        self.assertEqual(order["status"], "Abholbereit")
        self.assertTrue(invoice["invoice_number"].startswith("RE-"))
        self.assertEqual(invoice["total_cost_cents"], 48400)
        self.assertEqual(invoice["payment_status"], "offen")
        self.assertEqual(media["document_type"], "rechnung")
        self.assertEqual(media["mime_type"], "application/pdf")

    def test_approved_quote_can_generate_invoice_directly(self):
        create_response = self.create_order()
        order_id = int(create_response.headers["Location"].rsplit("/", 1)[-1])

        self.post(
            f"/orders/{order_id}/quote",
            data={
                "quote_title": "Kostenvoranschlag Netzteilservice",
                "quote_work_description": "Netzteil instandsetzen und Lasttest durchfuehren.",
                "quote_parts_description": "Kondensatorensatz und Sicherung.",
                "quote_labor_cost": "95,00",
                "quote_parts_cost": "38,00",
                "quote_external_cost": "5,00",
                "quote_shipping_cost": "0,00",
                "quote_valid_until": "2026-04-15",
                "quote_customer_message": "",
                "quote_approval_status": "freigegeben",
            },
            follow_redirects=False,
        )

        invoice_response = self.post(
            f"/orders/{order_id}/invoice/from-quote",
            data={},
            follow_redirects=False,
        )

        self.assertEqual(invoice_response.status_code, 302)
        self.assertTrue(invoice_response.headers["Location"].endswith("#invoice-workflow"))

        with self.app_db_context():
            db = get_db()
            invoice = db.execute(
                """
                SELECT title, labor_description, parts_description, labor_cost_cents, parts_cost_cents,
                       external_cost_cents, shipping_cost_cents, total_cost_cents, payment_status
                FROM service_order_invoices
                WHERE service_order_id = ?
                """,
                (order_id,),
            ).fetchone()
            order = db.execute("SELECT status FROM service_orders WHERE id = ?", (order_id,)).fetchone()

        self.assertEqual(invoice["title"], "Rechnung Netzteilservice")
        self.assertEqual(invoice["labor_description"], "Netzteil instandsetzen und Lasttest durchfuehren.")
        self.assertEqual(invoice["parts_description"], "Kondensatorensatz und Sicherung.")
        self.assertEqual(invoice["labor_cost_cents"], 9500)
        self.assertEqual(invoice["parts_cost_cents"], 3800)
        self.assertEqual(invoice["external_cost_cents"], 500)
        self.assertEqual(invoice["shipping_cost_cents"], 0)
        self.assertEqual(invoice["total_cost_cents"], 13800)
        self.assertEqual(invoice["payment_status"], "offen")
        self.assertEqual(order["status"], "Abholbereit")

    def test_invoice_from_quote_requires_approved_quote(self):
        create_response = self.create_order()
        order_id = int(create_response.headers["Location"].rsplit("/", 1)[-1])

        self.post(
            f"/orders/{order_id}/quote",
            data={
                "quote_title": "KVA offen",
                "quote_work_description": "Fehleranalyse.",
                "quote_parts_description": "",
                "quote_labor_cost": "50,00",
                "quote_parts_cost": "0,00",
                "quote_external_cost": "0,00",
                "quote_shipping_cost": "0,00",
                "quote_valid_until": "2026-04-15",
                "quote_customer_message": "",
                "quote_approval_status": "offen",
            },
            follow_redirects=False,
        )

        response = self.post(
            f"/orders/{order_id}/invoice/from-quote",
            data={},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 302)
        with self.app_db_context():
            db = get_db()
            invoice = db.execute(
                "SELECT id FROM service_order_invoices WHERE service_order_id = ?",
                (order_id,),
            ).fetchone()

        self.assertIsNone(invoice)

    def test_paid_invoice_marks_order_completed(self):
        create_response = self.create_order()
        order_id = int(create_response.headers["Location"].rsplit("/", 1)[-1])

        self.post(
            f"/orders/{order_id}/invoice",
            data={
                "invoice_title": "Rechnung abgeschlossen",
                "invoice_labor_description": "Reparatur abgeschlossen.",
                "invoice_parts_description": "",
                "invoice_labor_cost": "90,00",
                "invoice_parts_cost": "0,00",
                "invoice_external_cost": "0,00",
                "invoice_shipping_cost": "0,00",
                "invoice_date": "2026-03-29",
                "invoice_payment_status": "bezahlt",
                "invoice_internal_note": "",
            },
            follow_redirects=False,
        )

        with self.app_db_context():
            db = get_db()
            order = db.execute("SELECT status FROM service_orders WHERE id = ?", (order_id,)).fetchone()
            history = db.execute(
                """
                SELECT COUNT(*) AS total
                FROM service_order_status_history
                WHERE service_order_id = ? AND status = 'Abgeschlossen'
                """,
                (order_id,),
            ).fetchone()

        detail = self.get(f"/orders/{order_id}").get_data(as_text=True)
        self.assertEqual(order["status"], "Abgeschlossen")
        self.assertGreaterEqual(history["total"], 1)
        self.assertIn("Rechnung-PDF ansehen", detail)

    def test_quote_email_preparation_redirects_to_mailto_and_logs_history(self):
        create_response = self.create_order()
        order_id = int(create_response.headers["Location"].rsplit("/", 1)[-1])

        self.post(
            f"/orders/{order_id}/quote",
            data={
                "quote_title": "KVA Endstufentausch",
                "quote_work_description": "Fehleranalyse und Endstufentausch.",
                "quote_parts_description": "Endstufenmodul",
                "quote_labor_cost": "89,00",
                "quote_parts_cost": "129,00",
                "quote_external_cost": "0,00",
                "quote_shipping_cost": "7,90",
                "quote_valid_until": "2026-04-12",
                "quote_customer_message": "Bitte kurze Freigabe per Mail oder Telefon.",
                "quote_approval_status": "offen",
            },
            follow_redirects=False,
        )

        response = self.get(f"/orders/{order_id}/quote/email", follow_redirects=False)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].startswith("mailto:kundin.blau%40benchflow.invalid"))
        self.assertIn("Ihr%20Kostenvoranschlag%20KVA-", response.headers["Location"])
        self.assertIn("Mesa%20Boogie", response.headers["Location"])

        with self.app_db_context():
            db = get_db()
            history = db.execute(
                """
                SELECT note
                FROM service_order_status_history
                WHERE service_order_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (order_id,),
            ).fetchone()

        self.assertIn("KVA-Mail an kundin.blau@benchflow.invalid vorbereitet.", history["note"])

    def test_update_order_changes_status_and_creates_history_entry(self):
        create_response = self.create_order()
        order_id = int(create_response.headers["Location"].rsplit("/", 1)[-1])

        update_response = self.post(
            f"/orders/{order_id}/update",
            data={
                "customer_name": "Demo Kundin Blau",
                "customer_phone": "+49 171 5550000",
                "customer_email": "kundin.blau@benchflow.invalid",
                "category": "amp",
                "manufacturer": "Mesa",
                "model": "Boogie Mk II",
                "serial_number": "MB-123",
                "accessories": "Netzkabel",
                "condition_notes": "gebraucht",
                "issue_description": "Aussetzer im Betrieb",
                "status": "In Reparatur",
                "technician": "Bank 1",
                "intake_date": "2026-03-29",
                "warranty_status": "nein",
                "quote_required": "ja",
                "diagnostic_source": "Werkbank",
                "internal_notes": "Signalweg wird geprueft.",
            },
            follow_redirects=False,
        )

        self.assertEqual(update_response.status_code, 302)
        with self.app_db_context():
            db = get_db()
            order = db.execute(
                "SELECT status FROM service_orders WHERE id = ?",
                (order_id,),
            ).fetchone()
            history_count = db.execute(
                """
                SELECT COUNT(*) AS total
                FROM service_order_status_history
                WHERE service_order_id = ? AND status = ?
                """,
                (order_id, "In Reparatur"),
            ).fetchone()["total"]

        self.assertEqual(order["status"], "In Reparatur")
        self.assertGreaterEqual(history_count, 1)

    def test_uploads_image_and_pdf_and_serves_pdf_attachment(self):
        response = self.create_order(
            extra_files=[
                (
                    BytesIO(
                        b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
                    ),
                    "kva.pdf",
                    "application/pdf",
                ),
                (BytesIO(b"fakepng"), "front.png", "image/png"),
            ]
        )
        order_id = int(response.headers["Location"].rsplit("/", 1)[-1])

        with self.app_db_context():
            db = get_db()
            media_items = db.execute(
                """
                SELECT id, filename, mime_type, document_type
                FROM service_order_media
                WHERE service_order_id = ?
                ORDER BY id ASC
                """,
                (order_id,),
            ).fetchall()

        self.assertEqual(len(media_items), 2)
        pdf_row = next(item for item in media_items if item["mime_type"] == "application/pdf")
        attachment_response = self.get(f"/orders/{order_id}/attachments/{pdf_row['id']}")

        self.assertEqual(attachment_response.status_code, 200)
        self.assertEqual(attachment_response.mimetype, "application/pdf")
        self.assertEqual(pdf_row["document_type"], "")
        self.assertIn('inline; filename="kva.pdf"', attachment_response.headers["Content-Disposition"])
        self.assertTrue(attachment_response.data.startswith(b"%PDF-1.4"))

    def test_pdf_document_type_is_saved_and_rendered(self):
        response = self.post(
            "/orders",
            data={
                "customer_name": "Demo Kundin Blau",
                "customer_phone": "+49 171 5550000",
                "customer_email": "kundin.blau@benchflow.invalid",
                "category": "amp",
                "manufacturer": "Mesa",
                "model": "Boogie",
                "serial_number": "MB-123",
                "accessories": "Netzkabel",
                "condition_notes": "gebraucht",
                "issue_description": "Aussetzer im Betrieb",
                "technician": "Bank 1",
                "intake_date": "2026-03-29",
                "warranty_status": "nein",
                "quote_required": "ja",
                "diagnostic_source": "Werkbank",
                "document_type": "kva",
                "document_context": "KVA fuer Endstufentausch",
                "internal_notes": "Externer KVA erwartet.",
                "order_files": [
                    (
                        BytesIO(b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"),
                        "angebot.pdf",
                        "application/pdf",
                    ),
                ],
            },
            content_type="multipart/form-data",
            follow_redirects=False,
        )
        order_id = int(response.headers["Location"].rsplit("/", 1)[-1])

        with self.app_db_context():
            db = get_db()
            row = db.execute(
                "SELECT document_type, order_context FROM service_order_media WHERE service_order_id = ?",
                (order_id,),
            ).fetchone()

        self.assertEqual(row["document_type"], "kva")
        self.assertEqual(row["order_context"], "KVA fuer Endstufentausch")
        detail = self.get(f"/orders/{order_id}")
        self.assertIn("Kostenvoranschlag", detail.get_data(as_text=True))
        self.assertIn("KVA fuer Endstufentausch", detail.get_data(as_text=True))

    def test_existing_pdf_document_type_can_be_changed_on_detail_page(self):
        response = self.post(
            "/orders",
            data={
                "customer_name": "Demo Kundin Blau",
                "customer_phone": "+49 171 5550000",
                "customer_email": "kundin.blau@benchflow.invalid",
                "category": "amp",
                "manufacturer": "Mesa",
                "model": "Boogie",
                "serial_number": "MB-123",
                "accessories": "Netzkabel",
                "condition_notes": "gebraucht",
                "issue_description": "Aussetzer im Betrieb",
                "technician": "Bank 1",
                "intake_date": "2026-03-29",
                "warranty_status": "nein",
                "quote_required": "ja",
                "diagnostic_source": "Werkbank",
                "document_type": "kva",
                "document_context": "KVA fuer Endstufentausch",
                "internal_notes": "Externer KVA erwartet.",
                "order_files": [
                    (
                        BytesIO(b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"),
                        "angebot.pdf",
                        "application/pdf",
                    ),
                ],
            },
            content_type="multipart/form-data",
            follow_redirects=False,
        )
        order_id = int(response.headers["Location"].rsplit("/", 1)[-1])

        with self.app_db_context():
            db = get_db()
            media_id = db.execute(
                "SELECT id FROM service_order_media WHERE service_order_id = ?",
                (order_id,),
            ).fetchone()["id"]

        update_response = self.post(
            f"/orders/{order_id}/update",
            data={
                "customer_name": "Demo Kundin Blau",
                "customer_phone": "+49 171 5550000",
                "customer_email": "kundin.blau@benchflow.invalid",
                "category": "amp",
                "manufacturer": "Mesa",
                "model": "Boogie",
                "serial_number": "MB-123",
                "accessories": "Netzkabel",
                "condition_notes": "gebraucht",
                "issue_description": "Aussetzer im Betrieb",
                "status": "Angenommen",
                "technician": "Bank 1",
                "intake_date": "2026-03-29",
                "warranty_status": "nein",
                "quote_required": "ja",
                "diagnostic_source": "Werkbank",
                "document_type": "",
                "document_context": "",
                "internal_notes": "Externer KVA erwartet.",
                f"document_type_{media_id}": "rechnung",
                f"document_context_{media_id}": "Rechnung nach externer Reparatur",
            },
            follow_redirects=False,
        )

        self.assertEqual(update_response.status_code, 302)
        with self.app_db_context():
            db = get_db()
            row = db.execute(
                "SELECT document_type, order_context FROM service_order_media WHERE id = ?",
                (media_id,),
            ).fetchone()

        self.assertEqual(row["document_type"], "rechnung")
        self.assertEqual(row["order_context"], "Rechnung nach externer Reparatur")
        detail = self.get(f"/orders/{order_id}")
        self.assertIn("Rechnung", detail.get_data(as_text=True))
        self.assertIn("Rechnung nach externer Reparatur", detail.get_data(as_text=True))

    def test_orders_list_shows_document_hint_for_orders_with_pdfs(self):
        response = self.post(
            "/orders",
            data={
                "customer_name": "Demo Kundin Blau",
                "customer_phone": "+49 171 5550000",
                "customer_email": "kundin.blau@benchflow.invalid",
                "category": "amp",
                "manufacturer": "Mesa",
                "model": "Boogie",
                "serial_number": "MB-123",
                "accessories": "Netzkabel",
                "condition_notes": "gebraucht",
                "issue_description": "Aussetzer im Betrieb",
                "technician": "Bank 1",
                "intake_date": "2026-03-29",
                "warranty_status": "nein",
                "quote_required": "ja",
                "diagnostic_source": "Werkbank",
                "document_type": "kva",
                "document_context": "KVA fuer Endstufentausch",
                "internal_notes": "Externer KVA erwartet.",
                "order_files": [
                    (
                        BytesIO(b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"),
                        "angebot.pdf",
                        "application/pdf",
                    ),
                ],
            },
            content_type="multipart/form-data",
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 302)
        orders_page = self.get("/orders")
        body = orders_page.get_data(as_text=True)
        self.assertIn("1 Dokument", body)
        self.assertIn("Kostenvoranschlag", body)

    def test_orders_list_marks_mixed_document_types(self):
        response = self.post(
            "/orders",
            data={
                "customer_name": "Demo Kundin Blau",
                "customer_phone": "+49 171 5550000",
                "customer_email": "kundin.blau@benchflow.invalid",
                "category": "amp",
                "manufacturer": "Mesa",
                "model": "Boogie",
                "serial_number": "MB-123",
                "accessories": "Netzkabel",
                "condition_notes": "gebraucht",
                "issue_description": "Aussetzer im Betrieb",
                "technician": "Bank 1",
                "intake_date": "2026-03-29",
                "warranty_status": "nein",
                "quote_required": "ja",
                "diagnostic_source": "Werkbank",
                "document_type": "kva",
                "internal_notes": "Externer KVA erwartet.",
                "order_files": [
                    (
                        BytesIO(b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"),
                        "angebot.pdf",
                        "application/pdf",
                    ),
                ],
            },
            content_type="multipart/form-data",
            follow_redirects=False,
        )
        order_id = int(response.headers["Location"].rsplit("/", 1)[-1])

        with self.app_db_context():
            db = get_db()
            media_id = db.execute(
                "SELECT id FROM service_order_media WHERE service_order_id = ?",
                (order_id,),
            ).fetchone()["id"]

        self.post(
            f"/orders/{order_id}/update",
            data={
                "customer_name": "Demo Kundin Blau",
                "customer_phone": "+49 171 5550000",
                "customer_email": "kundin.blau@benchflow.invalid",
                "category": "amp",
                "manufacturer": "Mesa",
                "model": "Boogie",
                "serial_number": "MB-123",
                "accessories": "Netzkabel",
                "condition_notes": "gebraucht",
                "issue_description": "Aussetzer im Betrieb",
                "status": "Angenommen",
                "technician": "Bank 1",
                "intake_date": "2026-03-29",
                "warranty_status": "nein",
                "quote_required": "ja",
                "diagnostic_source": "Werkbank",
                "document_type": "rechnung",
                "document_context": "Rechnung Fremdwerkstatt",
                "internal_notes": "Externer KVA erwartet.",
                f"document_type_{media_id}": "kva",
                f"document_context_{media_id}": "KVA fuer Endstufentausch",
                "order_files": [
                    (
                        BytesIO(b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"),
                        "rechnung.pdf",
                        "application/pdf",
                    ),
                ],
            },
            content_type="multipart/form-data",
            follow_redirects=False,
        )

        body = self.get("/orders").get_data(as_text=True)
        self.assertIn("2 Dokumente", body)
        self.assertIn("gemischt", body)

    def test_archive_and_restore_flow_redirects_cleanly(self):
        create_response = self.create_order()
        order_id = int(create_response.headers["Location"].rsplit("/", 1)[-1])

        archive_response = self.post(
            f"/orders/{order_id}/archive",
            data={"next": "detail"},
            follow_redirects=False,
        )
        restore_response = self.post(
            f"/orders/{order_id}/restore",
            data={"next": "archive"},
            follow_redirects=False,
        )

        self.assertEqual(archive_response.status_code, 302)
        self.assertTrue(archive_response.headers["Location"].endswith(f"/orders/{order_id}"))
        self.assertEqual(restore_response.status_code, 302)
        self.assertTrue(restore_response.headers["Location"].endswith("/archive"))

    def test_orders_list_can_sort_by_intake_date_ascending_and_descending(self):
        self.post(
            "/orders",
            data={
                "customer_name": "Sort Kunde Alt",
                "customer_phone": "+49 171 5550100",
                "customer_email": "sort-alt@benchflow.invalid",
                "category": "amp",
                "manufacturer": "Mesa",
                "model": "Alpha",
                "serial_number": "SORT-OLD",
                "accessories": "",
                "condition_notes": "",
                "issue_description": "Amp rauscht alt",
                "technician": "Bank 1",
                "intake_date": "2026-03-01",
                "warranty_status": "nein",
                "quote_required": "nein",
                "diagnostic_source": "Werkbank",
                "document_type": "",
                "document_context": "",
                "internal_notes": "",
            },
            follow_redirects=False,
        )
        self.post(
            "/orders",
            data={
                "customer_name": "Sort Kunde Neu",
                "customer_phone": "+49 171 5550101",
                "customer_email": "sort-neu@benchflow.invalid",
                "category": "amp",
                "manufacturer": "Mesa",
                "model": "Omega",
                "serial_number": "SORT-NEW",
                "accessories": "",
                "condition_notes": "",
                "issue_description": "Amp rauscht neu",
                "technician": "Bank 1",
                "intake_date": "2026-03-30",
                "warranty_status": "nein",
                "quote_required": "nein",
                "diagnostic_source": "Werkbank",
                "document_type": "",
                "document_context": "",
                "internal_notes": "",
            },
            follow_redirects=False,
        )

        asc_body = self.get("/orders?q=Sort%20Kunde&sort_by=intake_date&sort_dir=asc").get_data(as_text=True)
        desc_body = self.get("/orders?q=Sort%20Kunde&sort_by=intake_date&sort_dir=desc").get_data(as_text=True)

        self.assertLess(asc_body.index("Sort Kunde Alt"), asc_body.index("Sort Kunde Neu"))
        self.assertLess(desc_body.index("Sort Kunde Neu"), desc_body.index("Sort Kunde Alt"))
        self.assertIn("sort_by=intake_date", asc_body)
        self.assertIn("ASC", asc_body)
        self.assertIn("sort_dir=desc", asc_body)

    def test_orders_list_can_sort_by_customer_name(self):
        self.post(
            "/orders",
            data={
                "customer_name": "Zulu Sort",
                "customer_phone": "+49 171 5550200",
                "customer_email": "zulu@benchflow.invalid",
                "category": "amp",
                "manufacturer": "Mesa",
                "model": "Zulu",
                "serial_number": "SORT-ZULU",
                "accessories": "",
                "condition_notes": "",
                "issue_description": "Amp rauscht zulu",
                "technician": "Bank 1",
                "intake_date": "2026-03-10",
                "warranty_status": "nein",
                "quote_required": "nein",
                "diagnostic_source": "Werkbank",
                "document_type": "",
                "document_context": "",
                "internal_notes": "",
            },
            follow_redirects=False,
        )
        self.post(
            "/orders",
            data={
                "customer_name": "Alpha Sort",
                "customer_phone": "+49 171 5550201",
                "customer_email": "alpha@benchflow.invalid",
                "category": "amp",
                "manufacturer": "Mesa",
                "model": "Alpha",
                "serial_number": "SORT-ALPHA",
                "accessories": "",
                "condition_notes": "",
                "issue_description": "Amp rauscht alpha",
                "technician": "Bank 1",
                "intake_date": "2026-03-11",
                "warranty_status": "nein",
                "quote_required": "nein",
                "diagnostic_source": "Werkbank",
                "document_type": "",
                "document_context": "",
                "internal_notes": "",
            },
            follow_redirects=False,
        )

        body = self.get("/orders?q=Sort&sort_by=customer&sort_dir=asc").get_data(as_text=True)

        self.assertLess(body.index("Alpha Sort"), body.index("Zulu Sort"))
        self.assertIn("sort_by=customer", body)
        self.assertIn("ASC", body)

    def test_customer_and_internal_print_views_are_available(self):
        response = self.create_order()
        order_id = int(response.headers["Location"].rsplit("/", 1)[-1])

        customer_print = self.get(f"/orders/{order_id}/print")
        internal_print = self.get(f"/orders/{order_id}/print/internal")

        self.assertEqual(customer_print.status_code, 200)
        self.assertEqual(internal_print.status_code, 200)
        self.assertIn("data:image/svg+xml;base64,", internal_print.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
