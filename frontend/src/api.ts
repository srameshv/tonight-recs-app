export type ItemType = 'movie' | 'tv' | 'restaurant'

export interface User {
  id: number
  name: string
}

export interface Item {
  id: number
  type: ItemType
  title: string
  item_metadata: Record<string, unknown>
}

export interface Rating {
  id: number
  user_id: number
  item_id: number
  value: number
}

export interface PreferenceNote {
  id: number
  user_id: number
  text: string
}

export type RankingMode = 'both_must_like' | 'weighted'

export interface RecommendationRequest {
  item_type: ItemType
  mode: RankingMode
  context?: Record<string, string>
  candidate_pool_size?: number
  top_n?: number
  shortlist_n?: number
}

export interface RankedCandidate {
  item_id: number
  title: string
  per_user_scores: Record<string, number>
  composite_score: number
}

export interface TopPick {
  item_id: number
  title: string
  per_user_scores: Record<string, number>
  blurb: string
}

export interface RecommendationResponse {
  ranked: RankedCandidate[]
  top_pick: TopPick | null
  log_id: number
}

const BASE = '/api'

async function json<T>(response: Response): Promise<T> {
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`)
  return response.json() as Promise<T>
}

export const api = {
  listUsers: () => fetch(`${BASE}/users`).then((r) => json<User[]>(r)),

  listItems: (type: ItemType) =>
    fetch(`${BASE}/items?type=${type}`).then((r) => json<Item[]>(r)),

  listRatings: (userId: number) =>
    fetch(`${BASE}/ratings?user_id=${userId}`).then((r) => json<Rating[]>(r)),

  upsertRating: (userId: number, itemId: number, value: number) =>
    fetch(`${BASE}/ratings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, item_id: itemId, value }),
    }).then((r) => json<Rating>(r)),

  getNote: (userId: number) =>
    fetch(`${BASE}/preferences/notes/${userId}`).then((r) =>
      json<PreferenceNote | null>(r),
    ),

  upsertNote: (userId: number, text: string) =>
    fetch(`${BASE}/preferences/notes`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, text }),
    }).then((r) => json<PreferenceNote>(r)),

  getRecommendations: (request: RecommendationRequest) =>
    fetch(`${BASE}/recommendations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    }).then((r) => json<RecommendationResponse>(r)),
}
