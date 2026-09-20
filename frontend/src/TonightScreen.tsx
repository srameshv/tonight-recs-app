import { useState } from 'react'
import {
  api,
  type ItemType,
  type RankingMode,
  type RecommendationResponse,
  type User,
} from './api'

const TYPES: { key: ItemType; label: string }[] = [
  { key: 'movie', label: 'Movie' },
  { key: 'tv', label: 'TV Show' },
  { key: 'restaurant', label: 'Restaurant' },
]

const MODES: { key: RankingMode; label: string }[] = [
  { key: 'both_must_like', label: 'We both have to like it' },
  { key: 'weighted', label: 'Weigh both tastes' },
]

function ScoreRow({
  users,
  scores,
}: {
  users: User[]
  scores: Record<string, number>
}) {
  return (
    <div className="score-row">
      {users.map((u) => (
        <span key={u.id} className="score-pill">
          {u.name}: {scores[String(u.id)]?.toFixed(2) ?? '—'}
        </span>
      ))}
    </div>
  )
}

export function TonightScreen({ users }: { users: User[] }) {
  const [itemType, setItemType] = useState<ItemType>('movie')
  const [mode, setMode] = useState<RankingMode>('both_must_like')
  const [mood, setMood] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<RecommendationResponse | null>(null)

  async function fetchRecommendations() {
    setLoading(true)
    setError(null)
    try {
      const response = await api.getRecommendations({
        item_type: itemType,
        mode,
        context: mood ? { mood } : {},
      })
      setResult(response)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Something went wrong')
      setResult(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <div className="type-tabs">
        {TYPES.map((t) => (
          <button
            key={t.key}
            className={t.key === itemType ? 'active' : ''}
            onClick={() => setItemType(t.key)}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="type-tabs">
        {MODES.map((m) => (
          <button
            key={m.key}
            className={m.key === mode ? 'active' : ''}
            onClick={() => setMode(m.key)}
          >
            {m.label}
          </button>
        ))}
      </div>

      <div className="mood-row">
        <input
          type="text"
          value={mood}
          onChange={(e) => setMood(e.target.value)}
          placeholder="Mood or occasion (optional), e.g. cozy weeknight"
        />
        <button onClick={fetchRecommendations} disabled={loading}>
          {loading ? 'Thinking…' : 'What should we do tonight?'}
        </button>
      </div>

      {error && <p className="error">{error}</p>}

      {result?.top_pick && (
        <section className="top-pick">
          <h2>Tonight's pick: {result.top_pick.title}</h2>
          <p className="blurb">{result.top_pick.blurb}</p>
          <ScoreRow users={users} scores={result.top_pick.per_user_scores} />
        </section>
      )}

      {result && result.ranked.length > 0 && (
        <section className="ranked-list">
          <h3>Full ranking (scores shown, nothing hidden)</h3>
          <ul className="item-list">
            {result.ranked.map((c) => (
              <li key={c.item_id} className="item-row ranked-row">
                <div>
                  <span className="item-title">{c.title}</span>
                  <ScoreRow users={users} scores={c.per_user_scores} />
                </div>
                <span className="composite">
                  composite {c.composite_score.toFixed(2)}
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}
    </>
  )
}
