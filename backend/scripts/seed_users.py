"""Seed the two profiles this app is built for."""

from sqlmodel import Session, select

from app.db import engine, init_db
from app.models import User

SEED_NAMES = ["You", "Husband"]


def main() -> None:
    init_db()
    with Session(engine) as session:
        for name in SEED_NAMES:
            existing = session.exec(select(User).where(User.name == name)).first()
            if not existing:
                session.add(User(name=name))
        session.commit()


if __name__ == "__main__":
    main()
