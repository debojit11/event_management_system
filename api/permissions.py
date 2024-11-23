from rest_framework.permissions import BasePermission
from events.models import Event

class IsOrganizerOrReadOnly(BasePermission):
    """
    Custom permission to only allow the organizer of an event to edit events and tickets.
    """

    def has_object_permission(self, request, view, obj):
        # For read-only permissions, grant access
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True

        # Check if the object is an Event (direct organizer field)
        if isinstance(obj, Event):
            if obj.organizer == request.user:
                return True

        # Check if the object is a Ticket (access organizer via related Event)
        if hasattr(obj, 'event') and isinstance(obj.event, Event):
            if obj.event.organizer == request.user:
                return True

        return False
