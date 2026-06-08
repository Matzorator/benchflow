import SwiftUI

struct NewOrderView: View {
    let apiClient: APIClient
    @State private var viewModel: NewOrderViewModel

    init(apiClient: APIClient) {
        self.apiClient = apiClient
        _viewModel = State(initialValue: NewOrderViewModel(apiClient: apiClient))
    }

    var body: some View {
        @Bindable var bindable = viewModel

        Form {
            Section("Bestehenden Kunden suchen") {
                ForEach(viewModel.customerCandidates.prefix(10)) { customer in
                    Button {
                        viewModel.applyCustomer(customer)
                    } label: {
                        VStack(alignment: .leading, spacing: 4) {
                            Text([customer.name, customer.company_name].filter { !$0.isEmpty }.joined(separator: " | "))
                            Text([customer.phone, customer.email].filter { !$0.isEmpty }.joined(separator: " | "))
                                .font(.footnote)
                                .foregroundStyle(.secondary)
                        }
                    }
                    .buttonStyle(.plain)
                }
            }

            Section("Kunde") {
                TextField("Name", text: $bindable.draft.customer.name)
                TextField("Firma", text: $bindable.draft.customer.company_name)
                TextField("E-Mail", text: $bindable.draft.customer.email)
                    .textInputAutocapitalization(.never)
                    .keyboardType(.emailAddress)
                TextField("Telefon", text: $bindable.draft.customer.phone)
                TextField("Strasse", text: $bindable.draft.customer.street)
                TextField("PLZ", text: $bindable.draft.customer.postal_code)
                TextField("Ort", text: $bindable.draft.customer.city)
                Picker("Bevorzugter Kontakt", selection: $bindable.draft.customer.preferred_contact) {
                    ForEach(viewModel.meta?.preferred_contact_options ?? []) { option in
                        Text(option.label).tag(option.value)
                    }
                }
                TextField("Interne Kundennotiz", text: $bindable.draft.customer.customer_notes, axis: .vertical)
            }

            Section("Geraet") {
                Picker("Kategorie", selection: $bindable.draft.device.category) {
                    Text("Bitte waehlen").tag("")
                    ForEach(viewModel.meta?.categories ?? []) { option in
                        Text(option.label).tag(option.value)
                    }
                }
                TextField("Hersteller", text: $bindable.draft.device.manufacturer)
                TextField("Modell", text: $bindable.draft.device.model)
                TextField("Seriennummer", text: $bindable.draft.device.serial_number)
                TextField("Zubehoer", text: $bindable.draft.device.accessories)
                TextField("Zustand", text: $bindable.draft.device.condition_notes, axis: .vertical)
            }

            Section("Auftrag") {
                TextField("Fehlerbild", text: $bindable.draft.issue_description, axis: .vertical)
                Picker("Technik", selection: $bindable.draft.technician) {
                    ForEach(viewModel.meta?.technicians ?? [], id: \.self) { technician in
                        Text(technician).tag(technician)
                    }
                }
                DateField(title: "Annahme", value: $bindable.draft.intake_date)
                Picker("Garantie", selection: $bindable.draft.warranty_status) {
                    ForEach(viewModel.meta?.warranty_options ?? []) { option in
                        Text(option.label).tag(option.value)
                    }
                }
                Picker("KVA noetig", selection: $bindable.draft.quote_required) {
                    ForEach(viewModel.meta?.quote_options ?? []) { option in
                        Text(option.label).tag(option.value)
                    }
                }
                Picker("Diagnosequelle", selection: $bindable.draft.diagnostic_source) {
                    ForEach(viewModel.meta?.diagnostic_sources ?? [], id: \.self) { source in
                        Text(source).tag(source)
                    }
                }
                TextField("Interne Notizen", text: $bindable.draft.internal_notes, axis: .vertical)
            }

            Section {
                Button {
                    Task {
                        _ = await viewModel.submit()
                    }
                } label: {
                    if viewModel.isSubmitting {
                        ProgressView()
                    } else {
                        Text("Auftrag anlegen")
                    }
                }
                .disabled(viewModel.isSubmitting)
            }
        }
        .navigationTitle("Neuer Auftrag")
        .task { await viewModel.load() }
        .navigationDestination(item: createdOrderBinding) { order in
            OrderDetailView(apiClient: apiClient, orderID: order.id)
        }
        .alert("Fehler", isPresented: errorBinding) {
            Button("OK", role: .cancel) {}
        } message: {
            Text(viewModel.errorMessage ?? "")
        }
        .toastOverlay(viewModel.toast)
    }

    private var createdOrderBinding: Binding<ServiceOrder?> {
        Binding(
            get: { viewModel.createdOrder },
            set: { if $0 == nil { viewModel.createdOrder = nil } }
        )
    }

    private var errorBinding: Binding<Bool> {
        Binding(
            get: { viewModel.errorMessage != nil },
            set: { if !$0 { viewModel.errorMessage = nil } }
        )
    }
}

private struct DateField: View {
    let title: String
    @Binding var value: String

    var body: some View {
        TextField(title, text: $value)
            .font(.body.monospaced())
    }
}
