from rest_framework.views import exception_handler
from rest_framework.exceptions import PermissionDenied, AuthenticationFailed, NotAuthenticated, ValidationError
from django.http import Http404

def custom_exc_handler(exc, context):
    result = exception_handler(exc, context)

    if isinstance(exc, PermissionDenied):
        result.status_code = 403
        result.data = {
              "message": "error",
              "error": {
                "code": 403,
                "details": "Access denied"
              },
              "data": None
            }

    if isinstance(exc, NotAuthenticated) or isinstance(exc, AuthenticationFailed):
        result.status_code = 401
        result.data = {
            "message": "error",
            "error": {
                "code": 401,
                "details": "Authentication failed"
            },
            "data": None
        }
    if isinstance(exc, Http404):
        result.status_code = 404
        result.data = {
            "message": "error",
            "error": {
                "code": 404,
                "details": "Not found"
            },
            "data": None
        }

    if isinstance(exc, ValidationError):
        result.status_code = 422
        result.data = {
            "message": "error",
            "error": {
                "code": 422,
                "details": "Validation error",
                "errors": exc.detail
            },
            "data": None
        }

    return result
