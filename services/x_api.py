"""X API wrapper skeleton."""


class XAPIService:
    """Handle post publishing and media operations through the X API."""

    async def publish_post(self, account_id: str, content: str) -> str:
        """Publish a post and return the post identifier."""
        return ""

    async def upload_media(self, account_id: str, media_path: str) -> str:
        """Upload media and return the media identifier."""
        return ""

