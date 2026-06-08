import Foundation
import Observation

@MainActor
@Observable
final class OrderDetailViewModel {
    private let apiClient: APIClient
    let orderID: Int

    var order: ServiceOrder?
    var meta: MetaResponse?
    var orderDraft: OrderMutationRequest?
    var quoteDraft = QuoteMutationRequest()
    var invoiceDraft = InvoiceMutationRequest()
    var selectedDocumentType = ""
    var selectedDocumentContext = ""
    var isLoading = false
    var isSaving = false
    var errorMessage: String?
    var toast: ToastState?
    var mailtoURL: URL?

    init(apiClient: APIClient, orderID: Int) {
        self.apiClient = apiClient
        self.orderID = orderID
    }

    func load() async {
        isLoading = true
        defer { isLoading = false }

        do {
            async let metaTask: MetaResponse = apiClient.fetch("/api/meta")
            async let orderTask: ServiceOrder = apiClient.fetch("/api/orders/\(orderID)")
            let (metaResponse, orderResponse) = try await (metaTask, orderTask)
            meta = metaResponse
            order = orderResponse
            hydrateDrafts(from: orderResponse, meta: metaResponse)
            errorMessage = nil
        } catch {
            errorMessage = (error as? APIError)?.errorDescription ?? error.localizedDescription
        }
    }

    func saveOrder() async {
        guard let orderDraft else { return }
        isSaving = true
        defer { isSaving = false }

        do {
            let updated: ServiceOrder = try await apiClient.fetch("/api/orders/\(orderID)", method: "PATCH", body: orderDraft)
            order = updated
            hydrateDrafts(from: updated, meta: meta)
            toast = ToastState(title: "Auftrag aktualisiert", message: updated.order_number)
            errorMessage = nil
        } catch {
            errorMessage = (error as? APIError)?.errorDescription ?? error.localizedDescription
        }
    }

    func saveQuote() async {
        isSaving = true
        defer { isSaving = false }

        do {
            let updated: ServiceOrder = try await apiClient.fetch("/api/orders/\(orderID)/quote", method: "POST", body: quoteDraft)
            order = updated
            hydrateDrafts(from: updated, meta: meta)
            toast = ToastState(title: "KVA gespeichert", message: updated.quote?.quote_number ?? updated.order_number)
            errorMessage = nil
        } catch {
            errorMessage = (error as? APIError)?.errorDescription ?? error.localizedDescription
        }
    }

    func saveInvoice() async {
        isSaving = true
        defer { isSaving = false }

        do {
            let updated: ServiceOrder = try await apiClient.fetch("/api/orders/\(orderID)/invoice", method: "POST", body: invoiceDraft)
            order = updated
            hydrateDrafts(from: updated, meta: meta)
            toast = ToastState(title: "Rechnung gespeichert", message: updated.invoice?.invoice_number ?? updated.order_number)
            errorMessage = nil
        } catch {
            errorMessage = (error as? APIError)?.errorDescription ?? error.localizedDescription
        }
    }

    func archive() async {
        await postMutation("/api/orders/\(orderID)/archive", successTitle: "Archiviert")
    }

    func restore() async {
        await postMutation("/api/orders/\(orderID)/restore", successTitle: "Wiederhergestellt")
    }

    func prepareQuoteEmail() async {
        do {
            let response: MailtoResponse = try await apiClient.fetch("/api/orders/\(orderID)/quote/email")
            mailtoURL = URL(string: response.mailto_url)
            toast = ToastState(title: "KVA-Mail vorbereitet", message: order?.customer.email ?? "")
            errorMessage = nil
        } catch {
            errorMessage = (error as? APIError)?.errorDescription ?? error.localizedDescription
        }
    }

    func uploadAttachments(_ files: [UploadableFile]) async {
        guard !files.isEmpty else { return }
        isSaving = true
        defer { isSaving = false }

        do {
            let response = try await apiClient.uploadAttachments(
                orderID: orderID,
                files: files,
                documentType: selectedDocumentType,
                orderContext: selectedDocumentContext
            )
            if var currentOrder = order {
                currentOrder = ServiceOrder(
                    id: currentOrder.id,
                    order_number: currentOrder.order_number,
                    customer_id: currentOrder.customer_id,
                    device_id: currentOrder.device_id,
                    issue_description: currentOrder.issue_description,
                    status: currentOrder.status,
                    technician: currentOrder.technician,
                    intake_date: currentOrder.intake_date,
                    warranty_status: currentOrder.warranty_status,
                    quote_required: currentOrder.quote_required,
                    diagnostic_source: currentOrder.diagnostic_source,
                    internal_notes: currentOrder.internal_notes,
                    archived_at: currentOrder.archived_at,
                    created_at: currentOrder.created_at,
                    updated_at: currentOrder.updated_at,
                    document_count: currentOrder.document_count,
                    document_type_count: currentOrder.document_type_count,
                    primary_document_type: currentOrder.primary_document_type,
                    document_hint: currentOrder.document_hint,
                    customer: currentOrder.customer,
                    device: currentOrder.device,
                    print_url: currentOrder.print_url,
                    internal_print_url: currentOrder.internal_print_url,
                    qr_url: currentOrder.qr_url,
                    attachments: response.attachments,
                    quote: currentOrder.quote,
                    invoice: currentOrder.invoice,
                    status_history: currentOrder.status_history
                )
                order = currentOrder
            }
            toast = ToastState(title: "Anhaenge hochgeladen", message: "\(response.added_count) Datei(en)")
            errorMessage = nil
        } catch {
            errorMessage = (error as? APIError)?.errorDescription ?? error.localizedDescription
        }
    }

    func deleteAttachment(_ attachment: Attachment) async {
        isSaving = true
        defer { isSaving = false }

        do {
            _ = try await apiClient.deleteAttachment(orderID: orderID, mediaID: attachment.id)
            await load()
            toast = ToastState(title: "Anhang geloescht", message: attachment.display_name)
        } catch {
            errorMessage = (error as? APIError)?.errorDescription ?? error.localizedDescription
        }
    }

    private func postMutation(_ endpoint: String, successTitle: String) async {
        isSaving = true
        defer { isSaving = false }

        do {
            let updated: ServiceOrder = try await apiClient.fetch(endpoint, method: "POST", body: EmptyPayload())
            order = updated
            hydrateDrafts(from: updated, meta: meta)
            toast = ToastState(title: successTitle, message: updated.order_number)
            errorMessage = nil
        } catch {
            errorMessage = (error as? APIError)?.errorDescription ?? error.localizedDescription
        }
    }

    private func hydrateDrafts(from order: ServiceOrder, meta: MetaResponse?) {
        orderDraft = OrderMutationRequest(
            customer: CustomerDraft(
                name: order.customer.name,
                company_name: order.customer.company_name,
                email: order.customer.email,
                phone: order.customer.phone,
                street: order.customer.street,
                postal_code: order.customer.postal_code,
                city: order.customer.city,
                preferred_contact: order.customer.preferred_contact,
                customer_notes: order.customer.customer_notes
            ),
            device: DeviceDraft(
                category: order.device.category,
                manufacturer: order.device.manufacturer,
                model: order.device.model,
                serial_number: order.device.serial_number,
                accessories: order.device.accessories,
                condition_notes: order.device.condition_notes
            ),
            issue_description: order.issue_description,
            technician: order.technician,
            intake_date: order.intake_date,
            warranty_status: order.warranty_status,
            quote_required: order.quote_required,
            diagnostic_source: order.diagnostic_source,
            internal_notes: order.internal_notes,
            status: order.status
        )

        if let quote = order.quote {
            quoteDraft = QuoteMutationRequest(
                title: quote.title,
                work_description: quote.work_description,
                parts_description: quote.parts_description,
                labor_cost_cents: quote.labor_cost_cents,
                parts_cost_cents: quote.parts_cost_cents,
                external_cost_cents: quote.external_cost_cents,
                shipping_cost_cents: quote.shipping_cost_cents,
                valid_until: quote.valid_until,
                customer_message: quote.customer_message,
                approval_status: quote.approval_status
            )
        } else {
            quoteDraft = QuoteMutationRequest(
                title: "Kostenvoranschlag \(order.order_number)",
                work_description: "",
                parts_description: "",
                labor_cost_cents: 0,
                parts_cost_cents: 0,
                external_cost_cents: 0,
                shipping_cost_cents: 0,
                valid_until: ISO8601DateFormatter.shortDate.string(from: Calendar.current.date(byAdding: .day, value: 14, to: .now) ?? .now),
                customer_message: "",
                approval_status: "offen"
            )
        }

        if let invoice = order.invoice {
            invoiceDraft = InvoiceMutationRequest(
                title: invoice.title,
                labor_description: invoice.labor_description,
                parts_description: invoice.parts_description,
                labor_cost_cents: invoice.labor_cost_cents,
                parts_cost_cents: invoice.parts_cost_cents,
                external_cost_cents: invoice.external_cost_cents,
                shipping_cost_cents: invoice.shipping_cost_cents,
                invoice_date: invoice.invoice_date,
                payment_status: invoice.payment_status,
                internal_note: invoice.internal_note
            )
        } else {
            invoiceDraft = InvoiceMutationRequest(
                title: "Rechnung \(order.order_number)",
                labor_description: "",
                parts_description: "",
                labor_cost_cents: 0,
                parts_cost_cents: 0,
                external_cost_cents: 0,
                shipping_cost_cents: 0,
                invoice_date: ISO8601DateFormatter.shortDate.string(from: .now),
                payment_status: "offen",
                internal_note: ""
            )
        }

        if selectedDocumentType.isEmpty {
            selectedDocumentType = meta?.document_types.first(where: { !$0.value.isEmpty })?.value ?? "pruefprotokoll"
        }
    }
}

private struct EmptyPayload: Codable {}

private extension ISO8601DateFormatter {
    static let shortDate: DateFormatter = {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter
    }()
}
