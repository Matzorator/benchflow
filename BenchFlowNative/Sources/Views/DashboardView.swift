import SwiftUI

struct DashboardView: View {
    let apiClient: APIClient
    @State private var viewModel: DashboardViewModel

    init(apiClient: APIClient) {
        self.apiClient = apiClient
        _viewModel = State(initialValue: DashboardViewModel(apiClient: apiClient))
    }

    var body: some View {
        List {
            if let dashboard = viewModel.dashboard {
                Section {
                    LazyVGrid(columns: [GridItem(.adaptive(minimum: 150), spacing: 12)], spacing: 12) {
                        SummaryCard(title: "Offene Auftraege", value: "\(dashboard.active_order_count)", tint: .blue)
                        SummaryCard(title: "Offene KVAs", value: "\(dashboard.pending_quotes_count)", tint: .orange)
                        SummaryCard(title: "Unbezahlte Rechnungen", value: "\(dashboard.unpaid_invoices_count)", tint: .red)
                        SummaryCard(title: "Abholbereit", value: "\(dashboard.ready_count)", tint: .green)
                    }
                    .padding(.vertical, 8)
                }

                Section("Statusuebersicht") {
                    ForEach(dashboard.status_summary) { item in
                        HStack {
                            Text(item.status)
                            Spacer()
                            Text("\(item.total)")
                                .foregroundStyle(.secondary)
                        }
                    }
                }

                Section("Zuletzt bearbeitet") {
                    ForEach(dashboard.recent_orders) { order in
                        NavigationLink {
                            OrderDetailView(apiClient: apiClient, orderID: order.id)
                        } label: {
                            VStack(alignment: .leading, spacing: 6) {
                                Text(order.order_number)
                                    .font(.headline)
                                Text(order.customer_line)
                                    .font(.subheadline)
                                Text(order.device_line)
                                    .font(.subheadline)
                                    .foregroundStyle(.secondary)
                                HStack {
                                    Text(order.status)
                                    if !order.document_hint.isEmpty {
                                        Text("· \(order.document_hint)")
                                    }
                                }
                                .font(.footnote)
                                .foregroundStyle(.secondary)
                            }
                            .padding(.vertical, 4)
                        }
                    }
                }
            } else if viewModel.isLoading {
                ProgressView("Dashboard wird geladen ...")
                    .frame(maxWidth: .infinity, alignment: .center)
            }
        }
        .navigationTitle("Dashboard")
        .task { await viewModel.load() }
        .refreshable { await viewModel.load() }
        .alert("Fehler", isPresented: errorBinding) {
            Button("OK", role: .cancel) {}
        } message: {
            Text(viewModel.errorMessage ?? "")
        }
        .toastOverlay(viewModel.toast)
    }

    private var errorBinding: Binding<Bool> {
        Binding(
            get: { viewModel.errorMessage != nil },
            set: { if !$0 { viewModel.errorMessage = nil } }
        )
    }
}

private struct SummaryCard: View {
    let title: String
    let value: String
    let tint: Color

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(title)
                .font(.caption)
                .foregroundStyle(.secondary)
            Text(value)
                .font(.system(size: 28, weight: .bold, design: .rounded))
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding()
        .background(tint.opacity(0.12), in: RoundedRectangle(cornerRadius: 18, style: .continuous))
    }
}
