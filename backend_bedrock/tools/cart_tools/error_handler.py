"""
Comprehensive error handling for cart operations
"""

import logging
from typing import Dict, Any, Optional
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CartError(Exception):
    """Base exception for cart operations"""
    pass

class ProductNotFoundError(CartError):
    """Raised when a product cannot be found"""
    pass

class BudgetExceededError(CartError):
    """Raised when adding an item would exceed budget"""
    pass

class AvailabilityError(CartError):
    """Raised when a product is not available"""
    pass

class SessionError(CartError):
    """Raised when there's an issue with session management"""
    pass

def handle_cart_errors(func):
    """
    Decorator to handle cart operation errors gracefully
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ProductNotFoundError as e:
            logger.warning(f"Product not found: {e}")
            return {
                "success": False,
                "error_type": "product_not_found",
                "message": f"I couldn't find that product. {str(e)}",
                "suggestions": [
                    "Try using different keywords",
                    "Check the spelling",
                    "Use more general terms",
                    "Browse by category instead"
                ]
            }
        except BudgetExceededError as e:
            logger.warning(f"Budget exceeded: {e}")
            return {
                "success": False,
                "error_type": "budget_exceeded",
                "message": f"This would exceed your budget. {str(e)}",
                "suggestions": [
                    "Remove some items from your cart",
                    "Look for cheaper alternatives",
                    "Increase your budget limit"
                ]
            }
        except AvailabilityError as e:
            logger.warning(f"Availability issue: {e}")
            return {
                "success": False,
                "error_type": "availability_issue",
                "message": f"This item is not available. {str(e)}",
                "suggestions": [
                    "Try a substitute product",
                    "Check back later",
                    "Look for similar items"
                ]
            }
        except SessionError as e:
            logger.error(f"Session error: {e}")
            return {
                "success": False,
                "error_type": "session_error",
                "message": "There was an issue with your session. Please try again.",
                "suggestions": [
                    "Refresh the page",
                    "Clear your browser cache",
                    "Try again in a few minutes"
                ]
            }
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}")
            return {
                "success": False,
                "error_type": "unexpected_error",
                "message": "I encountered an unexpected error. Please try again.",
                "suggestions": [
                    "Try rephrasing your request",
                    "Check your internet connection",
                    "Contact support if the issue persists"
                ]
            }
    return wrapper

def validate_session_id(session_id: Optional[str]) -> str:
    """
    Validate and normalize session ID
    """
    if not session_id:
        raise SessionError("Session ID is required")
    
    if not isinstance(session_id, str):
        raise SessionError("Session ID must be a string")
    
    if len(session_id.strip()) == 0:
        raise SessionError("Session ID cannot be empty")
    
    return session_id.strip()

def validate_user_id(user_id: Optional[str]) -> str:
    """
    Validate and normalize user ID
    """
    if not user_id:
        raise SessionError("User ID is required")
    
    if not isinstance(user_id, str):
        raise SessionError("User ID must be a string")
    
    if len(user_id.strip()) == 0:
        raise SessionError("User ID cannot be empty")
    
    return user_id.strip()

def validate_item_name(item_name: Optional[str]) -> str:
    """
    Validate and normalize item name
    """
    if not item_name:
        raise ProductNotFoundError("Item name is required")
    
    if not isinstance(item_name, str):
        raise ProductNotFoundError("Item name must be a string")
    
    cleaned_name = item_name.strip()
    if len(cleaned_name) == 0:
        raise ProductNotFoundError("Item name cannot be empty")
    
    if len(cleaned_name) > 100:
        raise ProductNotFoundError("Item name is too long (max 100 characters)")
    
    return cleaned_name

def validate_quantity(quantity: Any) -> int:
    """
    Validate and normalize quantity
    """
    try:
        qty = float(quantity)
        if qty <= 0:
            raise ValueError("Quantity must be positive")
        if qty > 1000:
            raise ValueError("Quantity is too large (max 1000)")
        return int(qty)
    except (ValueError, TypeError):
        raise ProductNotFoundError("Quantity must be a positive number")

def check_aws_service_health() -> Dict[str, Any]:
    """
    Check if AWS services are accessible
    """
    try:
        # Try to import and test basic AWS connectivity
        import boto3
        from botocore.exceptions import NoCredentialsError, ClientError
        
        # Test DynamoDB connectivity
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        
        return {
            "aws_available": True,
            "dynamodb_available": True,
            "message": "AWS services are accessible"
        }
    except NoCredentialsError:
        return {
            "aws_available": False,
            "dynamodb_available": False,
            "message": "AWS credentials not configured",
            "suggestion": "Configure AWS credentials using 'aws configure'"
        }
    except ClientError as e:
        return {
            "aws_available": False,
            "dynamodb_available": False,
            "message": f"AWS service error: {e}",
            "suggestion": "Check AWS service status and permissions"
        }
    except Exception as e:
        return {
            "aws_available": False,
            "dynamodb_available": False,
            "message": f"Unknown AWS error: {e}",
            "suggestion": "Check AWS configuration and network connectivity"
        }

def create_error_response(error_type: str, message: str, suggestions: list = None) -> Dict[str, Any]:
    """
    Create a standardized error response
    """
    return {
        "success": False,
        "error_type": error_type,
        "message": message,
        "suggestions": suggestions or [],
        "timestamp": None  # Could add timestamp if needed
    }

def create_success_response(message: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Create a standardized success response
    """
    response = {
        "success": True,
        "message": message
    }
    
    if data:
        response.update(data)
    
    return response