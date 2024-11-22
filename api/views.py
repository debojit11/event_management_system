from django.shortcuts import render
from rest_framework import viewsets
from .serializers import EventSerializer, AttendeeSerializer, TicketSerializer
from events.models import Event, Attendee, Ticket

class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer

class AttendeeViewSet(viewsets.ModelViewSet):
    queryset = Attendee.objects.all()
    serializer_class = AttendeeSerializer

class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer

# Create your views here.
