"""Isolation test for the Groq generation helpers, run before wiring into
the recommendation endpoint."""

from app.judgments.groq_client import generate_blurb, parse_preference_note


def main() -> None:
    blurb = generate_blurb(
        item_title="Coyote vs. Acme",
        item_type="movie",
        score_summary={"you": 3.6, "husband": 3.9},
    )
    print(f"[blurb] {blurb}")

    tags = parse_preference_note(
        "I love slow-burn thrillers and hate jump scares. Also allergic to shellfish."
    )
    print(f"[tags] {tags}")


if __name__ == "__main__":
    main()
