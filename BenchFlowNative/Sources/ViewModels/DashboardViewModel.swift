import Foundation
import Observation

@MainActor
@Observable
final class DashboardViewModel {
    private let apiClient: APIClient

    var dashboard: DashboardResponse?
    var isLoading = false
    var errorMessage: String?
    var toast: ToastState?

    init(apiClient: APIClient) {
        self.apiClient = apiClient
    }

    func load() async {
        isLoading = true
        defer { isLoading = false }

        do {
            dashboard = try await apiClient.fetch("/api/dashboard")
            errorMessage = nil
        } catch {
            errorMessage = (error as? APIError)?.errorDescription ?? error.localizedDescription
        }
    }
}
