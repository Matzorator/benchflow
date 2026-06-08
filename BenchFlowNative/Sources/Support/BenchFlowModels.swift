import Foundation

struct DashboardResponse: Codable, Sendable {
    let active_order_count: Int
    let pending_quotes_count: Int
    let unpaid_invoices_count: Int
    let ready_count: Int
    let blocked_count: Int
    let archived_count: Int
    let status_summary: [StatusSummaryItem]
    let recent_orders: [ServiceOrder]
}

struct StatusSummaryItem: Codable, Hashable, Sendable, Identifiable {
    let status: String
    let total: Int

    var id: String { status }
}

struct OrdersResponse: Codable, Sendable {
    let orders: [ServiceOrder]
    let order_count: Int
    let archived: Bool
    let filters: OrderFilters
}

struct OrderFilters: Codable, Hashable, Sendable {
    let q: String
    let status: String
    let category: String
    let document_type: String?
}

struct ServiceOrder: Codable, Identifiable, Hashable, Sendable {
    let id: Int
    let order_number: String
    let customer_id: Int
    let device_id: Int
    let issue_description: String
    let status: String
    let technician: String
    let intake_date: String
    let warranty_status: String
    let quote_required: String
    let diagnostic_source: String
    let internal_notes: String
    let archived_at: String?
    let created_at: String
    let updated_at: String?
    let document_count: Int
    let document_type_count: Int
    let primary_document_type: String
    let document_hint: String
    let customer: Customer
    let device: Device
    let print_url: String
    let internal_print_url: String
    let qr_url: String
    let attachments: [Attachment]?
    let quote: Quote?
    let invoice: Invoice?
    let status_history: [StatusHistoryEntry]?
}

struct Customer: Codable, Identifiable, Hashable, Sendable {
    let id: Int
    var name: String
    var company_name: String
    var email: String
    var phone: String
    var street: String
    var postal_code: String
    var city: String
    var preferred_contact: String
    var customer_notes: String
    var created_at: String
    var preferred_contact_label: String
    var location_label: String
    var order_count: Int?
    var active_order_count: Int?
    var latest_order_number: String?
    var latest_order_status: String?
    var latest_order_updated_at: String?
}

struct Device: Codable, Identifiable, Hashable, Sendable {
    let id: Int
    var category: String
    var manufacturer: String
    var model: String
    var serial_number: String
    var accessories: String
    var condition_notes: String
    var image_data: String
    var created_at: String
}

struct Attachment: Codable, Identifiable, Hashable, Sendable {
    let id: Int
    let service_order_id: Int
    let filename: String
    let mime_type: String
    let document_type: String
    let order_context: String
    let created_at: String
    let is_image: Bool
    let is_document: Bool
    let display_name: String
    let document_type_label: String
    let size_label: String
    let created_label: String
    let file_url: String?
}

struct Quote: Codable, Hashable, Sendable {
    let id: Int
    let service_order_id: Int
    let quote_number: String
    var title: String
    var work_description: String
    var parts_description: String
    var labor_cost_cents: Int
    var parts_cost_cents: Int
    var external_cost_cents: Int
    var shipping_cost_cents: Int
    var total_cost_cents: Int
    var valid_until: String
    var customer_message: String
    var approval_status: String
    let pdf_media_id: Int?
    let created_at: String
    let updated_at: String
    let approval_status_label: String
    let labor_cost_label: String
    let parts_cost_label: String
    let external_cost_label: String
    let shipping_cost_label: String
    let total_cost_label: String
    let pdf_url: String?
}

struct Invoice: Codable, Hashable, Sendable {
    let id: Int
    let service_order_id: Int
    let invoice_number: String
    var title: String
    var labor_description: String
    var parts_description: String
    var labor_cost_cents: Int
    var parts_cost_cents: Int
    var external_cost_cents: Int
    var shipping_cost_cents: Int
    var total_cost_cents: Int
    var invoice_date: String
    var payment_status: String
    var internal_note: String
    let pdf_media_id: Int?
    let created_at: String
    let updated_at: String
    let payment_status_label: String
    let labor_cost_label: String
    let parts_cost_label: String
    let external_cost_label: String
    let shipping_cost_label: String
    let total_cost_label: String
    let pdf_url: String?
}

struct StatusHistoryEntry: Codable, Identifiable, Hashable, Sendable {
    let id: Int
    let service_order_id: Int
    let status: String
    let note: String
    let changed_at: String
}

struct CustomersResponse: Codable, Sendable {
    let customers: [Customer]
    let customer_count: Int
    let filters: CustomerFilters
}

struct CustomerFilters: Codable, Hashable, Sendable {
    let q: String
    let scope: String
}

struct CustomerDetailResponse: Codable, Sendable {
    let customer: Customer
    let orders: [ServiceOrder]
    let order_count: Int
}

struct MetaResponse: Codable, Sendable {
    let base_url: String
    let technicians: [String]
    let statuses: [String]
    let categories: [PickerOption]
    let warranty_options: [PickerOption]
    let quote_options: [PickerOption]
    let diagnostic_sources: [String]
    let preferred_contact_options: [PickerOption]
    let document_types: [PickerOption]
    let quote_approval_options: [PickerOption]
    let invoice_payment_options: [PickerOption]
}

struct PickerOption: Codable, Hashable, Sendable, Identifiable {
    let value: String
    let label: String

    var id: String { value }
}

struct AttachmentUploadResponse: Codable, Sendable {
    let attachments: [Attachment]
    let added_count: Int
}

struct DeleteAttachmentResponse: Codable, Sendable {
    let deleted_media_id: Int
}

struct MailtoResponse: Codable, Sendable {
    let mailto_url: String
}

struct APIErrorPayload: Codable, Sendable {
    let error: String
    let field_errors: [String: String]?
}

struct OrderMutationRequest: Codable, Sendable {
    var customer: CustomerDraft
    var device: DeviceDraft
    var issue_description: String
    var technician: String
    var intake_date: String
    var warranty_status: String
    var quote_required: String
    var diagnostic_source: String
    var internal_notes: String
    var status: String?
}

struct CustomerDraft: Codable, Hashable, Sendable {
    var name: String = ""
    var company_name: String = ""
    var email: String = ""
    var phone: String = ""
    var street: String = ""
    var postal_code: String = ""
    var city: String = ""
    var preferred_contact: String = "telefon"
    var customer_notes: String = ""
}

struct DeviceDraft: Codable, Hashable, Sendable {
    var category: String = ""
    var manufacturer: String = ""
    var model: String = ""
    var serial_number: String = ""
    var accessories: String = ""
    var condition_notes: String = ""
}

struct QuoteMutationRequest: Codable, Hashable, Sendable {
    var title: String = ""
    var work_description: String = ""
    var parts_description: String = ""
    var labor_cost_cents: Int = 0
    var parts_cost_cents: Int = 0
    var external_cost_cents: Int = 0
    var shipping_cost_cents: Int = 0
    var valid_until: String = ""
    var customer_message: String = ""
    var approval_status: String = "offen"
}

struct InvoiceMutationRequest: Codable, Hashable, Sendable {
    var title: String = ""
    var labor_description: String = ""
    var parts_description: String = ""
    var labor_cost_cents: Int = 0
    var parts_cost_cents: Int = 0
    var external_cost_cents: Int = 0
    var shipping_cost_cents: Int = 0
    var invoice_date: String = ""
    var payment_status: String = "offen"
    var internal_note: String = ""
}

struct UploadableFile: Hashable, Sendable, Identifiable {
    let id = UUID()
    let filename: String
    let mime_type: String
    let data: Data
}

extension ServiceOrder {
    var customer_line: String {
        [customer.name, customer.company_name].filter { !$0.isEmpty }.joined(separator: " · ")
    }

    var device_line: String {
        [device.manufacturer, device.model].filter { !$0.isEmpty }.joined(separator: " ")
    }
}
