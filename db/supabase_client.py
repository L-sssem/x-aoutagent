"""Supabase client skeleton."""

from typing import Any


class SupabaseClient:
    """Provide database operations via Supabase."""

    def fetch_account(self, account_id: str) -> dict[str, Any]:
        """Fetch account data by account identifier."""
        return {}

    def save_post(self, account_id: str, content: str) -> None:
        """Save a post record for the specified account."""

