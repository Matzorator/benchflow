import PhotosUI
import SwiftUI
import UniformTypeIdentifiers

struct OrderDetailView: View {
    let apiClient: APIClient
    let orderID: Int

    @Environment(\.openURL) private var openURL
    @State private var viewModel: OrderDetailViewModel
    @State private var browserURL: IdentifiableURL?
    @State private var photoItems: [PhotosPickerItem] = []
    @State private var showPDFImporter = false

    init(apiClient: APIClient, orderID: Int) {
        self.apiClient = apiClient
        self.orderID = orderID
        _viewModel = State(initialValue: OrderDetailViewModel(apiClient: apiClient, orderID: orderID))
    }

    var body: some View {
        @Bindable var bindable = viewModel

        List {
            if let order = viewModel.order, let orderDraft = viewModel.orderDraft {
                Section("Ueberblick") {
                    LabeledContent("Auftrag", value: order.order_number)
                    LabeledContent("Status", value: order.status)
                    LabeledContent("Annahme", value: order.intake_date)
                    LabeledContent("Erstellt", value: order.created_at)
                }

                Section("Kundenkontakt") {
                    TextField("Name", text: binding(\.customer.name))
                    TextField("Firma", text: binding(\.customer.company_name))
                    TextField("E-Mail", text: binding(\.customer.email))
                    TextField("Telefon", text: binding(\.customer.phone))
                    TextField("Strasse", text: binding(\.customer.street))
                    TextField("PLZ", text: binding(\.customer.postal_code))
                    TextField("Ort", text: binding(\.customer.city))
                    Picker("Kontaktweg", selection: binding(\.customer.preferred_contact)) {
                        ForEach(viewModel.meta?.preferred_contact_options ?? []) { option in
                            Text(option.label).tag(option.value)
                        }
                    }
                    TextField("Kundennotiz", text: binding(\.customer.customer_notes), axis: .vertical)

                    NavigationLink("Kundendetail oeffnen") {
                        CustomerDetailView(apiClient: apiClient, customerID: order.customer.id)
                    }
                }

                Section("Annahme / Fehlerbild") {
                    Picker("Status", selection: binding(\.status).withDefault(orderDraft.status ?? order.status)) {
                        ForEach(viewModel.meta?.statuses ?? [], id: \.self) { status in
                            Text(status).tag(status)
                        }
                    }
                    Picker("Technik", selection: binding(\.technician)) {
                        ForEach(viewModel.meta?.technicians ?? [], id: \.self) { technician in
                            Text(technician).tag(technician)
                        }
                    }
                    DateField(title: "Annahme", value: binding(\.intake_date))
                    TextField("Fehlerbild", text: binding(\.issue_description), axis: .vertical)
                    Picker("Garantie", selection: binding(\.warranty_status)) {
                        ForEach(viewModel.meta?.warranty_options ?? []) { option in
                            Text(option.label).tag(option.value)
                        }
                    }
                    Picker("KVA noetig", selection: binding(\.quote_required)) {
                        ForEach(viewModel.meta?.quote_options ?? []) { option in
                            Text(option.label).tag(option.value)
                        }
                    }
                }

                Section("Werkstattbearbeitung") {
                    Picker("Diagnosequelle", selection: binding(\.diagnostic_source)) {
                        ForEach(viewModel.meta?.diagnostic_sources ?? [], id: \.self) { source in
                            Text(source).tag(source)
                        }
                    }
                    Picker("Kategorie", selection: binding(\.device.category)) {
                        ForEach(viewModel.meta?.categories ?? []) { option in
                            Text(option.label).tag(option.value)
                        }
                    }
                    TextField("Hersteller", text: binding(\.device.manufacturer))
                    TextField("Modell", text: binding(\.device.model))
                    TextField("Seriennummer", text: binding(\.device.serial_number))
                    TextField("Zubehoer", text: binding(\.device.accessories))
                    TextField("Zustand", text: binding(\.device.condition_notes), axis: .vertical)
                    TextField("Interne Notizen", text: binding(\.internal_notes), axis: .vertical)
                    Button("Auftragsdaten speichern") {
                        Task { await viewModel.saveOrder() }
                    }
                    .disabled(viewModel.isSaving)
                }

                Section("KVA") {
                    TextField("Titel", text: $bindable.quoteDraft.title)
                    TextField("Arbeitsumfang", text: $bindable.quoteDraft.work_description, axis: .vertical)
                    TextField("Teile / Fremdleistung", text: $bindable.quoteDraft.parts_description, axis: .vertical)
                    TextField("Arbeitskosten (Cent)", value: $bindable.quoteDraft.labor_cost_cents, format: .number)
                    TextField("Teilekosten (Cent)", value: $bindable.quoteDraft.parts_cost_cents, format: .number)
                    TextField("Fremdleistung (Cent)", value: $bindable.quoteDraft.external_cost_cents, format: .number)
                    TextField("Versand (Cent)", value: $bindable.quoteDraft.shipping_cost_cents, format: .number)
                    DateField(title: "Gueltig bis", value: $bindable.quoteDraft.valid_until)
                    Picker("Freigabestatus", selection: $bindable.quoteDraft.approval_status) {
                        ForEach(viewModel.meta?.quote_approval_options ?? []) { option in
                            Text(option.label).tag(option.value)
                        }
                    }
                    TextField("Kundennachricht", text: $bindable.quoteDraft.customer_message, axis: .vertical)

                    HStack {
                        Button("KVA speichern") {
                            Task { await viewModel.saveQuote() }
                        }
                        if let pdfURL = order.quote?.pdf_url.flatMap(URL.init(string:)) {
                            Button("PDF oeffnen") {
                                browserURL = IdentifiableURL(url: pdfURL)
                            }
                        }
                        Button("Mail vorbereiten") {
                            Task {
                                await viewModel.prepareQuoteEmail()
                                if let mailtoURL = viewModel.mailtoURL {
                                    openURL(mailtoURL)
                                }
                            }
                        }
                    }
                }

                Section("Rechnung") {
                    TextField("Titel", text: $bindable.invoiceDraft.title)
                    TextField("Leistung", text: $bindable.invoiceDraft.labor_description, axis: .vertical)
                    TextField("Teile", text: $bindable.invoiceDraft.parts_description, axis: .vertical)
                    TextField("Arbeitskosten (Cent)", value: $bindable.invoiceDraft.labor_cost_cents, format: .number)
                    TextField("Teilekosten (Cent)", value: $bindable.invoiceDraft.parts_cost_cents, format: .number)
                    TextField("Fremdleistung (Cent)", value: $bindable.invoiceDraft.external_cost_cents, format: .number)
                    TextField("Versand (Cent)", value: $bindable.invoiceDraft.shipping_cost_cents, format: .number)
                    DateField(title: "Rechnungsdatum", value: $bindable.invoiceDraft.invoice_date)
                    Picker("Zahlungsstatus", selection: $bindable.invoiceDraft.payment_status) {
                        ForEach(viewModel.meta?.invoice_payment_options ?? []) { option in
                            Text(option.label).tag(option.value)
                        }
                    }
                    TextField("Interne Notiz", text: $bindable.invoiceDraft.internal_note, axis: .vertical)

                    HStack {
                        Button("Rechnung speichern") {
                            Task { await viewModel.saveInvoice() }
                        }
                        if let pdfURL = order.invoice?.pdf_url.flatMap(URL.init(string:)) {
                            Button("PDF oeffnen") {
                                browserURL = IdentifiableURL(url: pdfURL)
                            }
                        }
                    }
                }

                Section("Anhaenge") {
                    Picker("Dokumenttyp", selection: $bindable.selectedDocumentType) {
                        ForEach((viewModel.meta?.document_types ?? []).filter { !$0.value.isEmpty }) { option in
                            Text(option.label).tag(option.value)
                        }
                    }
                    TextField("Bezug zum Auftrag", text: $bindable.selectedDocumentContext)

                    PhotosPicker(selection: $photoItems, matching: .images) {
                        Label("Fotos hochladen", systemImage: "photo.on.rectangle")
                    }

                    Button("PDF hochladen") {
                        showPDFImporter = true
                    }

                    if let attachments = order.attachments {
                        ForEach(attachments) { attachment in
                            VStack(alignment: .leading, spacing: 6) {
                                Text(attachment.display_name)
                                    .font(.headline)
                                Text(attachment.document_type_label)
                                    .font(.subheadline)
                                    .foregroundStyle(.secondary)
                                if !attachment.order_context.isEmpty {
                                    Text(attachment.order_context)
                                        .font(.footnote)
                                }
                                HStack {
                                    if let fileURL = attachment.file_url.flatMap(URL.init(string:)) {
                                        Button(attachment.is_image ? "Bild oeffnen" : "Dokument oeffnen") {
                                            browserURL = IdentifiableURL(url: fileURL)
                                        }
                                    }
                                    Button("Loeschen", role: .destructive) {
                                        Task { await viewModel.deleteAttachment(attachment) }
                                    }
                                }
                                .font(.footnote)
                            }
                            .padding(.vertical, 4)
                        }
                    }
                }

                Section("Statushistorie") {
                    ForEach(order.status_history ?? []) { entry in
                        VStack(alignment: .leading, spacing: 4) {
                            Text(entry.status)
                                .font(.headline)
                            Text(entry.changed_at)
                                .font(.footnote)
                                .foregroundStyle(.secondary)
                            if !entry.note.isEmpty {
                                Text(entry.note)
                                    .font(.subheadline)
                            }
                        }
                        .padding(.vertical, 4)
                    }
                }

                Section("Druck / Tools") {
                    if let printURL = URL(string: order.print_url) {
                        Button("Kundenbeleg") {
                            browserURL = IdentifiableURL(url: printURL)
                        }
                    }
                    if let internalURL = URL(string: order.internal_print_url) {
                        Button("Interner Beleg") {
                            browserURL = IdentifiableURL(url: internalURL)
                        }
                    }
                    AsyncImage(url: URL(string: order.qr_url)) { image in
                        image.resizable().scaledToFit()
                    } placeholder: {
                        ProgressView()
                    }
                    .frame(maxWidth: 180, maxHeight: 180)
                }

                Section {
                    if order.archived_at == nil {
                        Button("Archivieren", role: .destructive) {
                            Task { await viewModel.archive() }
                        }
                    } else {
                        Button("Aus Archiv holen") {
                            Task { await viewModel.restore() }
                        }
                    }
                }
            } else if viewModel.isLoading {
                ProgressView("Auftrag wird geladen ...")
            }
        }
        .navigationTitle(viewModel.order?.order_number ?? "Auftrag")
        .task { await viewModel.load() }
        .refreshable { await viewModel.load() }
        .sheet(item: $browserURL) { item in
            BrowserSheet(url: item.url)
        }
        .fileImporter(
            isPresented: $showPDFImporter,
            allowedContentTypes: [.pdf],
            allowsMultipleSelection: true
        ) { result in
            Task { await handleDocumentImport(result) }
        }
        .onChange(of: photoItems) { _, newItems in
            Task { await handlePhotoSelection(newItems) }
        }
        .alert("Fehler", isPresented: errorBinding) {
            Button("OK", role: .cancel) {}
        } message: {
            Text(viewModel.errorMessage ?? "")
        }
        .toastOverlay(viewModel.toast)
    }

    private func binding<Value>(_ keyPath: WritableKeyPath<OrderMutationRequest, Value>) -> Binding<Value> {
        Binding(
            get: { viewModel.orderDraft?[keyPath: keyPath] ?? fallbackValue(for: keyPath) },
            set: { viewModel.orderDraft?[keyPath: keyPath] = $0 }
        )
    }

    private func fallbackValue<Value>(for keyPath: WritableKeyPath<OrderMutationRequest, Value>) -> Value {
        OrderMutationRequest(
            customer: CustomerDraft(),
            device: DeviceDraft(),
            issue_description: "",
            technician: "",
            intake_date: "",
            warranty_status: "",
            quote_required: "",
            diagnostic_source: "",
            internal_notes: "",
            status: nil
        )[keyPath: keyPath]
    }

    private var errorBinding: Binding<Bool> {
        Binding(
            get: { viewModel.errorMessage != nil },
            set: { if !$0 { viewModel.errorMessage = nil } }
        )
    }

    private func handlePhotoSelection(_ items: [PhotosPickerItem]) async {
        var files: [UploadableFile] = []
        for (index, item) in items.enumerated() {
            if let data = try? await item.loadTransferable(type: Data.self) {
                files.append(
                    UploadableFile(
                        filename: "photo-\(index + 1).jpg",
                        mime_type: "image/jpeg",
                        data: data
                    )
                )
            }
        }
        photoItems = []
        await viewModel.uploadAttachments(files)
    }

    private func handleDocumentImport(_ result: Result<[URL], Error>) async {
        guard case let .success(urls) = result else { return }
        let files = urls.compactMap { url -> UploadableFile? in
            guard let data = try? Data(contentsOf: url) else { return nil }
            return UploadableFile(filename: url.lastPathComponent, mime_type: "application/pdf", data: data)
        }
        await viewModel.uploadAttachments(files)
    }
}

private extension Binding where Value == String? {
    func withDefault(_ defaultValue: String) -> Binding<String> {
        Binding<String>(
            get: { wrappedValue ?? defaultValue },
            set: { wrappedValue = $0 }
        )
    }
}
