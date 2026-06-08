import SwiftUI

struct ToastState: Equatable, Sendable {
    var title: String
    var message: String
}

struct ToastModifier: ViewModifier {
    let toast: ToastState?

    func body(content: Content) -> some View {
        content
            .overlay(alignment: .topTrailing) {
                if let toast {
                    VStack(alignment: .leading, spacing: 6) {
                        Text(toast.title)
                            .font(.headline)
                        Text(toast.message)
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                    }
                    .padding(14)
                    .frame(maxWidth: 320, alignment: .leading)
                    .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 18, style: .continuous))
                    .padding()
                    .transition(.move(edge: .top).combined(with: .opacity))
                }
            }
            .animation(.easeInOut(duration: 0.2), value: toast)
    }
}

extension View {
    func toastOverlay(_ toast: ToastState?) -> some View {
        modifier(ToastModifier(toast: toast))
    }
}
