import { useEffect, useMemo, useState } from 'react'

/**
 * App.jsx — Marvel Release Tracker (MVP)
 * - "Sync current month" -> POST /api/marvel/sync
 * - Wednesday picker -> GET /api/comics/week?wed=YYYY-MM-DD
 * - Search -> GET /api/comics/search?q=term
 * - Click a result -> GET /api/comics/{id} in a modal
 * - Optional "Single issues only" filter on the client
 *
 * Works with Vite proxy:
 *   server: { proxy: { '/api': 'http://127.0.0.1:8000' } }
 */

/* ----------------------- Small helpers ----------------------- */

// Format Date as YYYY-MM-DD (what the API expects)
function fmt(d) {
  return d.toISOString().slice(0, 10)
}

// Return all Wednesdays for the current month
function getWednesdaysForMonth(d = new Date()) {
  const year = d.getFullYear()
  const month = d.getMonth()
  const first = new Date(year, month, 1)
  const nextMonth = new Date(year, month + 1, 1)
  const weds = []
  // find first Wednesday (0=Sun..3=Wed)
  const offset = (3 - first.getDay() + 7) % 7
  let cur = new Date(year, month, 1 + offset)
  while (cur < nextMonth) {
    weds.push(new Date(cur))
    cur.setDate(cur.getDate() + 7)
  }
  return weds
}

/* ----------------------- Tiny API layer ----------------------- */

async function apiGet(path) {
  const res = await fetch(path)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}
async function apiPost(path) {
  const res = await fetch(path, { method: 'POST' })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

const getComicsByWeek = (isoWed) => apiGet(`/api/comics/week?wed=${isoWed}`)
const searchComics = (q) => apiGet(`/api/comics/search?q=${encodeURIComponent(q)}`)
const getComic = (id) => apiGet(`/api/comics/${id}`)
const syncMonth = (start, end) => apiPost(`/api/marvel/sync?start=${start}&end=${end}`)

/* ----------------------- Minimal Modal ----------------------- */

function Modal({ open, onClose, children }) {
  if (!open) return null
  return (
    <div
      role="dialog"
      aria-modal="true"
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0, background: 'rgba(0,0,0,.35)',
        display: 'grid', placeItems: 'center', padding: 16, zIndex: 1000
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{ background: 'white', color: 'black', maxWidth: 720, width: '100%', borderRadius: 12, padding: 16 }}
      >
        <button onClick={onClose} aria-label="Close" style={{ float: 'right', fontSize: 18 }}>✕</button>
        {children}
      </div>
    </div>
  )
}

/* ----------------------- Main App ----------------------- */

export default function App() {
  const [q, setQ] = useState('')
  const [selectedWed, setSelectedWed] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [open, setOpen] = useState(false)
  const [activeId, setActiveId] = useState(null)   // used for row highlight
  const [active, setActive] = useState(null)       // details data for modal
  const [singleOnly, setSingleOnly] = useState(true)

  const wednesdays = useMemo(() => getWednesdaysForMonth(new Date()), [])

  // Initial load: first Wednesday of the month
  useEffect(() => {
    async function loadInitial() {
      if (!wednesdays.length) return
      const iso = fmt(wednesdays[0])
      setSelectedWed(iso)
      setLoading(true); setError('')
      try {
        const data = await getComicsByWeek(iso)
        setResults(data)
      } catch (e) {
        setError(e.message)
      } finally {
        setLoading(false)
      }
    }
    loadInitial()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  /* ---------- handlers ---------- */

  async function onSearch(e) {
    e.preventDefault()
    if (!q.trim()) return
    setLoading(true); setError('')
    try {
      const data = await searchComics(q)
      setResults(data)
      setSelectedWed('') // clear week selection when searching
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  async function onPickWednesday(e) {
    const iso = e.target.value
    setSelectedWed(iso)
    if (!iso) return
    setLoading(true); setError('')
    try {
      const data = await getComicsByWeek(iso)
      setResults(data)
      setQ('') // clear text search when choosing a week
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  async function openDetails(id) {
    setActiveId(id)
    setOpen(true)
    setActive(null) // show "Loading..." in modal
    try {
      const data = await getComic(id)
      setActive(data)
    } catch (e) {
      setActive({ title: 'Error', description: e.message })
    }
  }

  async function syncCurrentMonth() {
    const d = new Date()
    const start = new Date(d.getFullYear(), d.getMonth(), 1).toISOString().slice(0, 10)
    const end = new Date(d.getFullYear(), d.getMonth() + 1, 0).toISOString().slice(0, 10)
    setLoading(true); setError('')
    try {
      await syncMonth(start, end)
      // After syncing, reload selected (or first) Wednesday
      const iso = selectedWed || (wednesdays[0] ? fmt(wednesdays[0]) : '')
      if (iso) {
        const data = await getComicsByWeek(iso)
        setSelectedWed(iso)
        setResults(data)
      }
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  function clearFilters() {
    setQ('')
    setSelectedWed('')
    setResults([])
    setError('')
    setActiveId(null)
  }

  // Client-side filter for single issues
  const filtered = singleOnly
    ? results.filter(c => {
        const f = (c.format || '').toLowerCase()
        // keep common "single issue" formats, hide collections
        const isComic = f.includes('comic')
        const isCollection = f.includes('collection') || f.includes('trade') || f.includes('hardcover') || f.includes('omnibus')
        return isComic && !isCollection
      })
    : results

  /* ---------- UI ---------- */

  return (
    <div className="container" style={{ maxWidth: 920, margin: '40px auto', padding: '0 16px', fontFamily: 'system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif' }}>
      <h1>Marvel Comic Release Tracker (MVP)</h1>

      {/* Controls card */}
      <div className="card" style={{ background: 'rgba(0,0,0,0.03)', padding: 16, borderRadius: 14, display: 'grid', gap: 12 }}>
        {/* Search */}
        <form onSubmit={onSearch} style={{ display: 'flex', gap: 8 }}>
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search titles (e.g., Avengers)…"
            aria-label="Search by title"
            style={{ padding: '10px 12px', borderRadius: 10, border: '1px solid #ccc', flex: 1 }}
          />
          <button type="submit" style={{ padding: '10px 12px', borderRadius: 10 }}>Search</button>
        </form>

        {/* Wednesday picker + actions */}
        <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
          <label style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <span>Pick a Wednesday:</span>
            <select
              value={selectedWed}
              onChange={onPickWednesday}
              style={{ padding: '10px 12px', borderRadius: 10, border: '1px solid #ccc' }}
            >
              <option value="">— choose —</option>
              {wednesdays.map((d) => {
                const iso = fmt(d)
                const human = d.toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric', weekday: 'short' })
                return <option key={iso} value={iso}>{human}</option>
              })}
            </select>
          </label>

          <label style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
            <input type="checkbox" checked={singleOnly} onChange={(e) => setSingleOnly(e.target.checked)} />
            Single issues only
          </label>

          <button type="button" onClick={syncCurrentMonth} style={{ padding: '10px 12px', borderRadius: 10 }}>
            Sync current month
          </button>

          <button type="button" onClick={clearFilters} style={{ padding: '10px 12px', borderRadius: 10 }}>
            Clear
          </button>
        </div>

        {/* Status */}
        {loading && <p>Loading…</p>}
        {error && <p role="alert" style={{ color: 'crimson' }}>Error: {error}</p>}
        {!loading && filtered.length === 0 && <p>No results yet. Try a search or pick a Wednesday.</p>}

        {/* Results */}
        <ul style={{ listStyle: 'none', padding: 0 }}>
          {filtered.map((c) => (
            <li
              key={c.id}
              onClick={() => openDetails(c.id)}
              aria-selected={c.id === activeId}
              style={{
                marginBottom: 12,
                display: 'grid',
                gridTemplateColumns: '80px 1fr',
                gap: 12,
                alignItems: 'start',
                cursor: 'pointer',
                background: c.id === activeId ? '#eef' : 'transparent',
                borderRadius: 10,
                padding: 6
              }}
            >
              {c.thumbnail_url
                ? <img src={c.thumbnail_url} alt={`${c.title} cover`} width={80} height={120} style={{ borderRadius: 8, objectFit: 'cover' }} />
                : <div style={{ width: 80, height: 120, borderRadius: 8, background: '#eee' }} />
              }
              <div>
                <div style={{ fontWeight: 700 }}>{c.title}</div>
                <div style={{ opacity: 0.8, margin: '2px 0' }}>
                  {c.author ? <em>{c.author}</em> : '—'}
                  {c.onsale_date ? <> • {new Date(c.onsale_date).toLocaleDateString()}</> : null}
                  {c.format ? <> • {c.format}</> : null}
                </div>
                {c.description && <p style={{ marginTop: 6 }}>{c.description}</p>}
              </div>
            </li>
          ))}
        </ul>
      </div>

      {/* Details Modal */}
      <Modal open={open} onClose={() => { setOpen(false); setActiveId(null) }}>
        {!active && <p>Loading…</p>}
        {active && (
          <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: 12 }}>
            {active.thumbnail_url
              ? <img src={active.thumbnail_url} alt={`${active.title} cover`} width={120} height={180} style={{ borderRadius: 8, objectFit: 'cover' }} />
              : <div style={{ width: 120, height: 180, borderRadius: 8, background: '#eee' }} />
            }
            <div>
              <h2 style={{ margin: 0 }}>{active.title}</h2>
              <p style={{ margin: '4px 0', opacity: .9 }}>
                {active.author ? <em>{active.author}</em> : '—'}
                {active.onsale_date ? <> • {new Date(active.onsale_date).toLocaleDateString()}</> : null}
                {active.format ? <> • {active.format}</> : null}
                {typeof active.issue_number === 'number' ? <> • #{active.issue_number}</> : null}
              </p>
              {active.description && <p style={{ marginTop: 8 }}>{active.description}</p>}
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
