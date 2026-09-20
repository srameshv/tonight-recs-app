# "Tonight" — a two-person recommendation app (portfolio project)

## Context

You and your husband want a shared tool that recommends what to watch (movies/TV) and where to eat, tailored to both of your tastes at once. Beyond solving that real problem, this is meant to be a **portfolio piece that shows both product polish and AI systems depth** to an audience like a frontier-lab engineer or recruiter.

Two decisions came out of brainstorming that shape the whole design:

1. **TypeSafe is the thing being showcased.** Its Jev model is a small, cheap "System One" model ($42/billion input tokens — not a general LLM), purpose-built for typed judgments (Choice/Score/Noul) rather than free text. The recommendation *logic* — ranking, filtering, tie-breaking — should run through TypeSafe, not a general LLM, because that's the differentiated thing worth writing about.
2. **Non-judgment LLM work goes to an open-source model via Groq (free tier).** Anything that's free-text generation rather than a typed decision — explaining *why* something was recommended, parsing a freeform preference note into structured tags — uses a Groq-hosted open model, not TypeSafe and not a paid frontier LLM. This keeps cost near-zero and cleanly separates "judgment" from "generation," which is itself a lesson worth documenting.

This is a greenfield build (no existing codebase for this project), so no exploration phase was run — per your standing preference, new ideas are treated as blank-slate rather than tied to existing project patterns. It will reuse the **FastAPI + React** stack pattern from Saveur AI, since that's a stack you're already comfortable with.

## Architecture

```
TMDB API  ──┐
Yelp/Places ─┼─► FastAPI backend ─► Postgres/SQLite (items, ratings, notes, log)
             │         │
             │         ├─► TypeSafe (Jev): Score / Noul / Choice  ← the showcase
             │         │      - Score: per-user taste fit per candidate
             │         │      - Noul: hard filters (already seen, dietary conflict, disliked genre)
             │         │      - Choice: final tie-break given situational context
             │         │
             │         └─► Groq (open-source LLM): non-judgment text
             │                - explain *why* a rec was chosen (blurb)
             │                - parse a freeform preference note into structured tags
             │
             ▼
        React frontend (profile switch, rate items, freeform notes, "what should we do tonight")
```

Composite scoring (combining both people's Score results into one ranked list) happens **in plain code**, not in a model call — e.g. `min(score_you, score_husband)` for "we both have to like it" nights vs. a weighted average otherwise. Keeping that policy in code (not a prompt) is itself a point for the writeup.

## Data model

- `users` — 2 seeded rows (you, husband)
- `items` — `id, type [movie|tv|restaurant], external_id, title, metadata (JSON: genres/cuisine/etc from TMDB/Yelp)`
- `ratings` — `user_id, item_id, value, created_at` (explicit like/dislike or 1–5)
- `preference_notes` — `user_id, text, updated_at` (freeform, e.g. "I love slow-burn thrillers, hate jump scares")
- `recommendation_log` — `created_at, context (JSON: day/mood/occasion), results (JSON: scores + chosen item)` — doubles as your eval history

## Backend (FastAPI)

- `app/ingestion/` — TMDB client (movies/TV) and Yelp/Google Places client (restaurants); a `sync` job/script that pulls a candidate pool into `items`.
- `app/preferences/` — CRUD endpoints for ratings and freeform notes per user.
- `app/judgments/typesafe_client.py` — thin wrapper around the TypeSafe SDK; defines the actual Score/Noul/Choice question specs (instructions + criteria) as versioned, testable objects — not inline strings scattered through request handlers.
- `app/judgments/groq_client.py` — wrapper for the Groq-hosted open model; used only for explanation text and freeform-note parsing.
- `app/recommend/` — the orchestration endpoint (`POST /recommendations`):
  1. fetch candidate items (unwatched/unvisited, filtered to type)
  2. run Score judgments for both users in parallel (one batched TypeSafe call)
  3. run Noul filters, drop failures
  4. composite-rank in code per the active policy (both-must-like vs. weighted)
  5. optional Choice call on the top-N shortlist for situational tie-break
  6. Groq call to generate a short "why this" blurb for the top pick(s)
  7. log the full request/response to `recommendation_log`
- `scripts/eval.py` — a small hand-labeled eval set (e.g. 15–20 scenarios with an expected good/bad rec) scored against the live judgment pipeline; this is what makes the "AI depth" half of the portfolio goal real instead of just a demo that seemed to work once.

## Frontend (React)

- Profile switch: You / Husband / Both
- Preference screens: rate past items (thumbs), freeform "describe your taste" note per person
- Main screen: "What should we watch tonight?" / "Where should we eat?" — triggers `/recommendations`, shows ranked cards with the Groq-generated blurb **and** the underlying per-person Score values visible (this transparency is a nice, easy differentiator — most rec-app demos hide the scoring)
- History view backed by `recommendation_log`

## Build order

1. Scaffold FastAPI + React project structure
2. TMDB + Yelp ingestion, seed a real candidate pool
3. Preference capture (ratings + freeform notes) — backend + minimal UI
4. TypeSafe integration: define and test the Score/Noul/Choice question specs in isolation before wiring into the endpoint
5. Groq integration: explanation blurb, freeform-note parsing
6. Recommendation orchestration endpoint (composite scoring policy in code)
7. Frontend recommendation UI with score transparency
8. Eval harness + README section on architecture and tradeoffs (why TypeSafe for judgments, why Groq for generation, what the eval showed)
9. Deploy (e.g. Fly.io/Render backend + Vercel frontend) so the portfolio link actually works live

## Verification

- Unit-level: test each TypeSafe question spec against a few fixed state inputs, confirm typed output shape and sane probabilities.
- Integration: run `/recommendations` end-to-end against seeded TMDB/Yelp data for both profiles, confirm composite ranking behaves as expected (e.g. an item one person dislikes doesn't win on "both must like" mode).
- Eval: run `scripts/eval.py` against the labeled scenario set; report accuracy/precision in the README.
- Manual: use the deployed app for a real "what should we watch tonight" decision with your husband before calling it done.

## Open items to confirm before implementation starts

- TMDB and Yelp/Google Places API keys — need to be obtained and stored server-side (never in frontend code).
- TypeSafe account/API key access (their site mentions "early access" — may need to request access before building against it).
- Groq API key for the open-source model calls.
