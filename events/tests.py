from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Event, Ticket, Attendee
from .forms import EventForm, TicketForm, CustomUserCreationForm, SupportForm
from django.utils.timezone import now  # Import the now() function
from datetime import timedelta  # Import timedelta

class EventModelTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")
        self.event = Event.objects.create(
            name="Tech Conference",
            description="A conference about the latest in tech.",
            location="Virtual",
            start_date=now() + timedelta(days=1),  # Use timezone-aware datetime
            end_date=now() + timedelta(days=2),
            speakers="Speaker1, Speaker2",
            organizer=self.user,
        )

    def test_event_creation(self):
        self.assertEqual(self.event.name, "Tech Conference")
        self.assertEqual(self.event.organizer, self.user)

    def test_event_ordering(self):
        event2 = Event.objects.create(
            name="Another Event",
            description="Description here.",
            location="Location",
            start_date=now() + timedelta(days=3),
            end_date=now() + timedelta(days=4),
            organizer=self.user,
        )
        events = Event.objects.all()
        self.assertEqual(events.first(), self.event)

class TicketModelTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")
        self.event = Event.objects.create(
            name="Tech Conference",
            description="A conference about the latest in tech.",
            location="Virtual",
            start_date=now() + timedelta(days=1),  # Use timezone-aware datetime
            end_date=now() + timedelta(days=2),
            speakers="Speaker1, Speaker2",
            organizer=self.user,
        )
        self.ticket = Ticket.objects.create(
            event=self.event,
            ticket_type="VIP",
            price=100.00,
            quantity=50,
        )

    def test_ticket_creation(self):
        self.assertEqual(self.ticket.event, self.event)
        self.assertEqual(self.ticket.ticket_type, "VIP")
        self.assertEqual(self.ticket.available_quantity(), 50)

class AttendeeModelTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")
        self.event = Event.objects.create(
            name="Tech Conference",
            description="A conference about the latest in tech.",
            location="Virtual",
            start_date=now() + timedelta(days=1),  # Use timezone-aware datetime
            end_date=now() + timedelta(days=2),
            speakers="Speaker1, Speaker2",
            organizer=self.user,
        )
        self.ticket = Ticket.objects.create(
            event=self.event,
            ticket_type="VIP",
            price=100.00,
            quantity=50,
        )
        self.attendee = Attendee.objects.create(
            user=self.user,
            event=self.event,
            ticket=self.ticket,
            registration_status=True
        )

    def test_attendee_creation(self):
        self.assertEqual(self.attendee.user, self.user)
        self.assertEqual(self.attendee.event, self.event)
        self.assertTrue(self.attendee.registration_status)

class EventFormTestCase(TestCase):
    def test_valid_event_form(self):
        form_data = {
            'name': 'Tech Conference',
            'description': 'A conference about tech.',
            'location': 'Virtual',
            'start_date': now() + timedelta(days=1),  # Use timezone-aware datetime
            'end_date': now() + timedelta(days=2),
            'speakers': 'Speaker1, Speaker2',
        }
        form = EventForm(data=form_data)
        self.assertTrue(form.is_valid())

class TicketFormTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")
        self.event = Event.objects.create(
            name="Tech Conference",
            description="A conference about the latest in tech.",
            location="Virtual",
            start_date=now() + timedelta(days=1),  # Use timezone-aware datetime
            end_date=now() + timedelta(days=2),
            speakers="Speaker1, Speaker2",
            organizer=self.user,
        )

    def test_valid_ticket_form(self):
        form_data = {
            'event': self.event.id,
            'ticket_type': 'VIP',
            'price': 100.00,
            'quantity': 50,
        }
        form = TicketForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())

class ViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser1", password="Admin12345")
        self.client.login(username="testuser1", password="Admin12345")
        self.event = Event.objects.create(
            name="Tech Conference",
            description="A conference about the latest in tech.",
            location="Virtual",
            start_date=now() + timedelta(days=1),  # Use timezone-aware datetime
            end_date=now() + timedelta(days=2),
            speakers="Speaker1, Speaker2",
            organizer=self.user,
        )

    def test_event_list_view(self):
        response = self.client.get(reverse('upcoming_events'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.event.name)

    def test_event_detail_view(self):
        response = self.client.get(reverse('event_detail', args=[self.event.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.event.description)
