"""Shadowban check service skeleton."""


class ShadowbanService:
    """Check and track shadowban state for accounts."""

    async def check_account(self, account_id: str) -> bool:
        """Return whether the target account is shadowbanned."""
        return False

