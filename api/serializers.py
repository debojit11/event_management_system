from rest_framework import serializers
from events.models import Event, Attendee, Ticket

class EventSerializer(serializers.ModelSerializer):
    organizer_name = serializers.ReadOnlyField(source='organizer.username')
    class Meta:
        model = Event
        fields = ['name', 'description', 'location', 'start_date', 'end_date', 'speakers', 'organizer', 'payment_page_url', 'organizer_name']
        read_only_fields = ['organizer']  # Prevent the client from setting the organizer field

    def create(self, validated_data):
        # Set the organizer to the logged-in user
        validated_data['organizer'] = self.context['request'].user
        return super().create(validated_data)

class AttendeeSerializer(serializers.ModelSerializer):
    # Include event name and ticket type as read-only fields
    event_name = serializers.ReadOnlyField(source='event.name')
    organizer_name = serializers.ReadOnlyField(source='event.organizer.username')
    ticket_type = serializers.ReadOnlyField(source='ticket.ticket_type')  # Assuming Ticket has a 'ticket_type' field
    user_name = serializers.ReadOnlyField(source='user.get_full_name')  # Get the user's full name
    user_email = serializers.ReadOnlyField(source='user.email')  # Get the user's email address
    ticket = serializers.PrimaryKeyRelatedField(queryset=Ticket.objects.all())  # Add ticket field to the serializer

    class Meta:
        model = Attendee
        fields = [
            'id', 
            'user', 
            'user_name',  # Added field for user's full name
            'user_email',  # Added field for user's email
            'event', 
            'event_name', 
            'organizer_name', 
            'ticket_type',
            'ticket',  # Include ticket field
            'created_at'
        ]


class TicketSerializer(serializers.ModelSerializer):
    event_name = serializers.ReadOnlyField(source='event.name')
    organizer_name = serializers.ReadOnlyField(source='event.organizer.username')
    class Meta:
        model = Ticket
        fields = [
            'id',
            'event',
            'event_name',
            'organizer_name',
            'ticket_type',
            'price',
            'quantity',
            'created_at'
        ]
