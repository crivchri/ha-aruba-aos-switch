class ArubaError(Exception):
    """Base Aruba API error."""
class ArubaAuthError(ArubaError):
    """Authentication failed."""
class ArubaConnectionError(ArubaError):
    """Connection failed."""
class ArubaProtocolError(ArubaError):
    """Unexpected API response."""
class ArubaRateLimitError(ArubaError):
    """Switch is busy or rate limiting."""
    def __init__(self, message: str, retry_after: int = 5) -> None:
        super().__init__(message); self.retry_after = retry_after
