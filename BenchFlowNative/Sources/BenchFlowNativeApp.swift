import Observation
import SwiftUI

@main
struct BenchFlowNativeApp: App {
    @AppStorage("colorScheme") private var colorScheme = "system"
    private let apiClient = APIClient()

    init() {
        BenchFlowAppearance.apply()
    }

    var body: some Scene {
        WindowGroup {
            RootScene(apiClient: apiClient)
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

private struct RootScene: View {
    let apiClient: APIClient
    @Environment(\.colorScheme) private var colorScheme

    var body: some View {
        let palette = BenchFlowPalette.resolve(for: colorScheme)

        GeometryReader { geometry in
            ZStack(alignment: .top) {
                BenchFlowBackground(palette: palette)

                AppShell(apiClient: apiClient)
                    .frame(
                        width: geometry.size.width,
                        height: geometry.size.height,
                        alignment: .topLeading
                    )
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
        }
        .ignoresSafeArea()
    }
}

private enum AppTab: Hashable {
    case dashboard
    case orders
    case newOrder
    case archive
    case customers
}

private struct AppShell: View {
    let apiClient: APIClient
    @State private var selectedTab: AppTab = .dashboard

    var body: some View {
        ZStack {
            switch selectedTab {
            case .dashboard:
                RootTabContainer {
                    DashboardView(apiClient: apiClient)
                }
            case .orders:
                RootTabContainer {
                    OrderListView(apiClient: apiClient)
                }
            case .newOrder:
                RootTabContainer {
                    NewOrderView(apiClient: apiClient)
                }
            case .archive:
                RootTabContainer {
                    ArchiveView(apiClient: apiClient)
                }
            case .customers:
                RootTabContainer {
                    CustomerListView(apiClient: apiClient)
                }
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
        .benchFlowScreenChrome()
        .overlay(alignment: .bottom) {
            BenchFlowTabBar(selection: $selectedTab)
                .padding(.horizontal, 10)
                .padding(.bottom, 0)
        }
    }
}

private struct RootTabContainer<Content: View>: View {
    @ViewBuilder let content: () -> Content

    var body: some View {
        NavigationStack {
            content()
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
    }
}

private struct BenchFlowTabBar: View {
    @Environment(\.colorScheme) private var colorScheme
    @Binding var selection: AppTab

    var body: some View {
        let palette = BenchFlowPalette.resolve(for: colorScheme)

        HStack(spacing: 4) {
            tabButton(title: "Start", icon: "square.grid.2x2", tab: .dashboard, palette: palette)
            tabButton(title: "Auftr.", icon: "wrench.and.screwdriver", tab: .orders, palette: palette)
            tabButton(title: "Neu", icon: "plus.square", tab: .newOrder, palette: palette)
            tabButton(title: "Archiv", icon: "archivebox", tab: .archive, palette: palette)
            tabButton(title: "Kunden", icon: "person.3", tab: .customers, palette: palette)
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 5)
        .background(
            RoundedRectangle(cornerRadius: 24, style: .continuous)
                .fill(
                    LinearGradient(
                        colors: [palette.panel, palette.panelStrong],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )
        )
        .overlay(
            RoundedRectangle(cornerRadius: 24, style: .continuous)
                .stroke(palette.line, lineWidth: 1)
        )
        .shadow(color: Color.black.opacity(0.16), radius: 12, y: 4)
    }

    private func tabButton(title: String, icon: String, tab: AppTab, palette: BenchFlowPalette) -> some View {
        Button {
            selection = tab
        } label: {
            VStack(spacing: 3) {
                Image(systemName: icon)
                    .font(.system(size: 15, weight: .semibold))
                Text(title)
                    .font(.system(size: 10, weight: .semibold, design: .rounded))
                    .lineLimit(1)
                    .minimumScaleFactor(0.85)
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, 6)
            .foregroundStyle(selection == tab ? palette.accent : palette.muted)
            .background(
                RoundedRectangle(cornerRadius: 18, style: .continuous)
                    .fill(selection == tab ? palette.accentSoft : .clear)
            )
        }
        .buttonStyle(.plain)
    }
}
