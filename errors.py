# extergram/errors.py

class ExtergramError(Exception):
    """Base exception for the Extergram library."""
    pass

class APIError(ExtergramError):
    def __init__(self, description: str, error_code: int, parameters: dict = None):
        self.description = description
        self.error_code = error_code
        self.parameters = parameters or {}
        message = f"[Error {error_code}] {description}"
        if self.parameters:
            message += f" (parameters: {self.parameters})"
        super().__init__(message)

class NetworkError(APIError):
    pass

class BadRequestError(APIError):
    pass

class UnauthorizedError(APIError):
    pass

class ForbiddenError(APIError):
    pass

class TelegramAdminError(ForbiddenError):
    pass

class NotFoundError(APIError):
    pass

class ConflictError(APIError):
    pass

class EntityTooLargeError(APIError):
    pass

class FloodControlError(APIError):
    def __init__(self, description: str, error_code: int, retry_after: int = None):
        super().__init__(description, error_code, {'retry_after': retry_after} if retry_after else None)
        self.retry_after = retry_after

class InternalServerError(APIError):
    pass

class BadGatewayError(APIError):
    pass

class EmptyTokenError(ExtergramError):
    """Raised when the bot token is empty."""
    pass

class InvalidTokenError(ExtergramError):
    """Raised when the token format is invalid (e.g., too short)."""
    pass

class WebhookError(ExtergramError):
    """Raised when webhook operations fail."""
    pass