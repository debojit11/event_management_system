from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
# Create your models here.


class Event(models.Model):
    """
    The Event model represents an event created by an organizer. 
    It stores information like the event's name, description, location, 
    start and end dates, speakers, and the creation timestamp.

    Fields:
    - name: The name of the event.
    - description: A detailed description of the event.
    - location: The location where the event will be held.
    - start_date: The start date and time of the event.
    - end_date: The end date and time of the event.
    - speakers: The list of speakers at the event.
    - created_at: Timestamp when the event is created.

    Meta:
    - The events are ordered by their start date.
    """
    
    name = models.CharField(max_length=200, help_text="Name of the event")
    description = models.TextField(help_text="Description of the event")
    location = models.CharField(max_length=255, help_text="Event location")
    start_date = models.DateTimeField(help_text="Event start date and time")
    end_date = models.DateTimeField(help_text="Event end date and time")
    speakers = models.TextField(null=True, blank=True, help_text="List of speakers at the event")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when event is created")
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events')
    payment_page_url = models.URLField(max_length=500, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['start_date']


class Ticket(models.Model):
    """
    The Ticket model represents a type of ticket for an event. 
    It stores details like the ticket type (VIP, Regular), the price, 
    the available quantity, and the event it is associated with.

    Fields:
    - event: The event that this ticket is associated with.
    - ticket_type: The type of ticket (e.g., VIP, Regular).
    - requires_payment: Does this ticket type require payment?
    - price: The price of the ticket.
    - quantity: The total quantity of tickets available.
    - created_at: Timestamp when the ticket type is created.
    - paymnet_page_url: The url of the payment page of the event

    Methods:
    - available_quantity: Returns the available quantity of tickets based on the total quantity and attendees.
    """
    event = models.ForeignKey(Event, related_name='tickets', on_delete=models.CASCADE, help_text="The event this ticket is associated with.")
    ticket_type = models.CharField(max_length=100, help_text="Type of the ticket (e.g., VIP, Regular).")
    price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="The price of this ticket.")
    quantity = models.PositiveIntegerField(help_text="The total quantity of this ticket type available for sale.")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when ticket type was created.")

    def __str__(self):
        return f"{self.ticket_type} - {self.event.name}"

    def available_quantity(self):
        """
        Returns the available quantity of tickets based on total quantity minus attendees.
        """
        return self.quantity - self.attendees.count()


class Attendee(models.Model):
    """
    The Attendee model represents a user who has registered for an event. 
    It stores the user, the event they are attending, the type of ticket they have selected, 
    and the timestamp of registration.

    Fields:
    - user: The user attending the event.
    - event: The event the attendee has registered for.
    - ticket: The ticket type the attendee has purchased.
    - created_at: Timestamp when the attendee registered.

    Methods:
    - __str__: Returns a string representation of the attendee (user, event, and ticket type).
    """
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, help_text="The user who is attending the event.")
    event = models.ForeignKey(Event, related_name='attendees', on_delete=models.CASCADE, help_text="The event the attendee has registered for.")
    ticket = models.ForeignKey(Ticket, related_name='attendees', on_delete=models.CASCADE, help_text="The ticket type the attendee has purchased.")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when the attendee registered.")

    def __str__(self):
        return f"{self.user.username} - {self.event.name} ({self.ticket.ticket_type})"
    
    @property
    def first_name(self):
        return self.user.first_name

    @property
    def last_name(self):
        return self.user.last_name

    @property
    def email(self):
        return self.user.email