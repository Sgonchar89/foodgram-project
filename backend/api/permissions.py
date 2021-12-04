from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdministrator(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_admin


class IsAdministratorOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        return (
            request.method in SAFE_METHODS
            or request.user.is_authenticated and request.user.is_admin
        )


class IsAuthorOrAdminOrModerator(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if request.method == 'POST':
            return request.user.is_authenticated
        return (
            request.user == obj.author
            or request.user.is_admin
            or request.user.is_moderator
        )
