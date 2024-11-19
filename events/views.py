import razorpay
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.views import View
from django.views.generic import ListView, UpdateView, TemplateView, DeleteView
from django.urls import reverse_lazy
from django.utils.timezone import now
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Event, Ticket, Attendee
from .forms import EventForm, CustomUserCreationForm, TicketForm
from reportlab.pdfgen import canvas
from io import BytesIO

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
        # Only show events with an end_date in the future
        events = Event.objects.filter(end_date__gte=now())
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
            return redirect('ticket_select', event_id=event_id)

        try:
            ticket = Ticket.objects.get(id=ticket_id, event=event)
        except Ticket.DoesNotExist:
            messages.error(request, "Invalid ticket selected.")
            return redirect('ticket_select', event_id=event_id)

        # Create an Attendee entry for the user
        attendee, created = Attendee.objects.get_or_create(
            user=request.user,
            event=event,
            defaults={'ticket': ticket}
        )

        if created:
            messages.success(request, "You have successfully registered for the event!")
        else:
            messages.info(request, "You are already registered for this event.")

        # Redirect to the payment page
        return redirect(event.payment_page_url)

class MyEventsView(LoginRequiredMixin, View):
    login_url = '/login/'  # Redirect to login page if not authenticated
    template_name = 'events/my_events.html'

    def get(self, request):
        # Get the current user
        user = request.user

        # Registered events for the user
        registered_events = Attendee.objects.filter(user=user)

        # Events organized by the user (assuming the user is the event organizer)
        created_events = Event.objects.filter(organizer=user)

        # Render the template with the events context
        context = {
            'registered_events': registered_events,
            'created_events': created_events
        }
        return render(request, self.template_name, context)
    
class RegisteredEventsView(LoginRequiredMixin, View):
    login_url = '/login/'  # Redirect to login page if not authenticated

    def get(self, request):
        user = request.user

        # Registered events for the user
        registered_events = Attendee.objects.filter(user=user)

        # Pass the registered events to the template
        context = {'registered_events': registered_events}
        return render(request, 'events/registered_events.html', context)
    
class RegisteredEventDetailView(LoginRequiredMixin, View):
    login_url = '/login/'  # Redirect to login page if not authenticated

    def get(self, request, pk):
        user = request.user

        # Get the attendee record for the logged-in user and the specified event
        try:
            attendee = Attendee.objects.get(pk=pk, user=user)
        except Attendee.DoesNotExist:
            return redirect('registered_events')  # Redirect if not found

        # Pass the event details to the template
        context = {'attendee': attendee}
        return render(request, 'events/registered_event_detail.html', context)

class DownloadTicketView(LoginRequiredMixin, View):
    login_url = '/login/'

    def get(self, request, pk):
        user = request.user

        # Get the attendee record
        try:
            attendee = Attendee.objects.get(pk=pk, user=user)
        except Attendee.DoesNotExist:
            return redirect('registered_events')

        # Create a PDF in memory
        buffer = BytesIO()
        p = canvas.Canvas(buffer)

        # Add ticket details to the PDF
        p.drawString(100, 800, f"Event Name: {attendee.event.name}")
        p.drawString(100, 780, f"Location: {attendee.event.location}")
        p.drawString(100, 760, f"Attendee Name: {attendee.user.first_name} {attendee.user.last_name}")
        p.drawString(100, 740, f"Email: {attendee.user.email}")
        p.drawString(100, 720, f"Ticket Type: {attendee.ticket.ticket_type}")

        # Finish up
        p.showPage()
        p.save()

        # Set up the response as a PDF file
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{attendee.event.name}_ticket.pdf"'

        return response

class CreatedEventsView(LoginRequiredMixin, View):
    login_url = '/login/'  # Redirect to login page if not authenticated

    def get(self, request):
        user = request.user

        # Events organized by the user (assuming the user is the event organizer)
        created_events = Event.objects.filter(organizer=user)

        # Pass the created events to the template
        context = {'created_events': created_events}
        return render(request, 'events/created_events.html', context)
    
class ManageEventView(LoginRequiredMixin, UpdateView):
    model = Event
    fields = ['name', 'description', 'start_date', 'end_date', 'location', 'speakers', 'payment_page_url']
    template_name = 'events/manage_event.html'
    success_url = '/my-events/'  # Redirect back to 'My Events' after saving

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add attendees to the context
        context['attendees'] = self.object.attendees.all()
        return context

class DeleteEventView(LoginRequiredMixin, DeleteView):
    model = Event
    template_name = 'events/delete_event.html'
    success_url = '/my_events/'  # Redirect back to 'My Events' after deletion

    def get_queryset(self):
        # Ensure that only the organizer can delete their events
        queryset = super().get_queryset()
        return queryset.filter(organizer=self.request.user)


class ConfirmRegistrationView(LoginRequiredMixin, UpdateView):
    model = Attendee
    fields = ['registration_status']
    template_name = 'events/confirm_registration.html'
    success_url = reverse_lazy('my_events')

    def form_valid(self, form):
        attendee = form.save(commit=False)
        if attendee.event.organizer != self.request.user:
            # Only the event creator can confirm registrations
            return redirect('my_events')
        attendee.registration_status = True
        attendee.save()
        return super().form_valid(form)

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