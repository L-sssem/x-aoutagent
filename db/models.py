"""Database model skeletons."""

from dataclasses import dataclass


@dataclass
class Account:
    """Represent an account model."""

    account_id: str
    display_name: str


@dataclass
class Post:
    """Represent a post model."""

    account_id: str
    content: str

