"""
Standardized error response utilities for consistent API error handling
"""
from fastapi import HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any


class ErrorResponse(BaseModel):
    """Standardized error response format"""
    success: bool = False
    error: str
    message: str
    status_code: int
    details: Optional[Dict[str, Any]] = None


class AuthenticationError(HTTPException):
    """Standardized authentication error"""
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=401,
            detail={
                "success": False,
                "error": "authentication_failed",
                "message": detail,
                "status_code": 401
            },
            headers={"WWW-Authenticate": "Bearer"}
        )


class ValidationError(HTTPException):
    """Standardized validation error"""
    def __init__(self, detail: str = "Validation failed", field: Optional[str] = None):
        details = {"field": field} if field else None
        super().__init__(
            status_code=400,
            detail={
                "success": False,
                "error": "validation_failed",
                "message": detail,
                "status_code": 400,
                "details": details
            }
        )


class NotFoundError(HTTPException):
    """Standardized not found error"""
    def __init__(self, resource: str = "Resource", detail: Optional[str] = None):
        message = detail or f"{resource} not found"
        super().__init__(
            status_code=404,
            detail={
                "success": False,
                "error": "not_found",
                "message": message,
                "status_code": 404
            }
        )


class ServerError(HTTPException):
    """Standardized server error"""
    def __init__(self, detail: str = "Internal server error"):
        super().__init__(
            status_code=500,
            detail={
                "success": False,
                "error": "internal_server_error",
                "message": detail,
                "status_code": 500
            }
        )


class ConflictError(HTTPException):
    """Standardized conflict error"""
    def __init__(self, detail: str = "Resource conflict"):
        super().__init__(
            status_code=409,
            detail={
                "success": False,
                "error": "conflict",
                "message": detail,
                "status_code": 409
            }
        )


class ForbiddenError(HTTPException):
    """Standardized forbidden error"""
    def __init__(self, detail: str = "Access forbidden"):
        super().__init__(
            status_code=403,
            detail={
                "success": False,
                "error": "forbidden",
                "message": detail,
                "status_code": 403
            }
        )


class BadRequestError(HTTPException):
    """Standardized bad request error"""
    def __init__(self, detail: str = "Bad request", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=400,
            detail={
                "success": False,
                "error": "bad_request",
                "message": detail,
                "status_code": 400,
                "details": details
            }
        )


def create_error_response(
    status_code: int,
    error_type: str,
    message: str,
    details: Optional[Dict[str, Any]] = None
) -> ErrorResponse:
    """Create a standardized error response"""
    return ErrorResponse(
        success=False,
        error=error_type,
        message=message,
        status_code=status_code,
        details=details
    )


def handle_authentication_error(detail: str = "Invalid or missing authentication token") -> AuthenticationError:
    """Handle authentication errors consistently"""
    return AuthenticationError(detail=detail)


def validate_user_access(current_user: dict, required_user_id: str = None) -> str:
    """
    Validate user access and extract user_id consistently across all endpoints
    
    Args:
        current_user: User object from get_current_user dependency
        required_user_id: Optional specific user ID that must match current user
        
    Returns:
        str: The validated user_id
        
    Raises:
        AuthenticationError: If validation fails
    """
    if not current_user:
        raise handle_authentication_error("User authentication required")
    
    user_id = current_user.get("user_id")
    if not user_id:
        raise handle_authentication_error("Invalid user session - missing user ID")
    
    # If a specific user ID is required, validate it matches
    if required_user_id and user_id != required_user_id:
        raise handle_authentication_error("Access denied - user ID mismatch")
    
    return user_id


def handle_validation_error(detail: str, field: Optional[str] = None) -> ValidationError:
    """Handle validation errors consistently"""
    return ValidationError(detail=detail, field=field)


def handle_not_found_error(resource: str, identifier: Optional[str] = None) -> NotFoundError:
    """Handle not found errors consistently"""
    detail = f"{resource} '{identifier}' not found" if identifier else None
    return NotFoundError(resource=resource, detail=detail)


def handle_server_error(detail: str = "An unexpected error occurred") -> ServerError:
    """Handle server errors consistently"""
    return ServerError(detail=detail)


def handle_conflict_error(detail: str = "Resource conflict") -> ConflictError:
    """Handle conflict errors consistently"""
    return ConflictError(detail=detail)


def handle_forbidden_error(detail: str = "Access forbidden") -> ForbiddenError:
    """Handle forbidden errors consistently"""
    return ForbiddenError(detail=detail)


def handle_bad_request_error(detail: str = "Bad request", details: Optional[Dict[str, Any]] = None) -> BadRequestError:
    """Handle bad request errors consistently"""
    return BadRequestError(detail=detail, details=details)