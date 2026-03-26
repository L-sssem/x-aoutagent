"""twitter-cli wrapper skeleton."""


class TwitterCLIService:
    """Wrap twitter-cli commands used by the system."""

    async def search_posts(self, query: str) -> list[dict[str, str]]:
        """Search posts with twitter-cli and return raw results."""
        return []

    async def fetch_mentions(self, account_id: str) -> list[dict[str, str]]:
        """Fetch mentions and replies for a target account."""
        return []

