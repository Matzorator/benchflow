import { useCallback, useEffect, useMemo, useState } from 'react'
import './App.css'

const navItems = [
  { id: 'dashboard', label: 'Dashboard' },
  { id: 'orders', label: 'Auftraege' },
  { id: 'new-order', label: 'Neuer Auftrag' },
  { id: 'customers', label: 'Kunden' },
  { id: 'archive', label: 'Archiv' },
]

const emptyOrderForm = {
  customer: {
    name: '',
    company_name: '',
    email: '',
    phone: '',
    street: '',
    postal_code: '',
    city: '',
    preferred_contact: 'telefon',
    customer_notes: '',
  },
  device: {
    category: '',
    manufacturer: '',
    model: '',
    serial_number: '',
    accessories: '',
    condition_notes: '',
  },
  issue_description: '',
  technician: '',
  intake_date: new Date().toISOString().slice(0, 10),
  warranty_status: 'unbekannt',
  quote_required: 'nein',
  diagnostic_source: 'Werkbank',
}

function buildQuery(params) {
  const query = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && `${value}`.trim()) {
      query.set(key, value)
    }
  })
  const queryString = query.toString()
  return queryString ? `?${queryString}` : ''
}

async function requestJson(path, options = {}) {
  const response = await fetch(path, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  })
  const payload = await response.json().catch(() => ({}))
  if (!response.ok) {
    const error = new Error(payload.error || 'Die API-Anfrage ist fehlgeschlagen.')
    error.payload = payload
    throw error
  }
  return payload
}

function formatDate(value) {
  if (!value) return 'Ohne Datum'
  return value.slice(0, 10)
}

function compactDevice(device) {
  if (!device) return 'Kein Geraet'
  return [device.manufacturer, device.model].filter(Boolean).join(' ') || device.category || 'Geraet'
}

function statusClass(status = '') {
  const normalized = status.toLowerCase()
  if (normalized.includes('fertig') || normalized.includes('abholbereit')) return 'is-ready'
  if (normalized.includes('wartet')) return 'is-waiting'
  if (normalized.includes('abgeschlossen')) return 'is-done'
  return 'is-open'
}

function App() {
  const [view, setView] = useState({ name: 'dashboard' })
  const [meta, setMeta] = useState(null)
  const [theme, setTheme] = useState(() => localStorage.getItem('benchflow-theme') || 'dark')

  useEffect(() => {
    requestJson('/api/meta').then(setMeta).catch(console.error)
  }, [])

  useEffect(() => {
    document.documentElement.dataset.theme = theme
    localStorage.setItem('benchflow-theme', theme)
  }, [theme])

  const navigate = useCallback((name, params = {}) => {
    setView({ name, ...params })
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }, [])

  return (
    <main className="layout">
      <header className="app-nav">
        <button className="brand-mark reset-button" onClick={() => navigate('dashboard')} type="button" aria-label="BenchFlow Startseite">
          <img src="/Benchflow_Logo.png" alt="BenchFlow" className="brand-logo" />
        </button>
        <div className="nav-cluster">
          <nav className="nav-links" aria-label="Hauptnavigation">
            {navItems.map((item) => (
              <button
                className={view.name === item.id ? 'is-active' : ''}
                key={item.id}
                onClick={() => navigate(item.id)}
                type="button"
              >
                {item.label}
              </button>
            ))}
          </nav>
          <button
            type="button"
            className="theme-toggle ghost-button compact-button"
            data-theme-target={theme === 'light' ? 'dark' : 'light'}
            aria-pressed={theme === 'light'}
            onClick={() => setTheme((current) => (current === 'light' ? 'dark' : 'light'))}
          >
            {theme === 'light' ? 'Dark Mode' : 'Light Mode'}
          </button>
        </div>
      </header>

      <div className="react-workspace">
        {view.name === 'dashboard' && <Dashboard navigate={navigate} />}
        {view.name === 'orders' && <OrdersView meta={meta} navigate={navigate} archived={false} />}
        {view.name === 'archive' && <OrdersView meta={meta} navigate={navigate} archived />}
        {view.name === 'customers' && <CustomersView navigate={navigate} />}
        {view.name === 'customer-detail' && <CustomerDetail customerId={view.customerId} navigate={navigate} />}
        {view.name === 'order-detail' && <OrderDetail orderId={view.orderId} navigate={navigate} />}
        {view.name === 'new-order' && <NewOrderView meta={meta} navigate={navigate} />}
      </div>

      <footer className="site-footer">
        <div className="site-footer-copy">
          <strong>BenchFlow</strong>
          <p>React-Migrationsfassung mit Flask als API-Backend. Die bestehende Template-Oberflaeche bleibt parallel erhalten.</p>
        </div>
      </footer>
    </main>
  )
}

function PageHeader({ eyebrow, title, children }) {
  return (
    <header className="page-intro page-intro-wide react-page-header">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h1>{title}</h1>
      </div>
      {children ? <div className="header-actions">{children}</div> : null}
    </header>
  )
}

function LoadingPanel() {
  return <div className="detail-card state-panel">Daten werden geladen...</div>
}

function ErrorPanel({ error }) {
  return <div className="detail-card form-alert">{error.message}</div>
}

function Dashboard({ navigate }) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    requestJson('/api/dashboard').then(setData).catch(setError)
  }, [])

  if (error) return <ErrorPanel error={error} />
  if (!data) return <LoadingPanel />

  const metrics = [
    { label: 'Aktive Auftraege', value: data.active_order_count },
    { label: 'Wartende KVA', value: data.pending_quotes_count },
    { label: 'Offene Rechnungen', value: data.unpaid_invoices_count },
    { label: 'Archiviert', value: data.archived_count },
  ]

  return (
    <>
      <section className="hero">
        <div>
          <p className="eyebrow">Werkstatt- und Serviceverwaltung</p>
          <h1>BenchFlow</h1>
          <div className="hero-actions">
            <button className="ghost-button" onClick={() => navigate('orders')} type="button">Aktive Auftraege</button>
            <button className="primary-button" onClick={() => navigate('new-order')} type="button">Neuen Auftrag anlegen</button>
          </div>
        </div>
        <div className="hero-card">
          <span>Heute im Blick</span>
          <strong>{data.active_order_count} aktive Auftraege</strong>
          <p>{data.ready_count} bereit oder fertig | {data.blocked_count} blockiert</p>
          <p className="hero-meta">Archiv: {data.archived_count} Auftraege</p>
        </div>
      </section>

      <section className="summary-grid">
        {metrics.map((metric) => (
          <article className="summary-card" key={metric.label}>
            <span>{metric.label}</span>
            <strong>{metric.value}</strong>
          </article>
        ))}
      </section>

      <section className="dashboard-grid">
        <article className="detail-card">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Schnellzugriffe</p>
              <h2>Tagesstart</h2>
            </div>
          </div>
          <div className="action-stack">
            <button className="ghost-button" onClick={() => navigate('new-order')} type="button">Auftrag annehmen</button>
            <button className="ghost-button" onClick={() => navigate('orders')} type="button">Serviceboard oeffnen</button>
            <button className="ghost-button" onClick={() => navigate('archive')} type="button">Archiv durchsuchen</button>
          </div>
        </article>
        <article className="detail-card">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Arbeitslage</p>
              <h2>Kurzlage</h2>
            </div>
          </div>
          <div className="quick-stats">
            <article className="quick-stat"><span>Aktiv</span><strong>{data.active_order_count}</strong></article>
            <article className="quick-stat"><span>Bereit / Fertig</span><strong>{data.ready_count}</strong></article>
            <article className="quick-stat"><span>Blockiert</span><strong>{data.blocked_count}</strong></article>
          </div>
        </article>
        <article className="detail-card dashboard-wide">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Letzte Aktivitaet</p>
              <h2>Zuletzt bearbeitet</h2>
            </div>
          </div>
          <OrderList orders={data.recent_orders} navigate={navigate} compact />
        </article>
      </section>
    </>
  )
}

function OrdersView({ archived, meta, navigate }) {
  const [filters, setFilters] = useState({ q: '', status: '', category: '', document_type: '' })
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    let ignore = false
    requestJson(`/api/orders${buildQuery({ ...filters, archived: archived ? '1' : '' })}`)
      .then((payload) => {
        if (!ignore) {
          setData(payload)
          setError(null)
        }
      })
      .catch((err) => {
        if (!ignore) setError(err)
      })
    return () => {
      ignore = true
    }
  }, [archived, filters])

  const statusOptions = meta?.statuses || []
  const categoryOptions = meta?.categories || []
  const documentOptions = meta?.document_types || []

  return (
    <>
      <section className="page-intro">
        <div>
          <p className="eyebrow">{archived ? 'Historie' : 'Auftraege'}</p>
          <h1>{archived ? 'Archiv' : 'Aktive Auftraege'}</h1>
          <p className="lead">{archived ? 'Abgeschlossene und abgelegte Werkstattfaelle.' : 'Suche, Filter und aktive Werkstattfaelle liegen getrennt vom Dashboard.'}</p>
        </div>
        <div className="hero-card compact-card">
          <span>Sichtbar</span>
          <strong>{data?.order_count ?? '-'} Auftraege</strong>
          <p>{archived ? 'Archivansicht' : 'Archiv separat verfuegbar'}</p>
        </div>
      </section>
      <section className="filter-panel">
        <div className="filter-form">
          <label className="search-field">
            <span>Suche</span>
            <input
              aria-label="Suche"
              onChange={(event) => setFilters((current) => ({ ...current, q: event.target.value }))}
              placeholder="Auftragsnummer, Kunde, Hersteller, Modell, Seriennummer"
              value={filters.q}
            />
          </label>
          <label>
            <span>Status</span>
            <select onChange={(event) => setFilters((current) => ({ ...current, status: event.target.value }))} value={filters.status}>
              <option value="">Alle Status</option>
              {statusOptions.map((status) => <option key={status} value={status}>{status}</option>)}
            </select>
          </label>
          <label>
            <span>Kategorie</span>
            <select onChange={(event) => setFilters((current) => ({ ...current, category: event.target.value }))} value={filters.category}>
              <option value="">Alle Kategorien</option>
              {categoryOptions.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
            </select>
          </label>
          <label>
            <span>Dokumenttyp</span>
            <select onChange={(event) => setFilters((current) => ({ ...current, document_type: event.target.value }))} value={filters.document_type}>
              <option value="">Alle Dokumente</option>
              {documentOptions.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
            </select>
          </label>
        </div>
      </section>
      {error && <ErrorPanel error={error} />}
      {!data && !error && <LoadingPanel />}
      {data && (
        <>
          <OrderList orders={data.orders} navigate={navigate} />
        </>
      )}
    </>
  )
}

function OrderList({ orders, navigate, compact = false }) {
  if (!orders?.length) return <p className="empty-text">Keine passenden Auftraege gefunden.</p>

  return (
    <section className={compact ? 'recent-list' : 'orders-list'}>
      {!compact && (
        <div className="orders-list-head">
          <span>Status</span>
          <span>Auftrag</span>
          <span>Kunde</span>
          <span>Geraet</span>
          <span>Technik</span>
          <span>Annahme</span>
          <span>Aktionen</span>
        </div>
      )}
      {orders.map((order) => (
        compact ? (
          <button className="recent-item reset-button" key={order.id} onClick={() => navigate('order-detail', { orderId: order.id })} type="button">
            <div>
              <strong>{order.order_number}</strong>
              <p>{compactDevice(order.device)} fuer {order.customer?.company_name || order.customer?.name || 'Ohne Kunde'}</p>
              {order.document_hint && <small className="document-hint">{order.document_hint}</small>}
            </div>
            <span className="pill">{order.status}</span>
          </button>
        ) : (
        <article className={`order-row ${order.archived_at ? 'is-archived' : ''}`} key={order.id}>
          <div className="order-cell" data-label="Status">
            <span className={`pill ${statusClass(order.status)}`}>{order.status}</span>
            {order.archived_at && <small className="archive-note">Archiviert {formatDate(order.archived_at)}</small>}
          </div>
          <div className="order-cell" data-label="Auftrag">
            <strong className="order-primary">{order.order_number}</strong>
            <span className="order-secondary">{order.issue_description}</span>
            {order.document_hint && <small className="document-hint">{order.document_hint}</small>}
          </div>
          <div className="order-cell" data-label="Kunde">
            <strong className="order-primary">{order.customer?.company_name || order.customer?.name || '-'}</strong>
            <span className="order-secondary">{order.customer?.phone || '-'}</span>
          </div>
          <div className="order-cell" data-label="Geraet">
            <strong className="order-primary">{compactDevice(order.device)}</strong>
            <span className="order-secondary">{order.device?.category || '-'} | {order.device?.serial_number || 'ohne Seriennummer'}</span>
          </div>
          <div className="order-cell" data-label="Technik">
            <strong className="order-primary">{order.technician || '-'}</strong>
          </div>
          <div className="order-cell" data-label="Annahme">
            <strong className="order-primary">{formatDate(order.intake_date)}</strong>
          </div>
          <div className="order-cell order-actions" data-label="Aktionen">
            <button className="card-link reset-button" onClick={() => navigate('order-detail', { orderId: order.id })} type="button">Oeffnen</button>
          </div>
        </article>
        )
      ))}
    </section>
  )
}

function CustomersView({ navigate }) {
  const [filters, setFilters] = useState({ q: '', scope: 'active' })
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    let ignore = false
    requestJson(`/api/customers${buildQuery(filters)}`)
      .then((payload) => {
        if (!ignore) {
          setData(payload)
          setError(null)
        }
      })
      .catch((err) => {
        if (!ignore) setError(err)
      })
    return () => {
      ignore = true
    }
  }, [filters])

  return (
    <>
      <section className="page-intro">
        <div>
          <p className="eyebrow">Kunden</p>
          <h1>Kundenliste</h1>
          <p className="lead">Schneller Zugriff auf Bestandskunden, Kontaktinfos und laufende Werkstattvorgaenge.</p>
        </div>
        <div className="hero-card compact-card">
          <span>Sichtbar</span>
          <strong>{data?.customer_count ?? '-'} Kunden</strong>
          <p>{filters.scope === 'all' ? 'Mit und ohne aktive Vorgaenge' : 'Nur Kunden mit aktiven Vorgaengen'}</p>
        </div>
      </section>
      <section className="filter-panel">
        <div className="filter-form customer-filter-form">
          <label className="search-field">
            <span>Suche</span>
            <input
              aria-label="Kundensuche"
              onChange={(event) => setFilters((current) => ({ ...current, q: event.target.value }))}
              placeholder="Name, Firma, Telefon, E-Mail oder Ort"
              value={filters.q}
            />
          </label>
          <label>
            <span>Umfang</span>
            <select
              aria-label="Kundenumfang"
              onChange={(event) => setFilters((current) => ({ ...current, scope: event.target.value }))}
              value={filters.scope}
            >
              <option value="active">Nur aktive Kunden</option>
              <option value="all">Alle Kunden</option>
            </select>
          </label>
        </div>
      </section>
      {error && <ErrorPanel error={error} />}
      {!data && !error && <LoadingPanel />}
      {data && (
        <section className="customer-directory">
          <div className="customer-directory-head">
            <span>Kunde</span>
            <span>Kontakt</span>
            <span>Ort</span>
            <span>Vorgaenge</span>
            <span>Letzter Auftrag</span>
            <span>Aktionen</span>
          </div>
          {data.customers.map((customer) => (
            <article className="customer-row" key={customer.id}>
              <div className="customer-cell" data-label="Kunde">
                <strong className="order-primary">{customer.name}</strong>
                <span className="order-secondary">{customer.company_name || 'Privatkunde'}</span>
              </div>
              <div className="customer-cell" data-label="Kontakt">
                <strong className="order-primary">{customer.phone || '-'}</strong>
                <span className="order-secondary">{customer.email || customer.preferred_contact_label}</span>
              </div>
              <div className="customer-cell" data-label="Ort">
                <strong className="order-primary">{customer.location_label || '-'}</strong>
                <span className="order-secondary">{customer.street || 'Keine Adresse hinterlegt'}</span>
              </div>
              <div className="customer-cell" data-label="Vorgaenge">
                <strong className="order-primary">{customer.active_order_count || 0} offen</strong>
                <span className="order-secondary">{customer.order_count || 0} insgesamt</span>
              </div>
              <div className="customer-cell" data-label="Letzter Auftrag">
                <strong className="order-primary">{customer.latest_order_number || '-'}</strong>
                <span className="order-secondary">{customer.latest_order_status || 'Noch kein Auftrag'}</span>
              </div>
              <div className="customer-cell customer-actions" data-label="Aktionen">
                <button className="card-link reset-button" onClick={() => navigate('customer-detail', { customerId: customer.id })} type="button">Oeffnen</button>
              </div>
            </article>
          ))}
        </section>
      )}
    </>
  )
}

function CustomerDetail({ customerId, navigate }) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    requestJson(`/api/customers/${customerId}`).then(setData).catch(setError)
  }, [customerId])

  if (error) return <ErrorPanel error={error} />
  if (!data) return <LoadingPanel />

  const { customer } = data
  return (
    <>
      <PageHeader eyebrow="Kundendetail" title={customer.company_name || customer.name}>
        <button className="ghost-button compact-button" onClick={() => navigate('customers')} type="button">
          Zurueck
        </button>
      </PageHeader>
      <section className="dashboard-grid">
        <article className="detail-card details">
          <h2>Kontakt</h2>
          <dl>
            <dt>Name</dt>
            <dd>{customer.name}</dd>
            <dt>E-Mail</dt>
            <dd>{customer.email || '-'}</dd>
            <dt>Telefon</dt>
            <dd>{customer.phone || '-'}</dd>
            <dt>Adresse</dt>
            <dd>{[customer.street, customer.location_label].filter(Boolean).join(', ') || '-'}</dd>
          </dl>
        </article>
        <article className="detail-card">
          <h2>Auftraege</h2>
          <OrderList orders={data.orders} navigate={navigate} compact />
        </article>
      </section>
    </>
  )
}

function OrderDetail({ orderId }) {
  const [order, setOrder] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    requestJson(`/api/orders/${orderId}`).then(setOrder).catch(setError)
  }, [orderId])

  if (error) return <ErrorPanel error={error} />
  if (!order) return <LoadingPanel />

  return (
    <>
      <PageHeader eyebrow="Auftrag" title={order.order_number}>
        <a className="ghost-button compact-button" href={order.print_url} rel="noreferrer" target="_blank">
          Kundenbeleg
        </a>
        <a className="ghost-button compact-button" href={order.internal_print_url} rel="noreferrer" target="_blank">
          Intern
        </a>
      </PageHeader>
      <section className="dashboard-grid react-detail-grid">
        <article className="detail-card details">
          <h2>Ueberblick</h2>
          <dl>
            <dt>Status</dt>
            <dd><span className={`pill ${statusClass(order.status)}`}>{order.status}</span></dd>
            <dt>Kunde</dt>
            <dd>{order.customer?.company_name || order.customer?.name}</dd>
            <dt>Geraet</dt>
            <dd>{compactDevice(order.device)}</dd>
            <dt>Seriennummer</dt>
            <dd>{order.device?.serial_number || '-'}</dd>
            <dt>Annahme</dt>
            <dd>{formatDate(order.intake_date)}</dd>
          </dl>
        </article>
        <article className="detail-card">
          <h2>Fehlerangabe</h2>
          <p className="copy-block">{order.issue_description}</p>
          <h2>Interne Notizen</h2>
          <p className="copy-block">{order.internal_notes || 'Keine interne Notiz hinterlegt.'}</p>
        </article>
        <article className="detail-card">
          <h2>Dokumente</h2>
          <AttachmentList attachments={order.attachments || []} />
        </article>
        <article className="detail-card">
          <h2>KVA / Rechnung</h2>
          <DocumentStatus label="Kostenvoranschlag" item={order.quote} />
          <DocumentStatus label="Rechnung" item={order.invoice} />
        </article>
        <article className="detail-card dashboard-wide">
          <h2>Statusverlauf</h2>
          <div className="timeline">
            {(order.status_history || []).map((entry) => (
              <div key={entry.id}>
                <span>{formatDate(entry.changed_at)}</span>
                <strong>{entry.status}</strong>
                <p>{entry.note || 'Ohne Notiz'}</p>
              </div>
            ))}
          </div>
        </article>
      </section>
    </>
  )
}

function AttachmentList({ attachments }) {
  if (!attachments.length) return <p className="empty-text">Keine Anhaenge vorhanden.</p>
  return (
    <div className="attachment-list">
      {attachments.map((item) => (
        <a href={item.file_url || '#'} key={item.id} rel="noreferrer" target="_blank">
          <strong>{item.display_name}</strong>
          <span>{item.document_type_label || item.mime_type}</span>
        </a>
      ))}
    </div>
  )
}

function DocumentStatus({ label, item }) {
  if (!item) {
    return (
      <div className="document-status">
        <strong>{label}</strong>
        <span>Nicht angelegt</span>
      </div>
    )
  }
  return (
    <div className="document-status">
      <strong>{label}</strong>
      <span>{item.approval_status || item.payment_status || 'vorhanden'}</span>
      {item.pdf_url && (
        <a href={item.pdf_url} rel="noreferrer" target="_blank">
          PDF oeffnen
        </a>
      )}
    </div>
  )
}

function NewOrderView({ meta, navigate }) {
  const [form, setForm] = useState(emptyOrderForm)
  const [error, setError] = useState(null)
  const [saving, setSaving] = useState(false)

  const options = useMemo(() => ({
    categories: meta?.categories || [],
    warranty: meta?.warranty_options || [],
    quote: meta?.quote_options || [],
    contact: meta?.preferred_contact_options || [],
    technicians: meta?.technicians || [],
    diagnostics: meta?.diagnostic_sources || [],
  }), [meta])

  function updateSection(section, key, value) {
    setForm((current) => ({
      ...current,
      [section]: {
        ...current[section],
        [key]: value,
      },
    }))
  }

  function updateField(key, value) {
    setForm((current) => ({ ...current, [key]: value }))
  }

  async function submitOrder(event) {
    event.preventDefault()
    setSaving(true)
    setError(null)
    try {
      const created = await requestJson('/api/orders', {
        method: 'POST',
        body: JSON.stringify(form),
      })
      navigate('order-detail', { orderId: created.id })
    } catch (err) {
      setError(err)
    } finally {
      setSaving(false)
    }
  }

  return (
    <>
      <PageHeader eyebrow="Annahme" title="Neuer Auftrag" />
      {error && <ErrorPanel error={error} />}
      <form className="order-form intake-form" onSubmit={submitOrder}>
        <fieldset className="detail-card">
          <legend>Kunde</legend>
          <Input label="Name" value={form.customer.name} onChange={(value) => updateSection('customer', 'name', value)} required />
          <Input label="Firma" value={form.customer.company_name} onChange={(value) => updateSection('customer', 'company_name', value)} />
          <Input label="E-Mail" value={form.customer.email} onChange={(value) => updateSection('customer', 'email', value)} />
          <Input label="Telefon" value={form.customer.phone} onChange={(value) => updateSection('customer', 'phone', value)} />
          <Input label="Strasse" value={form.customer.street} onChange={(value) => updateSection('customer', 'street', value)} />
          <Input label="PLZ" value={form.customer.postal_code} onChange={(value) => updateSection('customer', 'postal_code', value)} />
          <Input label="Ort" value={form.customer.city} onChange={(value) => updateSection('customer', 'city', value)} />
          <Select label="Kontaktweg" options={options.contact} value={form.customer.preferred_contact} onChange={(value) => updateSection('customer', 'preferred_contact', value)} />
        </fieldset>
        <fieldset className="detail-card">
          <legend>Geraet</legend>
          <Select label="Kategorie" options={options.categories} value={form.device.category} onChange={(value) => updateSection('device', 'category', value)} required />
          <Input label="Hersteller" value={form.device.manufacturer} onChange={(value) => updateSection('device', 'manufacturer', value)} required />
          <Input label="Modell" value={form.device.model} onChange={(value) => updateSection('device', 'model', value)} required />
          <Input label="Seriennummer" value={form.device.serial_number} onChange={(value) => updateSection('device', 'serial_number', value)} />
          <Textarea label="Zubehoer" value={form.device.accessories} onChange={(value) => updateSection('device', 'accessories', value)} />
          <Textarea label="Zustand" value={form.device.condition_notes} onChange={(value) => updateSection('device', 'condition_notes', value)} />
        </fieldset>
        <fieldset className="detail-card dashboard-wide">
          <legend>Werkstatt</legend>
          <Textarea label="Fehlerangabe" value={form.issue_description} onChange={(value) => updateField('issue_description', value)} required />
          <Select label="Techniker" options={options.technicians.map((value) => ({ value, label: value }))} value={form.technician} onChange={(value) => updateField('technician', value)} required />
          <Input label="Annahmedatum" type="date" value={form.intake_date} onChange={(value) => updateField('intake_date', value)} required />
          <Select label="Garantie" options={options.warranty} value={form.warranty_status} onChange={(value) => updateField('warranty_status', value)} />
          <Select label="KVA" options={options.quote} value={form.quote_required} onChange={(value) => updateField('quote_required', value)} />
          <Select label="Diagnosequelle" options={options.diagnostics.map((value) => ({ value, label: value }))} value={form.diagnostic_source} onChange={(value) => updateField('diagnostic_source', value)} />
          <Textarea label="Interne Notizen" value={form.internal_notes} onChange={(value) => updateField('internal_notes', value)} />
          <button className="primary-button submit-button" disabled={saving} type="submit">
            {saving ? 'Speichern...' : 'Auftrag anlegen'}
          </button>
        </fieldset>
      </form>
    </>
  )
}

function Input({ label, value, onChange, type = 'text', required = false }) {
  return (
    <label className="field">
      <span>{label}</span>
      <input required={required} type={type} value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
  )
}

function Textarea({ label, value, onChange, required = false }) {
  return (
    <label className="field">
      <span>{label}</span>
      <textarea required={required} rows="4" value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
  )
}

function Select({ label, value, options, onChange, required = false }) {
  return (
    <label className="field">
      <span>{label}</span>
      <select required={required} value={value} onChange={(event) => onChange(event.target.value)}>
        <option value="">Bitte waehlen</option>
        {options.map((item) => (
          <option key={item.value} value={item.value}>
            {item.label}
          </option>
        ))}
      </select>
    </label>
  )
}

export default App
