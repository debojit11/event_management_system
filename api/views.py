from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import EventSerializer, AttendeeSerializer, TicketSerializer
from events.models import Event, Attendee, Ticket
from .permissions import IsOrganizerOrReadOnly

class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated, IsOrganizerOrReadOnly]  # Ensure the user is authenticated and only the organizer can edit the event

class AttendeeViewSet(viewsets.ModelViewSet):
    queryset = Attendee.objects.all()
    serializer_class = AttendeeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Ensure the user sees attendees for events they organized
        if self.request.user.is_authenticated:
            return Attendee.objects.filter(event__organizer=self.request.user)
        return Attendee.objects.none()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Validate that the ticket belongs to the provided event
        event = serializer.validated_data['event']
        ticket = serializer.validated_data.get('ticket')
        if ticket and ticket.event != event:
            return Response(
                {"error": "The selected ticket does not belong to the specified event."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        self.perform_create(serializer)
        
        attendee = serializer.instance
        payment_page_url = attendee.event.payment_page_url
        
        response_data = {
            "message": "Attendee created successfully.",
            "attendee": {
                "name": attendee.user.get_full_name(),
                "email": attendee.user.email,
                "event_name": attendee.event.name,
                "ticket_type": attendee.ticket.ticket_type if attendee.ticket else "Not specified"
            },
            "payment_page_url": payment_page_url if payment_page_url else "No payment page URL provided."
        }
        
        headers = self.get_success_headers(serializer.data)
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)



class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated, IsOrganizerOrReadOnly]  # Ensure the user is authenticated and only the organizer can edit tickets

    def get_queryset(self):
        # Filter tickets to only show those related to the events the user can view
        if self.request.user.is_authenticated:
            return Ticket.objects.filter(event__organizer=self.request.user)
        return Ticket.objects.none()

    def perform_create(self, serializer):
        # Ensure the user is the organizer of the related event when creating a ticket
        event = serializer.validated_data.get('event')
        if event.organizer != self.request.user:
            raise PermissionError("You are not allowed to create tickets for this event.")
        serializer.save()
