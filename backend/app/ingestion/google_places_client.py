"""Google Places (New) client: pulls candidate restaurants into a normalized shape."""

import httpx

from app.config import settings

SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"

FIELD_MASK = ",".join(
    [
        "places.id",
        "places.displayName",
        "places.primaryType",
        "places.types",
        "places.priceLevel",
        "places.rating",
        "places.userRatingCount",
        "places.formattedAddress",
    ]
)


def _normalize(place: dict) -> dict:
    return {
        "type": "restaurant",
        "external_id": place["id"],
        "title": place.get("displayName", {}).get("text", ""),
        "item_metadata": {
            "cuisine_types": place.get("types", []),
            "primary_type": place.get("primaryType"),
            "price_level": place.get("priceLevel"),
            "rating": place.get("rating"),
            "user_rating_count": place.get("userRatingCount"),
            "address": place.get("formattedAddress"),
        },
    }


def fetch_candidates(query: str | None = None, max_result_count: int = 20) -> list[dict]:
    """Text-search restaurants near the configured default location."""
    text_query = query or f"restaurants in {settings.default_location}"
    with httpx.Client(timeout=10) as client:
        response = client.post(
            SEARCH_URL,
            headers={
                "X-Goog-Api-Key": settings.google_places_api_key,
                "X-Goog-FieldMask": FIELD_MASK,
                "Content-Type": "application/json",
            },
            json={"textQuery": text_query, "maxResultCount": max_result_count},
        )
        response.raise_for_status()
        places = response.json().get("places", [])
    return [_normalize(p) for p in places]
