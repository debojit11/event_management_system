from rest_framework import serializers
from events.models import Event, Attendee, Ticket

class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ['name', 'description', 'location', 'start_date', 'end_date', 'speakers', 'organizer']
        read_only_fields = ['organizer']  # Prevent the client from setting the organizer field

    def create(self, validated_data):
        # Set the organizer to the logged-in user
        validated_data['organizer'] = self.context['request'].user
        return super().create(validated_data)

class AttendeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendee
        fields = '__all__'  # Or specify fields as needed

class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = '__all__'  # Or specify fields as needed
