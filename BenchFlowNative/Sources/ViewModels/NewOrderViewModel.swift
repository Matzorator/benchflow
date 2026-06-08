import Foundation
import Observation

@MainActor
@Observable
final class NewOrderViewModel {
    private let apiClient: APIClient

    var meta: MetaResponse?
    var customerCandidates: [Customer] = []
    var draft = OrderMutationRequest(
        customer: CustomerDraft(),
        device: DeviceDraft(),
        issue_description: "",
        technician: "",
        intake_date: ISO8601DateFormatter.shortDate.string(from: .now),
        warranty_status: "unbekannt",
        quote_required: "nein",
        diagnostic_source: "Werkbank",
        internal_notes: "",
        status: nil
    )
    var isSubmitting = false
    var isLoading = false
    var errorMessage: String?
    var toast: ToastState?
    var createdOrder: ServiceOrder?

    init(apiClient: APIClient) {
        self.apiClient = apiClient
    }

    func load() async {
        isLoading = true
        defer { isLoading = false }

        do {
            async let metaTask: MetaResponse = apiClient.fetch("/api/meta")
            async let customerTask: CustomersResponse = apiClient.fetch("/api/customers?scope=all")
            let (metaResponse, customerResponse) = try await (metaTask, customerTask)
            meta = metaResponse
            customerCandidates = customerResponse.customers
            if draft.technician.isEmpty {
                draft.technician = metaResponse.technicians.first ?? ""
            }
            errorMessage = nil
        } catch {
            errorMessage = (error as? APIError)?.errorDescription ?? error.localizedDescription
        }
    }

    func applyCustomer(_ customer: Customer) {
        draft.customer.name = customer.name
        draft.customer.company_name = customer.company_name
        draft.customer.email = customer.email
        draft.customer.phone = customer.phone
        draft.customer.street = customer.street
        draft.customer.postal_code = customer.postal_code
        draft.customer.city = customer.city
        draft.customer.preferred_contact = customer.preferred_contact
        draft.customer.customer_notes = customer.customer_notes
    }

    func submit() async -> ServiceOrder? {
        isSubmitting = true
        defer { isSubmitting = false }

        do {
            let order: ServiceOrder = try await apiClient.fetch("/api/orders", method: "POST", body: draft)
            createdOrder = order
            toast = ToastState(title: "Auftrag angelegt", message: order.order_number)
            errorMessage = nil
            return order
        } catch {
            errorMessage = (error as? APIError)?.errorDescription ?? error.localizedDescription
            return nil
        }
    }
}
