from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.exceptions import PermissionDenied


class isCurrentUserOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if all(
            [
                str(request.user.id) != view.kwargs.get("user_id"),
                request.method not in SAFE_METHODS,
            ]
        ):
            raise PermissionDenied("You do not have permission to perform this action.")
        return True
