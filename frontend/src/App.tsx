import { useEffect, useMemo, useState } from 'react'
import { api, type Item, type ItemType, type Rating, type User } from './api'
import './App.css'

const TYPES: { key: ItemType; label: string }[] = [
  { key: 'movie', label: 'Movies' },
  { key: 'tv', label: 'TV Shows' },
  { key: 'restaurant', label: 'Restaurants' },
]

function App() {
  const [users, setUsers] = useState<User[]>([])
  const [activeUserId, setActiveUserId] = useState<number | null>(null)
  const [activeType, setActiveType] = useState<ItemType>('movie')
  const [items, setItems] = useState<Item[]>([])
  const [ratings, setRatings] = useState<Rating[]>([])
  const [note, setNote] = useState('')
  const [noteSaved, setNoteSaved] = useState(true)

  useEffect(() => {
    api.listUsers().then((u) => {
      setUsers(u)
      setActiveUserId(u[0]?.id ?? null)
    })
  }, [])

  useEffect(() => {
    api.listItems(activeType).then(setItems)
  }, [activeType])

  useEffect(() => {
    if (activeUserId == null) return
    api.listRatings(activeUserId).then(setRatings)
    api.getNote(activeUserId).then((n) => setNote(n?.text ?? ''))
  }, [activeUserId])

  const ratingByItemId = useMemo(() => {
    const map = new Map<number, number>()
    for (const r of ratings) map.set(r.item_id, r.value)
    return map
  }, [ratings])

  async function rate(itemId: number, value: number) {
    if (activeUserId == null) return
    const current = ratingByItemId.get(itemId)
    const next = current === value ? 0 : value
    await api.upsertRating(activeUserId, itemId, next)
    const updated = await api.listRatings(activeUserId)
    setRatings(updated)
  }

  async function saveNote() {
    if (activeUserId == null) return
    await api.upsertNote(activeUserId, note)
    setNoteSaved(true)
  }

  return (
    <main className="app">
      <h1>Tonight</h1>

      <div className="profile-switch">
        {users.map((u) => (
          <button
            key={u.id}
            className={u.id === activeUserId ? 'active' : ''}
            onClick={() => setActiveUserId(u.id)}
          >
            {u.name}
          </button>
        ))}
      </div>

      <section className="note-section">
        <label htmlFor="note">Describe your taste (freeform)</label>
        <textarea
          id="note"
          value={note}
          onChange={(e) => {
            setNote(e.target.value)
            setNoteSaved(false)
          }}
          placeholder="I love slow-burn thrillers, hate jump scares..."
        />
        <button onClick={saveNote} disabled={noteSaved}>
          {noteSaved ? 'Saved' : 'Save note'}
        </button>
      </section>

      <div className="type-tabs">
        {TYPES.map((t) => (
          <button
            key={t.key}
            className={t.key === activeType ? 'active' : ''}
            onClick={() => setActiveType(t.key)}
          >
            {t.label}
          </button>
        ))}
      </div>

      <ul className="item-list">
        {items.map((item) => {
          const value = ratingByItemId.get(item.id) ?? 0
          return (
            <li key={item.id} className="item-row">
              <span className="item-title">{item.title}</span>
              <span className="thumbs">
                <button
                  className={value === 1 ? 'active' : ''}
                  onClick={() => rate(item.id, 1)}
                  aria-label="thumbs up"
                >
                  👍
                </button>
                <button
                  className={value === -1 ? 'active' : ''}
                  onClick={() => rate(item.id, -1)}
                  aria-label="thumbs down"
                >
                  👎
                </button>
              </span>
            </li>
          )
        })}
      </ul>
    </main>
  )
}

export default App
