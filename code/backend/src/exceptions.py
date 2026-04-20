class BaseAppException(Exception):
    """Base exception for all application-specific errors."""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class EntityNotFoundError(BaseAppException):
    """Raised when a requested database entity is not found."""
    def __init__(self, entity_name: str, entity_id: int = None):
        msg = f"{entity_name} not found"
        if entity_id:
            msg += f" (ID: {entity_id})"
        super().__init__(message=msg, status_code=404)

class ValidationError(BaseAppException):
    """Raised when input validation fails (e.g., MIME type, size)."""
    def __init__(self, message: str):
        super().__init__(message=message, status_code=400)

class StorageError(BaseAppException):
    """Raised when an operation on the underlying blob storage (MinIO/S3) fails."""
    def __init__(self, message: str):
        super().__init__(message=f"Storage operation failed: {message}", status_code=502)

class UnauthorizedError(BaseAppException):
    """Raised when an action is denied due to permissions or missing authentication."""
    def __init__(self, message: str = "Not authenticated"):
        super().__init__(message=message, status_code=401)
