"""
Custom exceptions and error handlers
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
import structlog
from typing import Any, Dict
import traceback

logger = structlog.get_logger()

class AIBlogAssistantException(Exception):
    """Base exception for AI Blog Assistant"""
    def __init__(self, message: str, code: str = "INTERNAL_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)

class AuthenticationError(AIBlogAssistantException):
    """Authentication related errors"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTHENTICATION_ERROR")

class AuthorizationError(AIBlogAssistantException):
    """Authorization related errors"""
    def __init__(self, message: str = "Access denied"):
        super().__init__(message, "AUTHORIZATION_ERROR")

class ValidationError(AIBlogAssistantException):
    """Validation related errors"""
    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, "VALIDATION_ERROR")

class ContentGenerationError(AIBlogAssistantException):
    """Content generation related errors"""
    def __init__(self, message: str = "Content generation failed"):
        super().__init__(message, "CONTENT_GENERATION_ERROR")

class PublishingError(AIBlogAssistantException):
    """Publishing related errors"""
    def __init__(self, message: str = "Publishing failed"):
        super().__init__(message, "PUBLISHING_ERROR")

class APIIntegrationError(AIBlogAssistantException):
    """External API integration errors"""
    def __init__(self, message: str = "API integration failed"):
        super().__init__(message, "API_INTEGRATION_ERROR")

class FileProcessingError(AIBlogAssistantException):
    """File processing related errors"""
    def __init__(self, message: str = "File processing failed"):
        super().__init__(message, "FILE_PROCESSING_ERROR")

def create_error_response(
    code: str,
    message: str,
    details: Dict[str, Any] = None,
    status_code: int = 500
) -> JSONResponse:
    """Create standardized error response"""
    error_data = {
        "error": {
            "code": code,
            "message": message,
            "timestamp": "2025-01-28T10:30:00Z",
        }
    }
    
    if details:
        error_data["error"]["details"] = details
    
    return JSONResponse(
        status_code=status_code,
        content=error_data
    )

async def ai_blog_assistant_exception_handler(
    request: Request, 
    exc: AIBlogAssistantException
) -> JSONResponse:
    """Handle custom AI Blog Assistant exceptions"""
    logger.error(
        "AI Blog Assistant exception",
        error_code=exc.code,
        error_message=exc.message,
        path=request.url.path,
        method=request.method
    )
    
    status_code_map = {
        "AUTHENTICATION_ERROR": 401,
        "AUTHORIZATION_ERROR": 403,
        "VALIDATION_ERROR": 400,
        "CONTENT_GENERATION_ERROR": 422,
        "PUBLISHING_ERROR": 502,
        "API_INTEGRATION_ERROR": 502,
        "FILE_PROCESSING_ERROR": 422,
    }
    
    status_code = status_code_map.get(exc.code, 500)
    
    return create_error_response(
        code=exc.code,
        message=exc.message,
        status_code=status_code
    )

async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTP exceptions"""
    logger.warning(
        "HTTP exception",
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path,
        method=request.method
    )
    
    return create_error_response(
        code="HTTP_ERROR",
        message=exc.detail,
        status_code=exc.status_code
    )

async def validation_exception_handler(
    request: Request, 
    exc: RequestValidationError
) -> JSONResponse:
    """Handle request validation errors"""
    logger.warning(
        "Validation error",
        errors=exc.errors(),
        path=request.url.path,
        method=request.method
    )
    
    return create_error_response(
        code="VALIDATION_ERROR",
        message="Invalid input parameters",
        details={"validation_errors": exc.errors()},
        status_code=422
    )

async def sqlalchemy_exception_handler(
    request: Request, 
    exc: SQLAlchemyError
) -> JSONResponse:
    """Handle SQLAlchemy database errors"""
    logger.error(
        "Database error",
        error=str(exc),
        path=request.url.path,
        method=request.method,
        traceback=traceback.format_exc()
    )
    
    return create_error_response(
        code="DATABASE_ERROR",
        message="Database operation failed",
        status_code=500
    )

async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all other exceptions"""
    logger.error(
        "Unhandled exception",
        error=str(exc),
        error_type=type(exc).__name__,
        path=request.url.path,
        method=request.method,
        traceback=traceback.format_exc()
    )
    
    return create_error_response(
        code="INTERNAL_ERROR",
        message="An unexpected error occurred",
        status_code=500
    )

def setup_exception_handlers(app: FastAPI):
    """Setup all exception handlers"""
    app.add_exception_handler(AIBlogAssistantException, ai_blog_assistant_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)