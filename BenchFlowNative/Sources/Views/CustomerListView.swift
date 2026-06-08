import SwiftUI

struct CustomerListView: View {
    let apiClient: APIClient
    @State private var viewModel: CustomerListViewModel

    init(apiClient: APIClient) {
        self.apiClient = apiClient
        _viewModel = State(initialValue: CustomerListViewModel(apiClient: apiClient))
    }

    var body: some View {
        @Bindable var bindable = viewModel

        List {
            Section("Filter") {
                Picker("Umfang", selection: $bindable.scope) {
                    Text("Aktiv").tag("active")
                    Text("Alle").tag("all")
                }
                TextField("Suche", text: $bindable.query)
                Button("Kunden laden") {
                    Task { await viewModel.load() }
                }
            }

            Section("Kunden") {
                ForEach(viewModel.customers) { customer in
                    NavigationLink {
                        CustomerDetailView(apiClient: apiClient, customerID: customer.id)
                    } label: {
                        VStack(alignment: .leading, spacing: 6) {
                            Text([customer.name, customer.company_name].filter { !$0.isEmpty }.joined(separator: " · "))
                                .font(.headline)
                            Text([customer.location_label, customer.email, customer.phone].filter { !$0.isEmpty }.joined(separator: " · "))
                                .font(.subheadline)
                                .foregroundStyle(.secondary)
                            if let active = customer.active_order_count {
                                Text("\(active) offen")
                                    .font(.footnote)
                                    .foregroundStyle(.secondary)
                            }
                        }
                        .padding(.vertical, 4)
                    }
                }
            }
        }
        .navigationTitle("Kunden")
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
