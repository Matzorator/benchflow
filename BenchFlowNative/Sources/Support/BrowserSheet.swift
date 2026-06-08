import SwiftUI

struct IdentifiableURL: Identifiable, Equatable {
    let id = UUID()
    let url: URL
}

#if os(iOS)
import SafariServices

struct BrowserSheet: UIViewControllerRepresentable {
    let url: URL

    func makeUIViewController(context: Context) -> SFSafariViewController {
        SFSafariViewController(url: url)
    }

    func updateUIViewController(_ uiViewController: SFSafariViewController, context: Context) {
    }
}
#else
struct BrowserSheet: View {
    let url: URL
    @Environment(\.openURL) private var openURL

    var body: some View {
        VStack(spacing: 16) {
            Text(url.absoluteString)
                .font(.footnote.monospaced())
                .multilineTextAlignment(.center)
            Button("Im Browser oeffnen") {
                openURL(url)
            }
        }
        .padding(32)
        .frame(minWidth: 420, minHeight: 180)
    }
}
#endif
