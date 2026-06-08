import SwiftUI

@main
struct BenchFlowNativeApp: App {
    @AppStorage("colorScheme") private var colorScheme = "system"
    private let apiClient = APIClient()

    var body: some Scene {
        WindowGroup {
            AppShell(apiClient: apiClient, colorScheme: $colorScheme)
                .preferredColorScheme(preferredScheme)
        }
    }

    private var preferredScheme: ColorScheme? {
        switch colorScheme {
        case "light":
            return .light
        case "dark":
            return .dark
        default:
            return nil
        }
    }
}

private struct AppShell: View {
    let apiClient: APIClient
    @Binding var colorScheme: String

    var body: some View {
        TabView {
            NavigationStack {
                DashboardView(apiClient: apiClient)
            }
            .tabItem {
                Label("Dashboard", systemImage: "square.grid.2x2")
            }

            NavigationStack {
                OrderListView(apiClient: apiClient)
            }
            .tabItem {
                Label("Auftraege", systemImage: "wrench.and.screwdriver")
            }

            NavigationStack {
                NewOrderView(apiClient: apiClient)
            }
            .tabItem {
                Label("Neuer Auftrag", systemImage: "plus.square")
            }

            NavigationStack {
                ArchiveView(apiClient: apiClient)
            }
            .tabItem {
                Label("Archiv", systemImage: "archivebox")
            }

            NavigationStack {
                CustomerListView(apiClient: apiClient)
            }
            .tabItem {
                Label("Kunden", systemImage: "person.3")
            }
        }
        .toolbar {
            ToolbarItem(placement: .automatic) {
                Picker("Design", selection: $colorScheme) {
                    Text("System").tag("system")
                    Text("Hell").tag("light")
                    Text("Dunkel").tag("dark")
                }
                .pickerStyle(.segmented)
            }
        }
    }
}
