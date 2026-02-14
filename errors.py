# extergram/errors.py

class ExtergramError(Exception):
    """Base exception class for the Extergram library."""
    pass

class APIError(ExtergramError):
    """Raised when the Telegram API returns an error."""
    def __init__(self, description: str, error_code: int):
        self.description = description
        self.error_code = error_code
        super().__init__(f"[Error {error_code}] {description}")

class NetworkError(APIError):
    """Raised when a network-related error occurs."""
    pass

class BadRequestError(APIError):
    """Raised for 400 Bad Request errors."""
    pass

class UnauthorizedError(APIError):
    """Raised for 401 Unauthorized errors. Invalid token."""
    pass

class ForbiddenError(APIError):
    """Raised for 403 Forbidden errors."""
    pass
    
class TelegramAdminError(ForbiddenError):
    """Raised when the bot has insufficient rights to perform an admin action."""
    pass

class NotFoundError(APIError):
    """Raised for 404 Not Found errors."""
    pass

class ConflictError(APIError):
    """Raised for 409 Conflict errors."""
    pass

class EntityTooLargeError(APIError):
    """Raised for 413 Request Entity Too Large errors."""
    pass

class BadGatewayError(APIError):
    """Raised for 502 Bad Gateway errors."""
    pass

class InternalServerError(APIError):
    """Raised for 500 Internal Server Error."""
    pass