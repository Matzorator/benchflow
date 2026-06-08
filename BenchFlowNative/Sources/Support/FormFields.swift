import SwiftUI

struct DateField: View {
    let title: String
    @Binding var value: String

    var body: some View {
        TextField(title, text: $value)
            .font(.body.monospaced())
    }
}

struct BenchFlowFieldLabel: View {
    let title: String
    let palette: BenchFlowPalette

    var body: some View {
        Text(title)
            .font(.system(size: 15, weight: .semibold))
            .foregroundStyle(palette.text)
    }
}

private struct BenchFlowInputModifier: ViewModifier {
    let palette: BenchFlowPalette

    func body(content: Content) -> some View {
        content
            .padding(.horizontal, 12)
            .padding(.vertical, 11)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(
                RoundedRectangle(cornerRadius: 14, style: .continuous)
                    .fill(palette.panelStrong)
            )
            .overlay(
                RoundedRectangle(cornerRadius: 14, style: .continuous)
                    .stroke(palette.line, lineWidth: 1)
            )
    }
}

extension View {
    func benchFlowInput(palette: BenchFlowPalette) -> some View {
        modifier(BenchFlowInputModifier(palette: palette))
    }

    func benchFlowMenuPicker(palette: BenchFlowPalette) -> some View {
        self
            .font(.system(size: 14, weight: .medium))
            .pickerStyle(.menu)
            .benchFlowInput(palette: palette)
    }
}
