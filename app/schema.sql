CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    company_name TEXT NOT NULL DEFAULT '',
    email TEXT NOT NULL DEFAULT '',
    phone TEXT NOT NULL DEFAULT '',
    street TEXT NOT NULL DEFAULT '',
    postal_code TEXT NOT NULL DEFAULT '',
    city TEXT NOT NULL DEFAULT '',
    preferred_contact TEXT NOT NULL DEFAULT '',
    customer_notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL DEFAULT 'sonstiges',
    manufacturer TEXT NOT NULL DEFAULT '',
    model TEXT NOT NULL,
    serial_number TEXT NOT NULL DEFAULT '',
    accessories TEXT NOT NULL DEFAULT '',
    condition_notes TEXT NOT NULL DEFAULT '',
    image_data TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS service_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number TEXT NOT NULL UNIQUE,
    customer_id INTEGER NOT NULL,
    device_id INTEGER NOT NULL,
    issue_description TEXT NOT NULL,
    status TEXT NOT NULL,
    technician TEXT NOT NULL,
    intake_date TEXT NOT NULL,
    warranty_status TEXT NOT NULL DEFAULT 'unbekannt',
    quote_required TEXT NOT NULL DEFAULT 'nein',
    diagnostic_source TEXT NOT NULL DEFAULT 'Werkbank',
    internal_notes TEXT NOT NULL DEFAULT '',
    archived_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers (id),
    FOREIGN KEY (device_id) REFERENCES devices (id)
);

CREATE TABLE IF NOT EXISTS service_order_status_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_order_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    note TEXT NOT NULL DEFAULT '',
    changed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (service_order_id) REFERENCES service_orders (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS service_order_media (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_order_id INTEGER NOT NULL,
    filename TEXT NOT NULL DEFAULT '',
    mime_type TEXT NOT NULL DEFAULT '',
    document_type TEXT NOT NULL DEFAULT '',
    order_context TEXT NOT NULL DEFAULT '',
    media_data TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (service_order_id) REFERENCES service_orders (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS service_order_quotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_order_id INTEGER NOT NULL UNIQUE,
    quote_number TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL DEFAULT '',
    work_description TEXT NOT NULL DEFAULT '',
    parts_description TEXT NOT NULL DEFAULT '',
    labor_cost_cents INTEGER NOT NULL DEFAULT 0,
    parts_cost_cents INTEGER NOT NULL DEFAULT 0,
    external_cost_cents INTEGER NOT NULL DEFAULT 0,
    shipping_cost_cents INTEGER NOT NULL DEFAULT 0,
    total_cost_cents INTEGER NOT NULL DEFAULT 0,
    valid_until TEXT NOT NULL DEFAULT '',
    customer_message TEXT NOT NULL DEFAULT '',
    approval_status TEXT NOT NULL DEFAULT 'offen',
    pdf_media_id INTEGER,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (service_order_id) REFERENCES service_orders (id) ON DELETE CASCADE,
    FOREIGN KEY (pdf_media_id) REFERENCES service_order_media (id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS service_order_invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_order_id INTEGER NOT NULL UNIQUE,
    invoice_number TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL DEFAULT '',
    labor_description TEXT NOT NULL DEFAULT '',
    parts_description TEXT NOT NULL DEFAULT '',
    labor_cost_cents INTEGER NOT NULL DEFAULT 0,
    parts_cost_cents INTEGER NOT NULL DEFAULT 0,
    external_cost_cents INTEGER NOT NULL DEFAULT 0,
    shipping_cost_cents INTEGER NOT NULL DEFAULT 0,
    total_cost_cents INTEGER NOT NULL DEFAULT 0,
    invoice_date TEXT NOT NULL DEFAULT '',
    payment_status TEXT NOT NULL DEFAULT 'offen',
    internal_note TEXT NOT NULL DEFAULT '',
    pdf_media_id INTEGER,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (service_order_id) REFERENCES service_orders (id) ON DELETE CASCADE,
    FOREIGN KEY (pdf_media_id) REFERENCES service_order_media (id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_service_orders_status ON service_orders(status);
CREATE INDEX IF NOT EXISTS idx_service_orders_customer_id ON service_orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_service_orders_device_id ON service_orders(device_id);
CREATE INDEX IF NOT EXISTS idx_devices_category ON devices(category);
CREATE INDEX IF NOT EXISTS idx_status_history_order_id ON service_order_status_history(service_order_id);
CREATE INDEX IF NOT EXISTS idx_order_media_order_id ON service_order_media(service_order_id);
CREATE INDEX IF NOT EXISTS idx_quotes_order_id ON service_order_quotes(service_order_id);
CREATE INDEX IF NOT EXISTS idx_invoices_order_id ON service_order_invoices(service_order_id);
