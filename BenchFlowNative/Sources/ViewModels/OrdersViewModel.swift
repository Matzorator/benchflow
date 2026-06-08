import Foundation
import Observation

@MainActor
@Observable
final class OrdersViewModel {
    private let apiClient: APIClient
    let archived: Bool

    var orders: [ServiceOrder] = []
    var meta: MetaResponse?
    var isLoading = false
    var errorMessage: String?
    var query = ""
    var selectedStatus = ""
    var selectedCategory = ""
    var selectedDocumentType = ""

    init(apiClient: APIClient, archived: Bool) {
        self.apiClient = apiClient
        self.archived = archived
    }

    func load() async {
        isLoading = true
        defer { isLoading = false }

        do {
            async let metaTask: MetaResponse = apiClient.fetch("/api/meta")
            async let ordersTask: OrdersResponse = apiClient.fetch(endpoint)
            let (metaResponse, ordersResponse) = try await (metaTask, ordersTask)
            meta = metaResponse
            orders = ordersResponse.orders
            errorMessage = nil
        } catch {
            errorMessage = (error as? APIError)?.errorDescription ?? error.localizedDescription
        }
    }

    var endpoint: String {
        var components = URLComponents()
        components.path = "/api/orders"
        components.queryItems = [
            URLQueryItem(name: "archived", value: archived ? "true" : "false"),
            URLQueryItem(name: "q", value: query.isEmpty ? nil : query),
            URLQueryItem(name: "status", value: selectedStatus.isEmpty ? nil : selectedStatus),
            URLQueryItem(name: "category", value: selectedCategory.isEmpty ? nil : selectedCategory),
            URLQueryItem(name: "document_type", value: selectedDocumentType.isEmpty ? nil : selectedDocumentType),
        ]
        return components.string ?? "/api/orders"
    }
}
