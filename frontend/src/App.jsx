// frontend/src/App.jsx
import { useEffect, useMemo, useState } from 'react'

/** Basic fetch helpers for the FastAPI backend */
async function apiGet(path) {
  const res = await fetch(path)
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`HTTP ${res.status}${text ? ` — ${text.slice(0, 140)}` : ''}`)
  }
  return res.json()
}
async function apiPost(path) {
  const res = await fetch(path, { method: 'POST' })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`HTTP ${res.status}${text ? ` — ${text.slice(0, 140)}` : ''}`)
  }
  return res.json().catch(() => ({}))
}

/** Utils */
function ymd(d) {
  const yyyy = d.getFullYear()
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${yyyy}-${mm}-${dd}`
}
function toWednesday(d) {
  const copy = new Date(d)
  const delta = (3 - copy.getDay() + 7) % 7 // 3 = Wed
  copy.setDate(copy.getDate() + delta)
  return copy
}
function niceLabel(d) {
  return d.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' })
}
function wednesdayOptions(selected) {
  const base = toWednesday(selected ?? new Date())
  const out = []
  for (let i = -4; i <= 7; i++) {
    const d = new Date(base)
    d.setDate(d.getDate() + i * 7)
    out.push({ value: ymd(d), label: niceLabel(d) })
  }
  return out
}
const stripHtml = (html) =>
  typeof html === 'string' ? html.replace(/<[^>]*>/g, '').trim() : ''

export default function App() {
  const [q, setQ] = useState('')
  const [selectedWed, setSelectedWed] = useState(() => ymd(toWednesday(new Date())))
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState(null) // modal comic

  // pagination
  const [page, setPage] = useState(1)
  const ITEMS_PER_PAGE = 12
  const pageCount = Math.max(1, Math.ceil(results.length / ITEMS_PER_PAGE))
  const paginatedResults = useMemo(() => {
    const start = (page - 1) * ITEMS_PER_PAGE
    return results.slice(start, start + ITEMS_PER_PAGE)
  }, [results, page])

  const wedOptions = useMemo(() => wednesdayOptions(new Date(selectedWed)), [selectedWed])

  // Reset page to 1 any time the result set changes
  useEffect(() => { setPage(1) }, [results])

  useEffect(() => {
    let cancelled = false
    async function run() {
      setLoading(true)
      setError('')
      try {
        const data = await apiGet(`/api/comics/week?wed=${selectedWed}`)
        if (!cancelled) setResults(data || [])
      } catch (e) {
        if (!cancelled) setError(e.message || 'Failed to load comics')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    run()
    return () => { cancelled = true }
  }, [selectedWed])

  async function doSearch(ev) {
    ev?.preventDefault?.()
    setError('')
    setLoading(true)
    try {
      const term = q.trim()
      if (!term) {
        const data = await apiGet(`/api/comics/week?wed=${selectedWed}`)
        setResults(data || [])
        return
      }
      const data = await apiGet(`/api/comics/search?q=${encodeURIComponent(term)}`)
      setResults(data || [])
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
      setPage(1)
    }
  }

  async function syncCurrentMonth() {
    setError('')
    setLoading(true)
    try {
      const d = new Date(selectedWed)
      const start = new Date(d.getFullYear(), d.getMonth(), 1)
      const end = new Date(d.getFullYear(), d.getMonth() + 1, 0)
      const startStr = ymd(start)
      const endStr = ymd(end)

      // ComicVine sync
      const summary = await apiPost(`/api/cv/sync?start=${startStr}&end=${endStr}`)

      // Refresh week
      const week = await apiGet(`/api/comics/week?wed=${selectedWed}`)
      setResults(week || [])
      setPage(1)

      if (summary && (summary.inserted !== undefined || summary.updated !== undefined)) {
        alert(`Synced ${startStr}..${endStr}\nInserted: ${summary.inserted ?? 0}\nUpdated: ${summary.updated ?? 0}`)
      }
    } catch (e) {
      setError(e.message || 'Sync failed')
    } finally {
      setLoading(false)
    }
  }

  function openModal(c) {
    setActive(c)
    setOpen(true)
  }
  function closeModal() {
    setOpen(false)
    setActive(null)
  }

  return (
    <div style={{ fontFamily: 'system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif', padding: 20, maxWidth: 1100, margin: '0 auto' }}>
      <header style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap', marginBottom: 16 }}>
        <h1 style={{ fontSize: 22, margin: 0 }}>Comic Finder</h1>
        <span style={{ opacity: 0.6 }}>•</span>
        <span style={{ opacity: 0.8 }}>Backend: ComicVine</span>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
          <button
            onClick={syncCurrentMonth}
            style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid #ddd', background: '#f7f7f7', cursor: 'pointer' }}
            title="Pull covers & descriptions for this month"
          >
            Sync current month
          </button>
        </div>
      </header>

      {/* Controls */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 12 }}>
        {/* Search */}
        <form onSubmit={doSearch} style={{ display: 'flex', gap: 8 }}>
          <input
            type="text"
            placeholder="Search by title (e.g., Avengers)"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            style={{ flex: 1, padding: '10px 12px', borderRadius: 8, border: '1px solid #ccc' }}
          />
          <button type="submit" style={{ padding: '10px 12px', borderRadius: 8, border: '1px solid #ddd', background: '#fafafa', cursor: 'pointer' }}>
            Search
          </button>
        </form>

        {/* Wednesday picker */}
        <div style={{ display: 'flex', gap: 8 }}>
          <select
            value={selectedWed}
            onChange={(e) => setSelectedWed(e.target.value)}
            style={{ flex: 1, padding: '10px 12px', borderRadius: 8, border: '1px solid #ccc' }}
            aria-label="Pick a Wednesday"
          >
            {wedOptions.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
          <button
            onClick={() => setSelectedWed(ymd(new Date(new Date(selectedWed).getTime() - 7 * 24 * 3600 * 1000)))}
            style={{ padding: '10px 12px', borderRadius: 8, border: '1px solid #ddd', background: '#fafafa', cursor: 'pointer' }}
            title="Previous week"
          >
            ⟵
          </button>
          <button
            onClick={() => setSelectedWed(ymd(new Date(new Date(selectedWed).getTime() + 7 * 24 * 3600 * 1000)))}
            style={{ padding: '10px 12px', borderRadius: 8, border: '1px solid #ddd', background: '#fafafa', cursor: 'pointer' }}
            title="Next week"
          >
            ⟶
          </button>
        </div>
      </div>

      {/* Status */}
      {loading && <div style={{ marginBottom: 12, color: '#555' }}>Loading…</div>}
      {error && <div style={{ marginBottom: 12, color: '#b00020' }}>Error: {error}</div>}

      {/* Results grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 12, minHeight: 200 }}>
        {paginatedResults.map((c) => (
          <button
            key={c.id}
            onClick={() => openModal(c)}
            style={{
              textAlign: 'left',
              display: 'grid',
              gridTemplateColumns: '80px 1fr',
              gap: 12,
              padding: 12,
              borderRadius: 12,
              border: '1px solid #e5e7eb',
              background: '#fff',
              cursor: 'pointer',
            }}
          >
            {c.thumbnail_url ? (
              <img
                src={c.thumbnail_url}
                alt={`${c.title} cover`}
                width={80}
                height={120}
                style={{ borderRadius: 8, objectFit: 'cover' }}
                onError={(e) => { e.currentTarget.style.visibility = 'hidden' }}
              />
            ) : (
              <div style={{ width: 80, height: 120, background: '#eee', borderRadius: 8 }} />
            )}

            <div style={{ display: 'grid', gap: 6 }}>
              <div style={{ fontWeight: 600 }}>{c.title || 'Untitled'}</div>
              <div style={{ fontSize: 12, color: '#555' }}>
                {c.onsale_date ? `On sale: ${c.onsale_date}` : 'On sale: —'}
              </div>
              <div style={{ fontSize: 12, color: '#6b7280' }}>
                {c.format || 'Comic'}
              </div>
            </div>
          </button>
        ))}
      </div>

      {/* Pagination controls */}
      <div style={{ display: 'flex', justifyContent: 'center', gap: 6, marginTop: 16 }}>
        {Array.from({ length: pageCount }, (_, i) => {
          const p = i + 1
          const active = p === page
          return (
            <button
              key={p}
              onClick={() => setPage(p)}
              style={{
                padding: '8px 12px',
                borderRadius: 8,
                border: `1px solid ${active ? '#7c3aed' : '#ddd'}`,
                background: active ? '#f5f3ff' : '#fafafa',
                cursor: 'pointer',
                fontWeight: active ? 600 : 400
              }}
              aria-current={active ? 'page' : undefined}
            >
              {p}
            </button>
          )
        })}
      </div>

      {/* Modal */}
      {open && active && (
        <div
          onClick={closeModal}
          style={{
            position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.35)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20, zIndex: 50
          }}
          aria-modal="true"
          role="dialog"
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{ background: '#fff', borderRadius: 12, maxWidth: 720, width: '100%', padding: 20, boxShadow: '0 10px 30px rgba(0,0,0,0.2)' }}
          >
            <div style={{ display: 'grid', gridTemplateColumns: '140px 1fr', gap: 16 }}>
              {active.thumbnail_url ? (
                <img
                  src={active.thumbnail_url}
                  alt={`${active.title} cover`}
                  width={120}
                  height={180}
                  style={{ borderRadius: 8, objectFit: 'cover' }}
                />
              ) : (
                <div style={{ width: 120, height: 180, background: '#eee', borderRadius: 8 }} />
              )}

              <div>
                <h2 style={{ margin: '0 0 6px' }}>{active.title || 'Untitled'}</h2>
                <div style={{ fontSize: 14, color: '#555', marginBottom: 12 }}>
                  {active.onsale_date ? `On sale: ${active.onsale_date}` : ''} {active.format ? `• ${active.format}` : ''}
                </div>
                <p style={{ whiteSpace: 'pre-wrap', lineHeight: 1.5 }}>
                  {stripHtml(active.description) || 'No description provided.'}
                </p>
              </div>
            </div>

            <div style={{ textAlign: 'right', marginTop: 16 }}>
              <button onClick={closeModal} style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid #ddd', background: '#fafafa', cursor: 'pointer' }}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      <footer style={{ marginTop: 24, fontSize: 12, color: '#6b7280' }}>
        Tip: If a week looks empty, click <b>Sync current month</b> first, then re‑select your Wednesday.
      </footer>
    </div>
  )
}
