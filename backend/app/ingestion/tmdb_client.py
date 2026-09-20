"""TMDB client: pulls candidate movies and TV shows into a normalized shape."""

import httpx

from app.config import settings

BASE_URL = "https://api.themoviedb.org/3"


def _normalize(result: dict, media_type: str) -> dict:
    return {
        "type": media_type,
        "external_id": str(result["id"]),
        "title": result.get("title") or result.get("name", ""),
        "item_metadata": {
            "overview": result.get("overview", ""),
            "genre_ids": result.get("genre_ids", []),
            "vote_average": result.get("vote_average"),
            "release_date": result.get("release_date") or result.get("first_air_date"),
            "poster_path": result.get("poster_path"),
        },
    }


def fetch_candidates(media_type: str, pages: int = 3) -> list[dict]:
    """media_type: 'movie' or 'tv'. Pulls `pages` pages of popular titles."""
    endpoint = f"{BASE_URL}/discover/{media_type}"
    candidates: list[dict] = []
    with httpx.Client(timeout=10) as client:
        for page in range(1, pages + 1):
            response = client.get(
                endpoint,
                params={
                    "api_key": settings.tmdb_api_key,
                    "sort_by": "popularity.desc",
                    "page": page,
                    "include_adult": False,
                },
            )
            response.raise_for_status()
            results = response.json().get("results", [])
            candidates.extend(_normalize(r, media_type) for r in results)
    return candidates
