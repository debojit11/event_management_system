import razorpay
from django.db.models import Q
from django.conf import settings
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.views import View
from django.views.generic import ListView, UpdateView, TemplateView, DeleteView
from django.views.generic.edit import FormView
from django.core.mail import send_mail
from django.urls import reverse_lazy, reverse
from django.utils.timezone import now
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Event, Ticket, Attendee
from django.contrib.auth.forms import AuthenticationForm
from .forms import EventForm, CustomUserCreationForm, TicketForm, SupportForm
from reportlab.pdfgen import canvas
from io import BytesIO
from reportlab.lib.pagesizes import inch, letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

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

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Add the 'transparent-textarea' class to the fields
        form.fields['username'].widget.attrs.update({
            'class': 'transparent-textarea',
            'placeholder': 'Username',
        })
        form.fields['password'].widget.attrs.update({
            'class': 'transparent-textarea',
            'placeholder': 'Password',
        })
        return form

# Upcoming Events View (Login Required)
class UpcomingEventsView(LoginRequiredMixin, View):
    login_url = '/login/'
    redirect_field_name = 'next'

    def get(self, request):
        # Get the search query from GET parameters
        search_query = request.GET.get('q', '')
        
        # Filter events by end date and search query
        events = Event.objects.filter(
            end_date__gte=now()
        )
        
        if search_query:
            events = events.filter(
                Q(name__icontains=search_query) | 
                Q(description__icontains=search_query) | 
                Q(location__icontains=search_query)
            )

        # Paginate the filtered events
        paginator = Paginator(events, 10)  # 10 events per page
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        # Pass the paginated events and search query to the template
        return render(request, 'events/upcoming_events.html', {
            'events': page_obj,
            'search_query': search_query,
        })

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
        
        if ticket.available_quantity() <= 0:
            messages.error(request, "Sorry, no tickets are available for this event.")
            return redirect('ticket_select', event_id=event_id)

        # Create an Attendee entry for the user
        attendee, created = Attendee.objects.get_or_create(
            user=request.user,
            event=event,
            defaults={'ticket': ticket}
        )

        if created:
            ticket.quantity -= 1
            ticket.save()
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

        # Card dimensions: 3.5 inches x 6 inches
        card_width = 3.5 * inch
        card_height = 6 * inch

        # Create a PDF in memory with the specified size
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=(card_width, card_height))

        # Set background color (light gray for example)
        p.setFillColor(colors.lightgrey)
        p.rect(0, 0, card_width, card_height, fill=1)

        # Add a header
        p.setFont("Helvetica-Bold", 16)
        p.setFillColor(colors.darkblue)
        p.drawString(20, card_height - 40, "Event Ticket")

        # Draw a horizontal line under the header
        p.setStrokeColor(colors.darkblue)
        p.setLineWidth(2)
        p.line(10, card_height - 50, card_width - 10, card_height - 50)

        # Add ticket details with spacing and custom fonts
        p.setFont("Helvetica", 12)
        p.setFillColor(colors.black)
        details = [
            f"Event Name: {attendee.event.name}",
            f"Location: {attendee.event.location}",
            f"Attendee: {attendee.user.first_name} {attendee.user.last_name}",
            f"Email: {attendee.user.email}",
            f"Ticket Type: {attendee.ticket.ticket_type}",
        ]

        y = card_height - 80  # Starting height for details
        for detail in details:
            p.drawString(20, y, detail)
            y -= 20  # Spacing between lines

        # Add a footer
        p.setFont("Helvetica-Oblique", 10)
        p.setFillColor(colors.grey)
        p.drawString(20, 20, "Thank you for attending!")

        # Finish up
        p.showPage()
        p.save()

        # Set up the response as a PDF file
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{attendee.event.name}_ticket.pdf"'

        return response
    
class DownloadAttendeeListView(LoginRequiredMixin, View):
    login_url = '/login/'

    def get(self, request, pk):
        # Get the event and its attendees
        event = get_object_or_404(Event, pk=pk)
        attendees = event.attendees.all()

        # Create a PDF in memory
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []

        # Add title
        title = f"Attendee List for {event.name}"
        elements.append(Table([[title]], style=[('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                                ('FONTSIZE', (0, 0), (-1, -1), 16)]))
        elements.append(Table([[""]]))  # Empty row for spacing

        # Add attendee details as a table
        data = [["First Name", "Last Name", "Email", "Ticket Type", "Payment Confirmed"]]
        for attendee in attendees:
            data.append([
                attendee.first_name,
                attendee.last_name,
                attendee.email,
                attendee.ticket.ticket_type,
                "Yes" if attendee.registration_status else "No"
            ])

        # Style the table
        table = Table(data, colWidths=[100, 100, 150, 120, 120])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(table)

        # Build the PDF
        doc.build(elements)

        # Set up the response as a PDF file
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{event.name}_attendees.pdf"'
        return response

class CreatedEventsView(LoginRequiredMixin, View):
    login_url = '/login/'  # Redirect to login page if not authenticated

    def get(self, request):
        user = request.user

        # Events organized by the user (assuming the user is the event organizer)
        created_events = Event.objects.filter(organizer=user)

        # Paginate events (10 events per page)
        paginator = Paginator(created_events, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # Pass the paginated events to the template
        context = {'page_obj': page_obj}
        return render(request, 'events/created_events.html', context)
    
class ManageEventView(LoginRequiredMixin, UpdateView):
    model = Event
    fields = ['name', 'description', 'start_date', 'end_date', 'location', 'speakers', 'payment_page_url']
    template_name = 'events/manage_event.html'
    success_url = '/my-events/'  # Redirect back to 'My Events' after saving

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add attendees and tickets to the context
        context['attendees'] = self.object.attendees.all()
        context['tickets'] = self.object.tickets.all()
        return context


class DeleteEventView(LoginRequiredMixin, DeleteView):
    model = Event
    template_name = 'events/delete_event.html'
    success_url = '/my-events/'  # Redirect back to 'My Events' after deletion

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
    
class DeleteTicketView(LoginRequiredMixin, DeleteView):
    model = Ticket
    template_name = 'events/delete_ticket.html'
    
    def get_success_url(self):
        # Redirect back to the manage event page after deletion
        event = self.object.event
        return reverse('manage_event', kwargs={'pk': event.id})

    def get_queryset(self):
        # Ensure only the organizer can delete tickets for their events
        return super().get_queryset().filter(event__organizer=self.request.user)


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

    def post(self, request):
        # Handle form submission to update user profile
        user = request.user
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')

        # Update user fields
        user.username = username
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.save()

        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')
    

class SupportPageView(View):
    def get(self, request, *args, **kwargs):
        # Initialize the form when the page is accessed via GET request
        form = SupportForm()
        return render(request, 'events/support_page.html', {'form': form})

    def post(self, request, *args, **kwargs):
        form = SupportForm(request.POST)
        if form.is_valid():
            # Get the message from the form
            message = form.cleaned_data['message']

            # Send email to the support team
            send_mail(
                'Support Request',
                message,
                settings.DEFAULT_FROM_EMAIL,  # Your from email address
                [settings.SUPPORT_EMAIL],  # Support email configured in settings.py
                fail_silently=False,
            )

            # Add success message to show confirmation to the user
            messages.success(request, 'Your support request has been sent successfully.')
            return redirect(reverse_lazy('support_page'))  # Redirect after success

        # If the form is invalid, re-render the page with errors
        messages.error(request, 'Please provide a message.')
        return render(request, 'events/support_page.html', {'form': form})