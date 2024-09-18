from django.urls import resolve
from rest_framework.permissions import AllowAny


from typing import Any


def get_permission_class_app_name(request):
    resolver_match = resolve(request.path_info)
    view_function = resolver_match.func
    view_class = getattr(view_function, "view_class", None)
    permission_classes = getattr(view_class, "permission_classes", [])
    return permission_classes


class ClearAuthenticationHeaderMiddleware:
    """
    For removing Authentication headers from 'anonymous' endpoints such as Register, Login...
    """

    def __init__(self, get_response) -> None:
        self.get_response = get_response

    def __call__(self, request) -> Any:
        permission_classes = get_permission_class_app_name(request)
        token = request.META.get("HTTP_AUTHORIZATION")
        if token and AllowAny in permission_classes:
            request.META.pop("HTTP_AUTHORIZATION")

        return self.get_response(request)
