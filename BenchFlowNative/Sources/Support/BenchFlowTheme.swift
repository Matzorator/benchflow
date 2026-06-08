import SwiftUI
import UIKit

struct BenchFlowPalette {
    let backgroundTop: Color
    let backgroundBottom: Color
    let glowPrimary: Color
    let glowWarning: Color
    let panel: Color
    let panelStrong: Color
    let panelSoft: Color
    let line: Color
    let text: Color
    let muted: Color
    let accent: Color
    let accentSoft: Color
    let success: Color
    let warning: Color
    let danger: Color

    static func resolve(for scheme: ColorScheme) -> BenchFlowPalette {
        if scheme == .light {
            return BenchFlowPalette(
                backgroundTop: Color(hex: 0xF8FBFD),
                backgroundBottom: Color(hex: 0xEFF3F6),
                glowPrimary: Color(hex: 0x0087A3).opacity(0.08),
                glowWarning: Color(hex: 0xD9672F).opacity(0.06),
                panel: Color.white.opacity(0.92),
                panelStrong: Color(hex: 0xEDF5F8),
                panelSoft: Color.white.opacity(0.84),
                line: Color(hex: 0xC7D3DE),
                text: Color(hex: 0x13202C),
                muted: Color(hex: 0x5F7387),
                accent: Color(hex: 0x0087A3),
                accentSoft: Color(hex: 0x0087A3).opacity(0.10),
                success: Color(hex: 0x118B57),
                warning: Color(hex: 0xD9672F),
                danger: Color(hex: 0xC62649)
            )
        }

        return BenchFlowPalette(
            backgroundTop: Color(hex: 0x0C0F13),
            backgroundBottom: Color(hex: 0x0A0C0F),
            glowPrimary: Color(hex: 0x00E5FF).opacity(0.09),
            glowWarning: Color(hex: 0xFF6B35).opacity(0.07),
            panel: Color(hex: 0x0F1318).opacity(0.92),
            panelStrong: Color(hex: 0x121821),
            panelSoft: Color(hex: 0x0F1318).opacity(0.82),
            line: Color(hex: 0x1E2530),
            text: Color(hex: 0xC8D8E8),
            muted: Color(hex: 0x72879D),
            accent: Color(hex: 0x00E5FF),
            accentSoft: Color(hex: 0x00E5FF).opacity(0.12),
            success: Color(hex: 0x00FF88),
            warning: Color(hex: 0xFF6B35),
            danger: Color(hex: 0xFF2244)
        )
    }
}

struct BenchFlowBackground: View {
    let palette: BenchFlowPalette

    var body: some View {
        ZStack {
            LinearGradient(
                colors: [palette.backgroundTop, palette.backgroundBottom],
                startPoint: .top,
                endPoint: .bottom
            )

            RadialGradient(
                colors: [palette.glowPrimary, .clear],
                center: .topLeading,
                startRadius: 20,
                endRadius: 280
            )

            RadialGradient(
                colors: [palette.glowWarning, .clear],
                center: UnitPoint(x: 0.88, y: 0.12),
                startRadius: 20,
                endRadius: 220
            )

            BenchFlowScanlineOverlay(color: palette.accent, opacity: palette.backgroundTop == Color(hex: 0xF8FBFD) ? 0.015 : 0.03)
        }
        .ignoresSafeArea()
    }
}

struct BenchFlowScanlineOverlay: View {
    let color: Color
    let opacity: Double

    var body: some View {
        GeometryReader { geometry in
            Path { path in
                let spacing: CGFloat = 4
                var y: CGFloat = 0
                while y < geometry.size.height {
                    path.move(to: CGPoint(x: 0, y: y))
                    path.addLine(to: CGPoint(x: geometry.size.width, y: y))
                    y += spacing
                }
            }
            .stroke(color.opacity(opacity), lineWidth: 1)
        }
        .allowsHitTesting(false)
    }
}

struct BenchFlowSectionHeader: View {
    let title: String
    let palette: BenchFlowPalette

    var body: some View {
        Text(title.uppercased())
            .font(.system(size: 12, weight: .semibold, design: .monospaced))
            .tracking(1.4)
            .foregroundStyle(palette.muted)
            .padding(.bottom, 4)
    }
}

struct BenchFlowPanel<Content: View>: View {
    let palette: BenchFlowPalette
    @ViewBuilder let content: () -> Content

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            content()
        }
        .padding(14)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(panelBackground)
        .overlay(
            RoundedRectangle(cornerRadius: 18, style: .continuous)
                .stroke(palette.line, lineWidth: 1)
        )
        .shadow(color: Color.black.opacity(0.18), radius: 18, y: 10)
    }

    private var panelBackground: some View {
        RoundedRectangle(cornerRadius: 18, style: .continuous)
            .fill(
                LinearGradient(
                    colors: [palette.panel, palette.panelStrong],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
            )
    }
}

struct BenchFlowTopBar: View {
    let title: String
    let palette: BenchFlowPalette
    var showsBackButton = false
    var showsThemeButton = true

    @AppStorage("colorScheme") private var colorSchemeChoice = "system"
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        HStack(alignment: .center, spacing: 12) {
            if showsBackButton {
                Button {
                    dismiss()
                } label: {
                    Image(systemName: "chevron.left")
                        .font(.system(size: 14, weight: .semibold))
                        .foregroundStyle(palette.text)
                        .frame(width: 36, height: 36)
                        .background(
                            Circle()
                                .fill(palette.panel.opacity(0.94))
                        )
                        .overlay(
                            Circle()
                                .stroke(palette.line, lineWidth: 1)
                        )
                }
                .buttonStyle(.plain)
            }

            Text(title)
                .font(.system(size: 20, weight: .semibold, design: .rounded))
                .foregroundStyle(palette.text)
                .lineLimit(1)

            Spacer()

            if showsThemeButton {
                Menu {
                    Picker("Design", selection: $colorSchemeChoice) {
                        Label("System", systemImage: "circle.lefthalf.filled").tag("system")
                        Label("Hell", systemImage: "sun.max").tag("light")
                        Label("Dunkel", systemImage: "moon").tag("dark")
                    }
                } label: {
                    Image(systemName: "circle.lefthalf.filled")
                        .font(.system(size: 14, weight: .semibold, design: .monospaced))
                        .foregroundStyle(palette.text)
                        .frame(width: 36, height: 36)
                        .background(
                            Circle()
                                .fill(palette.panel.opacity(0.94))
                        )
                        .overlay(
                            Circle()
                                .stroke(palette.line, lineWidth: 1)
                        )
                }
            }
        }
        .padding(.vertical, 0)
    }
}

struct BenchFlowScreenChrome: ViewModifier {
    @Environment(\.colorScheme) private var colorScheme

    func body(content: Content) -> some View {
        content
            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
            .scrollContentBackground(.hidden)
            .foregroundStyle(BenchFlowPalette.resolve(for: colorScheme).text)
            .tint(BenchFlowPalette.resolve(for: colorScheme).accent)
    }
}

extension View {
    func benchFlowScreenChrome() -> some View {
        modifier(BenchFlowScreenChrome())
    }

    func benchFlowPageChrome(
        title: String,
        showsBackButton: Bool = false,
        showsThemeButton: Bool = true,
        topContentPadding: CGFloat = 30,
        bottomContentPadding: CGFloat = 58
    ) -> some View {
        modifier(
            BenchFlowPageChromeModifier(
                title: title,
                showsBackButton: showsBackButton,
                showsThemeButton: showsThemeButton,
                topContentPadding: topContentPadding,
                bottomContentPadding: bottomContentPadding
            )
        )
    }
}

private struct BenchFlowPageChromeModifier: ViewModifier {
    @Environment(\.colorScheme) private var colorScheme

    let title: String
    let showsBackButton: Bool
    let showsThemeButton: Bool
    let topContentPadding: CGFloat
    let bottomContentPadding: CGFloat

    func body(content: Content) -> some View {
        let palette = BenchFlowPalette.resolve(for: colorScheme)

        content
            .toolbar(.hidden, for: .navigationBar)
            .safeAreaInset(edge: .top, spacing: 0) {
                Color.clear
                    .frame(height: topContentPadding)
            }
            .safeAreaInset(edge: .bottom, spacing: 0) {
                Color.clear
                    .frame(height: bottomContentPadding)
            }
            .overlay(alignment: .top) {
                BenchFlowTopBar(
                    title: title,
                    palette: palette,
                    showsBackButton: showsBackButton,
                    showsThemeButton: showsThemeButton
                )
                .padding(.horizontal, 16)
                .padding(.top, -2)
            }
    }
}

extension Color {
    init(hex: UInt32, alpha: Double = 1) {
        let red = Double((hex >> 16) & 0xFF) / 255
        let green = Double((hex >> 8) & 0xFF) / 255
        let blue = Double(hex & 0xFF) / 255
        self.init(.sRGB, red: red, green: green, blue: blue, opacity: alpha)
    }
}

enum BenchFlowAppearance {
    static func apply() {
        let accent = UIColor(red: 0 / 255, green: 229 / 255, blue: 255 / 255, alpha: 1)
        let text = UIColor(red: 200 / 255, green: 216 / 255, blue: 232 / 255, alpha: 1)
        let muted = UIColor(red: 114 / 255, green: 135 / 255, blue: 157 / 255, alpha: 1)

        let navAppearance = UINavigationBarAppearance()
        navAppearance.configureWithTransparentBackground()
        navAppearance.backgroundEffect = nil
        navAppearance.backgroundColor = UIColor.clear
        navAppearance.shadowColor = UIColor.clear
        navAppearance.titleTextAttributes = [
            .foregroundColor: text,
            .font: UIFont.monospacedSystemFont(ofSize: 15, weight: .semibold)
        ]
        navAppearance.largeTitleTextAttributes = [
            .foregroundColor: text,
            .font: UIFont.systemFont(ofSize: 28, weight: .bold)
        ]

        UINavigationBar.appearance().standardAppearance = navAppearance
        UINavigationBar.appearance().scrollEdgeAppearance = navAppearance
        UINavigationBar.appearance().compactAppearance = navAppearance
        UINavigationBar.appearance().tintColor = accent

        let tabAppearance = UITabBarAppearance()
        tabAppearance.configureWithTransparentBackground()
        tabAppearance.backgroundEffect = nil
        tabAppearance.backgroundColor = UIColor.clear
        tabAppearance.shadowColor = UIColor.clear

        let stacked = tabAppearance.stackedLayoutAppearance
        stacked.selected.iconColor = accent
        stacked.selected.titleTextAttributes = [.foregroundColor: accent]
        stacked.normal.iconColor = muted
        stacked.normal.titleTextAttributes = [.foregroundColor: muted]
        stacked.selected.titlePositionAdjustment = UIOffset(horizontal: 0, vertical: -2)
        stacked.normal.titlePositionAdjustment = UIOffset(horizontal: 0, vertical: -2)
        stacked.selected.iconColor = accent
        stacked.normal.iconColor = muted

        UITabBar.appearance().standardAppearance = tabAppearance
        UITabBar.appearance().scrollEdgeAppearance = tabAppearance
        UITabBar.appearance().tintColor = accent
        UITabBar.appearance().unselectedItemTintColor = muted
        UITabBar.appearance().isTranslucent = true

        UITableView.appearance().backgroundColor = .clear
        UITableViewCell.appearance().backgroundColor = .clear
        UICollectionView.appearance().backgroundColor = .clear
    }
}
