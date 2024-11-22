from rest_framework.permissions import BasePermission

class IsOrganizerOrReadOnly(BasePermission):
    """
    Custom permission to allow only the organizer of an event to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request (GET, HEAD, OPTIONS)
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        # Otherwise, check if the user is the organizer
        return obj.organizer == request.user
