import SwiftUI

struct ArchiveView: View {
    let apiClient: APIClient
    @State private var viewModel: OrdersViewModel

    init(apiClient: APIClient) {
        self.apiClient = apiClient
        _viewModel = State(initialValue: OrdersViewModel(apiClient: apiClient, archived: true))
    }

    var body: some View {
        @Bindable var bindable = viewModel

        List {
            Section("Filter") {
                Picker("Status", selection: bindable.selectedStatus) {
                    Text("Alle").tag("")
                    ForEach(viewModel.meta?.statuses ?? [], id: \.self) { status in
                        Text(status).tag(status)
                    }
                }
                TextField("Suche", text: $bindable.query)
                Button("Archiv laden") {
                    Task { await viewModel.load() }
                }
            }

            Section("Archivierte Auftraege") {
                ForEach(viewModel.orders) { order in
                    NavigationLink {
                        OrderDetailView(apiClient: apiClient, orderID: order.id)
                    } label: {
                        VStack(alignment: .leading, spacing: 6) {
                            Text(order.order_number)
                                .font(.headline)
                            Text(order.customer_line)
                            Text(order.status)
                                .font(.footnote)
                                .foregroundStyle(.secondary)
                        }
                        .padding(.vertical, 4)
                    }
                }
            }
        }
        .navigationTitle("Archiv")
        .task { await viewModel.load() }
        .refreshable { await viewModel.load() }
        .alert("Fehler", isPresented: errorBinding) {
            Button("OK", role: .cancel) {}
        } message: {
            Text(viewModel.errorMessage ?? "")
        }
    }

    private var errorBinding: Binding<Bool> {
        Binding(
            get: { viewModel.errorMessage != nil },
            set: { if !$0 { viewModel.errorMessage = nil } }
        )
    }
}
