"""Supabase client implementation."""

from __future__ import annotations

import logging
import os
from typing import Any

from dotenv import load_dotenv
from supabase import Client, create_client

LOGGER = logging.getLogger(__name__)


class SupabaseClient:
    """Provide database operations via Supabase."""

    def __init__(self, url: str | None = None, key: str | None = None) -> None:
        """Initialize the Supabase client from explicit values or .env variables."""
        load_dotenv()

        supabase_url = url or os.getenv("SUPABASE_URL")
        supabase_key = key or os.getenv("SUPABASE_KEY")

        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be configured in .env.")

        try:
            self.client: Client = create_client(supabase_url, supabase_key)
        except Exception as exc:  # pragma: no cover - depends on external service state
            LOGGER.exception("Failed to initialize Supabase client.")
            raise ConnectionError("Failed to initialize Supabase client.") from exc

    def check_connection(self) -> bool:
        """Check connectivity by running a minimal read query."""
        try:
            self.client.table("accounts").select("account_id").limit(1).execute()
            return True
        except Exception as exc:  # pragma: no cover - depends on external service state
            LOGGER.exception("Supabase connection check failed.")
            return False

    def fetch_account(self, account_id: str) -> dict[str, Any]:
        """Fetch account data by account identifier."""
        try:
            response = (
                self.client.table("accounts")
                .select("*")
                .eq("account_id", account_id)
                .limit(1)
                .execute()
            )
            records = response.data or []
            return records[0] if records else {}
        except Exception as exc:
            LOGGER.exception("Failed to fetch account: %s", account_id)
            raise RuntimeError(f"Failed to fetch account: {account_id}") from exc

    def save_post(self, account_id: str, content: str) -> None:
        """Save a post record for the specified account."""
        payload = {
            "account_id": account_id,
            "content": content,
        }
        try:
            self.client.table("posts").insert(payload).execute()
        except Exception as exc:
            LOGGER.exception("Failed to save post for account: %s", account_id)
            raise RuntimeError(f"Failed to save post for account: {account_id}") from exc
