"""Pull a candidate pool from TMDB and Google Places into the items table."""

from sqlmodel import Session, select

from app.db import engine, init_db
from app.ingestion import google_places_client, tmdb_client
from app.models import Item


def upsert(session: Session, candidate: dict) -> None:
    existing = session.exec(
        select(Item).where(
            Item.type == candidate["type"],
            Item.external_id == candidate["external_id"],
        )
    ).first()
    if existing:
        existing.title = candidate["title"]
        existing.item_metadata = candidate["item_metadata"]
        session.add(existing)
    else:
        session.add(Item(**candidate))


def main() -> None:
    init_db()
    candidates = [
        *tmdb_client.fetch_candidates("movie"),
        *tmdb_client.fetch_candidates("tv"),
        *google_places_client.fetch_candidates(),
    ]
    with Session(engine) as session:
        for candidate in candidates:
            upsert(session, candidate)
        session.commit()
    print(f"Synced {len(candidates)} candidates.")


if __name__ == "__main__":
    main()
