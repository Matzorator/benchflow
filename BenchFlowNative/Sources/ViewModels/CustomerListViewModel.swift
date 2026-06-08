import Foundation
import Observation

@MainActor
@Observable
final class CustomerListViewModel {
    private let apiClient: APIClient

    var customers: [Customer] = []
    var query = ""
    var scope = "active"
    var isLoading = false
    var errorMessage: String?

    init(apiClient: APIClient) {
        self.apiClient = apiClient
    }

    func load() async {
        isLoading = true
        defer { isLoading = false }

        do {
            let response: CustomersResponse = try await apiClient.fetch(endpoint)
            customers = response.customers
            errorMessage = nil
        } catch {
            errorMessage = (error as? APIError)?.errorDescription ?? error.localizedDescription
        }
    }

    var endpoint: String {
        var components = URLComponents()
        components.path = "/api/customers"
        components.queryItems = [
            URLQueryItem(name: "scope", value: scope),
            URLQueryItem(name: "q", value: query.isEmpty ? nil : query),
        ]
        return components.string ?? "/api/customers"
    }
}
