import Foundation
import Observation

@MainActor
@Observable
final class CustomerDetailViewModel {
    private let apiClient: APIClient
    let customerID: Int

    var response: CustomerDetailResponse?
    var isLoading = false
    var errorMessage: String?

    init(apiClient: APIClient, customerID: Int) {
        self.apiClient = apiClient
        self.customerID = customerID
    }

    func load() async {
        isLoading = true
        defer { isLoading = false }

        do {
            response = try await apiClient.fetch("/api/customers/\(customerID)")
            errorMessage = nil
        } catch {
            errorMessage = (error as? APIError)?.errorDescription ?? error.localizedDescription
        }
    }
}
