import SwiftUI

struct OrderListView: View {
    let apiClient: APIClient
    @State private var viewModel: OrdersViewModel

    init(apiClient: APIClient) {
        self.apiClient = apiClient
        _viewModel = State(initialValue: OrdersViewModel(apiClient: apiClient, archived: false))
    }

    var body: some View {
        @Bindable var bindable = viewModel

        List {
            filters(bindable: bindable)

            Section("Auftraege") {
                if viewModel.isLoading && viewModel.orders.isEmpty {
                    ProgressView("Auftraege werden geladen ...")
                } else {
                    ForEach(viewModel.orders) { order in
                        NavigationLink {
                            OrderDetailView(apiClient: apiClient, orderID: order.id)
                        } label: {
                            VStack(alignment: .leading, spacing: 6) {
                                HStack {
                                    Text(order.order_number)
                                        .font(.headline)
                                    Spacer()
                                    Text(order.status)
                                        .font(.footnote.weight(.semibold))
                                        .padding(.horizontal, 8)
                                        .padding(.vertical, 4)
                                        .background(.quaternary, in: Capsule())
                                }
                                Text(order.customer_line)
                                    .font(.subheadline)
                                Text(order.device_line)
                                    .font(.subheadline)
                                    .foregroundStyle(.secondary)
                                Text(order.document_hint.isEmpty ? order.intake_date : "\(order.intake_date) · \(order.document_hint)")
                                    .font(.footnote)
                                    .foregroundStyle(.secondary)
                            }
                            .padding(.vertical, 4)
                        }
                    }
                }
            }
        }
        .navigationTitle("Auftraege")
        .task { await viewModel.load() }
        .refreshable { await viewModel.load() }
        .searchable(text: $bindable.query, prompt: "Suche nach Auftrag, Kunde, Ort, Geraet")
        .onSubmit(of: .search) { Task { await viewModel.load() } }
        .alert("Fehler", isPresented: errorBinding) {
            Button("OK", role: .cancel) {}
        } message: {
            Text(viewModel.errorMessage ?? "")
        }
    }

    @ViewBuilder
    private func filters(bindable: Bindable<OrdersViewModel>) -> some View {
        Section("Filter") {
            Picker("Status", selection: bindable.selectedStatus) {
                Text("Alle").tag("")
                ForEach(viewModel.meta?.statuses ?? [], id: \.self) { status in
                    Text(status).tag(status)
                }
            }

            Picker("Kategorie", selection: bindable.selectedCategory) {
                Text("Alle").tag("")
                ForEach(viewModel.meta?.categories ?? []) { option in
                    Text(option.label).tag(option.value)
                }
            }

            Picker("Dokumenttyp", selection: bindable.selectedDocumentType) {
                Text("Alle").tag("")
                ForEach((viewModel.meta?.document_types ?? []).filter { !$0.value.isEmpty }) { option in
                    Text(option.label).tag(option.value)
                }
            }

            Button("Filter anwenden") {
                Task { await viewModel.load() }
            }
        }
    }

    private var errorBinding: Binding<Bool> {
        Binding(
            get: { viewModel.errorMessage != nil },
            set: { if !$0 { viewModel.errorMessage = nil } }
        )
    }
}
