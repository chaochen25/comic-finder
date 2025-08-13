export async function apiGet(path) {
  const res = await fetch(path)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export const getHealth = () => apiGet('/api/health')
export const searchComics = (q) => apiGet(`/api/comics/search?q=${encodeURIComponent(q)}`)
export const getComicsByWeek = (isoWed) => apiGet(`/api/comics/week?wed=${isoWed}`)
export const getComic = (id) => apiGet(`/api/comics/${id}`)
export async function apiPost(path) {
    const res = await fetch(path, { method: 'POST' })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.json()
  }
  export const syncMonth = (start, end) => apiPost(`/api/marvel/sync?start=${start}&end=${end}`)
  