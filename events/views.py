import razorpay
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.views import View
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Event, Ticket, Attendee
from .forms import EventForm, CustomUserCreationForm, TicketForm

# Initialize Razorpay client
client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

# Landing Page View
class LandingPageView(View):
    def get(self, request):
        return render(request, 'events/landing.html')

# Signup View
class SignupView(View):
    def get(self, request):
        form = CustomUserCreationForm()
        return render(request, 'events/signup.html', {'form': form})
    
    def post(self, request):
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Automatically log the user in after sign-up
            return redirect('landing_page')
        return render(request, 'events/signup.html', {'form': form})

# Login View (Custom)
class CustomLoginView(LoginView):
    template_name = 'events/login.html'

# Upcoming Events View (Login Required)
class UpcomingEventsView(LoginRequiredMixin, View):
    login_url = '/login/'  # Redirect to login page if not authenticated
    redirect_field_name = 'next'  # The field to redirect to after login

    def get(self, request):
        events = Event.objects.all()
        return render(request, 'events/upcoming_events.html', {'events': events})

# Event Detail View
class EventDetailView(LoginRequiredMixin, View):
    login_url = '/login/'

    def get(self, request, event_id):
        event = get_object_or_404(Event, id=event_id)
        tickets = Ticket.objects.filter(event=event)
        return render(request, 'events/event_detail.html', {'event': event, 'tickets': tickets})

# Ticket Purchase View
class TicketSelectView(View):
    def get(self, request, event_id):
        event = get_object_or_404(Event, id=event_id)
        ticket_types = Ticket.objects.filter(event=event)

        return render(request, 'events/select_ticket.html', {
            'event': event,
            'ticket_types': ticket_types,
            'user': request.user,
        })

    def post(self, request, event_id):
        event = get_object_or_404(Event, id=event_id)
        ticket_id = request.POST.get('ticket_type')  # `ticket_type` from the dropdown in `purchase_ticket.html`

        # Validate the selected ticket type
        try:
            ticket = Ticket.objects.get(id=ticket_id, event=event)
        except Ticket.DoesNotExist:
            messages.error(request, "Invalid ticket type selected.")
            return redirect('ticket_select', event_id=event_id)

        # Store the ticket ID in the session for use in payment
        request.session['selected_ticket_id'] = ticket.id

        # Redirect to the payment page
        return redirect('proceed_to_payment', event_id=event_id)

class TicketPaymentView(View):
    def get(self, request, event_id):
        event = get_object_or_404(Event, id=event_id)
        ticket_id = request.session.get('selected_ticket_id')

        # Validate the ticket ID from the session
        if not ticket_id:
            messages.error(request, "No ticket selected. Please choose a ticket first.")
            return redirect('events:ticket_select', event_id=event_id)

        try:
            ticket = Ticket.objects.get(id=ticket_id, event=event)
        except Ticket.DoesNotExist:
            messages.error(request, "Invalid ticket selected.")
            return redirect('ticket_select', event_id=event_id)

        # Redirect to the payment page
        return redirect(event.payment_page_url)



class MyEventsView(LoginRequiredMixin, View):
    login_url = '/login/'

    def get(self, request):
        # Events registered by the user
        registered_events = Attendee.objects.filter(user=request.user)

        # Events created by the user
        created_events = Event.objects.filter(organizer=request.user).prefetch_related('tickets__attendee_set')

        return render(request, 'events/my_events.html', {
            'registered_events': registered_events,
            'created_events': created_events,
        })

# Create Event View
class CreateEventView(LoginRequiredMixin, View):
    login_url = '/login/'

    def get(self, request):
        form = EventForm()
        return render(request, 'events/create_event.html', {'form': form})
    
    def post(self, request):
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.organizer = request.user
            event.save()
            return redirect('create_ticket', event_id=event.id)  # Redirect to ticket creation view with event ID
        return render(request, 'events/create_event.html', {'form': form})
    
class CreateTicketView(LoginRequiredMixin, View):
    login_url = '/login/'

    def get(self, request, event_id):
        event = get_object_or_404(Event, id=event_id, organizer=request.user)
        form = TicketForm(user=request.user, initial={'event': event})
        return render(request, 'events/create_ticket.html', {'form': form, 'event': event})

    def post(self, request, event_id):
        event = get_object_or_404(Event, id=event_id, organizer=request.user)
        form = TicketForm(request.POST, user=request.user)

        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.event = event
            ticket.save()
            messages.success(request, "Ticket created successfully!")

            # Handle which button was clicked
            if 'save_and_add_another' in request.POST:
                return redirect('create_ticket', event_id=event.id)

            elif 'done' in request.POST:
                # Redirect to confirmation page
                return redirect('confirm_integration', event_id=event.id)

        return render(request, 'events/create_ticket.html', {'form': form, 'event': event})


class ConfirmIntegrationView(View):
    def get(self, request, event_id):
        event = get_object_or_404(Event, id=event_id, organizer=request.user)
        return render(request, 'events/confirm_integration.html', {'event': event})

    def post(self, request, event_id):
        event = get_object_or_404(Event, id=event_id, organizer=request.user)

        # Remove 'without_payment' option and only allow 'with_payment'
        if 'with_payment' in request.POST:
            return redirect('setup_razorpay', event_id=event.id)


class RazorPaySetupView(View):
    def get(self, request, event_id):
        event = get_object_or_404(Event, id=event_id, organizer=request.user)
        return render(request, 'events/setup_razorpay.html', {'event': event})

    def post(self, request, event_id):
        event = get_object_or_404(Event, id=event_id, organizer=request.user)
        payment_page_url = request.POST.get('payment_page_url')

        if not payment_page_url:
            messages.error(request, "")
            return redirect('setup_razorpay', event_id=event.id)

        # Save Razorpay Payment Page URL to the Event model
        event.payment_page_url = payment_page_url
        event.save()

        messages.success(request, "Payment integration setup successfully!")
        return redirect('upcoming_events')  # Redirect to the list of upcoming events

# Custom Logout View
class CustomLogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('landing_page')

# Password reset form view
class CustomPasswordResetView(PasswordResetView):
    template_name = 'registration/password_reset_form.html'
    email_template_name = 'registration/password_reset_email.html'
    subject_template_name = 'registration/password_reset_subject.txt'  # Optional: Add a subject line template
    success_url = '/password_reset/done/'  # Redirect after the form is submitted

# Password reset done view
class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'registration/password_reset_done.html'

# Password reset confirm view
class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'registration/password_reset_confirm.html'  # You will create this template
    success_url = '/reset/done/'  # Redirect after resetting the password

# Password reset complete view
class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'registration/password_reset_complete.html'

# Profile View
class ProfileView(LoginRequiredMixin, View):
    login_url = '/login/'

    def get(self, request):
        # Get the current user profile data
        user = request.user
        return render(request, 'events/profile.html', {'user': user})