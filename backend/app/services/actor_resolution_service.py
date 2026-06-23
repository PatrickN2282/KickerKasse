from sqlalchemy.orm import Session

from app.repositories import UserRepository

MAX_USERNAME_LENGTH = 50
INVALID_USERNAME_CHARS = {"\r", "\n", "\t", "\0"}


def resolve_actor_username(
    db: Session,
    *,
    executed_by_user_id: int | None = None,
    executed_by_username: str | None = None,
) -> str | None:
    normalized_username = (executed_by_username or "").strip()
    if (
        normalized_username
        and (
            len(normalized_username) > MAX_USERNAME_LENGTH
            or any(char in INVALID_USERNAME_CHARS for char in normalized_username)
        )
    ):
        normalized_username = ""

    actor_repo = UserRepository(db)
    actor = None

    if executed_by_user_id is not None:
        actor = actor_repo.get_by_id(executed_by_user_id)

    if normalized_username:
        if actor and actor.username and actor.username.casefold() == normalized_username.casefold():
            return actor.username

        matched_actor = actor_repo.get_by_username(normalized_username)
        if matched_actor and matched_actor.username:
            return matched_actor.username

    if actor and actor.username:
        return actor.username
    if normalized_username and executed_by_user_id is None:
        return normalized_username
    return None
