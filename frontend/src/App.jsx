import { useEffect, useMemo, useState } from "react";

//helper functions
const pad = (n) => String(n).padStart(2, "0");
const fmtISO = (d) =>
  `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;

function startOfWeekWed(d) {
  // Normalize to the Wednesday of the week that contains d (Wed..Tue window)
  const dd = new Date(d.getFullYear(), d.getMonth(), d.getDate());
  const dow = dd.getDay(); // 0 Sun .. 6 Sat
  // Distance from current day to Wednesday (3)
  const delta = (dow <= 3 ? -(3 - dow) : 7 - (dow - 3));
  dd.setDate(dd.getDate() + delta);
  return dd;
}
function addDays(d, n) {
  const x = new Date(d);
  x.setDate(x.getDate() + n);
  return x;
}

// UI
function Spinner() {
  return (
    <div className="spinner">
      <div />
      <div />
      <div />
    </div>
  );
}

function Modal({ open, onClose, title, children }) {
  if (!open) return null;
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className="modal-card"
        onClick={(e) => {
          e.stopPropagation();
        }}
      >
        <div className="modal-header">
          <h3>{title}</h3>
          <button className="btn btn-sm" onClick={onClose}>
            ×
          </button>
        </div>
        <div className="modal-body">{children}</div>
      </div>
    </div>
  );
}

// Main functioning app
export default function App() {
  // Query/search
  const [q, setQ] = useState("");
  const [mode, setMode] = useState("week"); // "week" | "search"

  // Week navigation & paging
  const [wed, setWed] = useState(() => startOfWeekWed(new Date()));
  const [page, setPage] = useState(1); // 1-based
  const [pageSize] = useState(25); // show 5x5 per page
  const [total, setTotal] = useState(0);

  // Data & UI state
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [selected, setSelected] = useState(null); // comic for modal

  const totalPages = useMemo(
    () => Math.max(1, Math.ceil(total / pageSize)),
    [total, pageSize]
  );

  // Build a safe URL helper (prevents “Invalid URL” errors)
  const api = (path, params = {}) => {
    const base = "/api";
    const url = new URL(base + path, window.location.origin);
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== "") {
        url.searchParams.set(k, String(v));
      }
    });
    return url.toString();
  };

  // Fetch (week)
  const fetchWeek = async (w, p = 1) => {
    setLoading(true);
    setErr("");
    try {
      const res = await fetch(
        api("/comics/week", {
          wed: fmtISO(w),
          page: p,
          limit: pageSize,
        })
      );
      if (!res.ok) {
        const t = await res.text();
        throw new Error(`HTTP ${res.status}${t ? ` — ${t}` : ""}`);
      }
      const data = await res.json();
      setRows(data.items || data); // backend returns {items, total}? support both
      setTotal(Number(data.total ?? data.length ?? 0));
    } catch (e) {
      setErr(String(e.message || e));
      setRows([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  };

  // Fetch (search)
  const fetchSearch = async (term, p = 1) => {
    setLoading(true);
    setErr("");
    try {
      const clean = (term || "").trim();
      if (clean.length < 2) {
        // Don’t hit backend with empty/1-char -> avoids 422
        setRows([]);
        setTotal(0);
        setErr("Type at least 2 characters to search.");
      } else {
        const res = await fetch(
          api("/comics/search", {
            q: clean, // URL helper encodes
            page: p,
            limit: pageSize,
          })
        );
        if (!res.ok) {
          const t = await res.text();
          throw new Error(`HTTP ${res.status}${t ? ` — ${t}` : ""}`);
        }
        const data = await res.json();
        setRows(data.items || data);
        setTotal(Number(data.total ?? data.length ?? 0));
      }
    } catch (e) {
      setErr(String(e.message || e));
      setRows([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  };

  // Initial load
  useEffect(() => {
    setMode("week");
    setPage(1);
    fetchWeek(wed, 1);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // When mode/page/wed/q changes, refetch
  useEffect(() => {
    if (mode === "week") {
      fetchWeek(wed, page);
    } else {
      fetchSearch(q, page);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode, page, wed]);

  // UI handlers
  const goPrevWeek = () => {
    const n = addDays(wed, -7);
    setWed(n);
    setMode("week");
    setPage(1);
  };
  const goNextWeek = () => {
    const n = addDays(wed, +7);
    setWed(n);
    setMode("week");
    setPage(1);
  };
  const onSearch = (e) => {
    e.preventDefault();
    setMode("search");
    setPage(1);
    fetchSearch(q, 1);
  };
  const clearSearch = () => {
    setQ("");
    setMode("week");
    setPage(1);
    fetchWeek(wed, 1);
  };

  // Format helpers
  const weekLabel = useMemo(() => {
    const end = addDays(wed, 6);
    return new Intl.DateTimeFormat(undefined, {
      month: "short",
      day: "numeric",
      year: "numeric",
    }).formatRange?.(wed, end)
      ? new Intl.DateTimeFormat(undefined, {
          month: "short",
          day: "numeric",
          year: "numeric",
        }).formatRange(wed, end)
      : `${wed.toDateString()} – ${end.toDateString()}`;
  }, [wed]);

  return (
    // This JavaScript XML is created with the help of AI
    <div className="container">
      <header className="toolbar">
        <div className="brand">Comic Finder</div>

        <form className="searchbar" onSubmit={onSearch}>
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search by title (e.g., Daredevil)"
            aria-label="Search by title"
          />
          <button className="btn" type="submit">
            Search
          </button>
          {mode === "search" && (
            <button type="button" className="btn ghost" onClick={clearSearch}>
              Clear
            </button>
          )}
        </form>

        <div className="weeknav">
          <button className="btn" onClick={goPrevWeek} title="Previous week">
            ←
          </button>
          <div className="weeklabel">
            {mode === "week" ? `Week: ${weekLabel}` : "Search results"}
          </div>
          <button className="btn" onClick={goNextWeek} title="Next week">
            →
          </button>
        </div>
      </header>

      {/* Error + loading */}
      {err && (
        <div className="alert">
          {mode === "search" && q
            ? `Search results for “${q}” — ${err}`
            : `Error — ${err}`}
        </div>
      )}
      {loading && (
        <div className="loading">
          <Spinner />
          <span>Loading…</span>
        </div>
      )}

      {/* Grid */}
      {!loading && rows.length === 0 && !err && (
        <div className="empty">No results.</div>
      )}

      <div className="grid">
        {rows.map((c) => (
          <article
            key={c.id}
            className="card"
            onClick={() => setSelected(c)}
            title={c.title}
            role="button"
          >
            <div className="thumbwrap">
              {c.thumbnail_url ? (
                <img
                  src={c.thumbnail_url}
                  alt={c.title}
                  loading="lazy"
                  referrerPolicy="no-referrer"
                />
              ) : (
                <div className="thumb placeholder">No image</div>
              )}
            </div>
            <h4 className="title" title={c.title}>
              {c.title}
            </h4>
            <div className="meta">
              <span>
                {c.onsale_date
                  ? new Date(c.onsale_date).toLocaleDateString()
                  : "—"}
              </span>
              <span>·</span>
              <span>{c.format || "Comic"}</span>
            </div>
          </article>
        ))}
      </div>

      {/* Pagination (5×5 per page) */}
      {totalPages > 1 && (
        <nav className="pager">
          <button
            className="btn"
            disabled={page <= 1}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
          >
            Prev
          </button>
          <span className="pageinfo">
            Page {page} / {totalPages}
          </span>
          <button
            className="btn"
            disabled={page >= totalPages}
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
          >
            Next
          </button>
        </nav>
      )}

      {/* Modal for details */}
      <Modal
        open={!!selected}
        onClose={() => setSelected(null)}
        title={selected?.title || ""}
      >
        <div className="detail">
          <div className="detail-thumb">
            {selected?.thumbnail_url ? (
              <img
                src={selected.thumbnail_url}
                alt={selected.title}
                loading="lazy"
                referrerPolicy="no-referrer"
              />
            ) : (
              <div className="thumb placeholder">No image</div>
            )}
          </div>
          <div className="detail-text">
            <div className="detail-meta">
              {selected?.onsale_date
                ? new Date(selected.onsale_date).toLocaleDateString()
                : "—"}{" "}
              • {selected?.format || "Comic"}
            </div>
            <div
              className="detail-desc"
              // Backend sends HTML (ComicVine). Safe-ish for this controlled demo.
              dangerouslySetInnerHTML={{
                __html:
                  selected?.description ||
                  "<em>No description provided.</em>",
              }}
            />
          </div>
        </div>
      </Modal>
    </div>
  );
}
