import SwiftUI

struct CustomerDetailView: View {
    let apiClient: APIClient
    let customerID: Int
    @State private var viewModel: CustomerDetailViewModel

    init(apiClient: APIClient, customerID: Int) {
        self.apiClient = apiClient
        self.customerID = customerID
        _viewModel = State(initialValue: CustomerDetailViewModel(apiClient: apiClient, customerID: customerID))
    }

    var body: some View {
        List {
            if let response = viewModel.response {
                Section("Stammdaten") {
                    LabeledContent("Name", value: response.customer.name)
                    if !response.customer.company_name.isEmpty {
                        LabeledContent("Firma", value: response.customer.company_name)
                    }
                    LabeledContent("E-Mail", value: response.customer.email.isEmpty ? "-" : response.customer.email)
                    LabeledContent("Telefon", value: response.customer.phone.isEmpty ? "-" : response.customer.phone)
                    LabeledContent("Adresse", value: [response.customer.street, response.customer.postal_code, response.customer.city].filter { !$0.isEmpty }.joined(separator: ", "))
                    LabeledContent("Kontaktweg", value: response.customer.preferred_contact_label)
                    if !response.customer.customer_notes.isEmpty {
                        Text(response.customer.customer_notes)
                    }
                }

                Section("Auftragshistorie") {
                    ForEach(response.orders) { order in
                        NavigationLink {
                            OrderDetailView(apiClient: apiClient, orderID: order.id)
                        } label: {
                            VStack(alignment: .leading, spacing: 4) {
                                Text(order.order_number)
                                    .font(.headline)
                                Text(order.device_line)
                                    .foregroundStyle(.secondary)
                                Text("\(order.status) · \(order.intake_date)")
                                    .font(.footnote)
                                    .foregroundStyle(.secondary)
                            }
                            .padding(.vertical, 4)
                        }
                    }
                }
            } else if viewModel.isLoading {
                ProgressView("Kundendetail wird geladen ...")
            }
        }
        .navigationTitle(viewModel.response?.customer.name ?? "Kunde")
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
