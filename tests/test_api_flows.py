import os
import tempfile
import unittest
from contextlib import contextmanager
from io import BytesIO
from pathlib import Path

from app import create_app
from app.db import close_db, get_db, init_db


class BenchFlowAPIFlowsTestCase(unittest.TestCase):
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

    def patch(self, *args, **kwargs):
        response = self.client.patch(*args, **kwargs)
        self.addCleanup(response.close)
        return response

    def delete(self, *args, **kwargs):
        response = self.client.delete(*args, **kwargs)
        self.addCleanup(response.close)
        return response

    def create_order_payload(self):
        return {
            "customer": {
                "name": "Demo Kundin Blau",
                "company_name": "Atelier Nord Demo",
                "email": "kundin.blau@benchflow.invalid",
                "phone": "+49 171 5550000",
                "street": "Musterweg 12",
                "postal_code": "40549",
                "city": "Teststadt",
                "preferred_contact": "email",
                "customer_notes": "Bitte Demo-Freigaben zuerst per Mail bestaetigen.",
            },
            "device": {
                "category": "amp",
                "manufacturer": "Mesa",
                "model": "Boogie",
                "serial_number": "MB-123",
                "accessories": "Netzkabel",
                "condition_notes": "gebraucht",
            },
            "issue_description": "Aussetzer im Betrieb",
            "technician": "Bank 1",
            "intake_date": "2026-03-29",
            "warranty_status": "nein",
            "quote_required": "ja",
            "diagnostic_source": "Werkbank",
            "internal_notes": "Externer KVA erwartet.",
        }

    def test_api_dashboard_returns_summary_payload(self):
        response = self.get("/api/dashboard")
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertIn("active_order_count", payload)
        self.assertIn("pending_quotes_count", payload)
        self.assertIn("unpaid_invoices_count", payload)
        self.assertIn("recent_orders", payload)
        self.assertTrue(payload["recent_orders"])

    def test_api_create_order_returns_nested_detail(self):
        response = self.post("/api/orders", json=self.create_order_payload())
        payload = response.get_json()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(payload["status"], "Angenommen")
        self.assertEqual(payload["customer"]["company_name"], "Atelier Nord Demo")
        self.assertEqual(payload["device"]["manufacturer"], "Mesa")
        self.assertEqual(payload["attachments"], [])
        self.assertTrue(payload["print_url"].endswith(f"/orders/{payload['id']}/print"))

    def test_api_order_detail_includes_quote_invoice_attachments_and_history(self):
        created = self.post("/api/orders", json=self.create_order_payload()).get_json()
        order_id = created["id"]

        detail = self.get(f"/api/orders/{order_id}")
        payload = detail.get_json()

        self.assertEqual(detail.status_code, 200)
        self.assertIsNone(payload["quote"])
        self.assertIsNone(payload["invoice"])
        self.assertEqual(payload["customer"]["name"], "Demo Kundin Blau")
        self.assertEqual(len(payload["status_history"]), 1)

    def test_api_quote_and_invoice_workflow_updates_order(self):
        created = self.post("/api/orders", json=self.create_order_payload()).get_json()
        order_id = created["id"]

        quote_response = self.post(
            f"/api/orders/{order_id}/quote",
            json={
                "title": "Kostenvoranschlag SO-Test",
                "work_description": "Fehleranalyse, Endstufentausch und Funktionstest.",
                "parts_description": "Endstufenmodul inkl. Beschaffung.",
                "labor_cost_cents": 8900,
                "parts_cost_cents": 12900,
                "external_cost_cents": 0,
                "shipping_cost_cents": 790,
                "valid_until": "2026-04-12",
                "customer_message": "Bitte kurze Freigabe per Mail oder Telefon.",
                "approval_status": "offen",
            },
        )
        quote_payload = quote_response.get_json()

        self.assertEqual(quote_response.status_code, 200)
        self.assertEqual(quote_payload["status"], "Wartet auf Freigabe")
        self.assertEqual(quote_payload["quote"]["approval_status"], "offen")
        self.assertIn(f"/orders/{order_id}/attachments/", quote_payload["quote"]["pdf_url"])

        invoice_response = self.post(
            f"/api/orders/{order_id}/invoice",
            json={
                "title": "Rechnung SO-Test",
                "labor_description": "Endstufentausch und Endtest.",
                "parts_description": "Endstufenmodul.",
                "labor_cost_cents": 8900,
                "parts_cost_cents": 12900,
                "external_cost_cents": 0,
                "shipping_cost_cents": 790,
                "invoice_date": "2026-04-02",
                "payment_status": "offen",
                "internal_note": "Zahlung bei Abholung vorgesehen.",
            },
        )
        invoice_payload = invoice_response.get_json()

        self.assertEqual(invoice_response.status_code, 200)
        self.assertEqual(invoice_payload["status"], "Abholbereit")
        self.assertEqual(invoice_payload["invoice"]["payment_status"], "offen")
        self.assertIsNotNone(invoice_payload["invoice"]["pdf_url"])

    def test_api_attachment_upload_and_delete_roundtrip(self):
        created = self.post("/api/orders", json=self.create_order_payload()).get_json()
        order_id = created["id"]

        upload_response = self.post(
            f"/api/orders/{order_id}/attachments",
            data={
                "document_type": "pruefprotokoll",
                "document_context": "Messprotokoll Werkbank",
                "order_files": (BytesIO(b"%PDF-1.4\n%benchflow\n"), "messung.pdf"),
            },
            content_type="multipart/form-data",
        )
        upload_payload = upload_response.get_json()

        self.assertEqual(upload_response.status_code, 200)
        self.assertEqual(upload_payload["added_count"], 1)
        self.assertEqual(upload_payload["attachments"][0]["document_type"], "pruefprotokoll")

        media_id = upload_payload["attachments"][0]["id"]
        delete_response = self.delete(f"/api/orders/{order_id}/attachments/{media_id}")

        self.assertEqual(delete_response.status_code, 200)
        self.assertEqual(delete_response.get_json()["deleted_media_id"], media_id)

    def test_api_customer_list_and_detail_work(self):
        created = self.post("/api/orders", json=self.create_order_payload()).get_json()
        customer_id = created["customer"]["id"]

        list_response = self.get("/api/customers?scope=all&q=Atelier")
        list_payload = list_response.get_json()
        detail_response = self.get(f"/api/customers/{customer_id}")
        detail_payload = detail_response.get_json()

        self.assertEqual(list_response.status_code, 200)
        self.assertTrue(list_payload["customers"])
        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(detail_payload["customer"]["id"], customer_id)
        self.assertEqual(detail_payload["orders"][0]["customer_id"], customer_id)

    def test_api_meta_exposes_picker_options(self):
        response = self.get("/api/meta")
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertIn("technicians", payload)
        self.assertIn("document_types", payload)
        self.assertIn("Bank 1", payload["technicians"])
        self.assertTrue(any(item["value"] == "rechnung" for item in payload["document_types"]))
