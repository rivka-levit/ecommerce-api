from rest_framework import permissions


class AccessOwnProfile(permissions.BasePermission):
    """Allow users to access just their own profiles."""

    def has_object_permission(self, request, view, obj):
        """Check user is trying to access its own profile."""

        return obj.user.id == request.user.id
