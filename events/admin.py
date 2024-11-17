from django.contrib import admin
from .models import Event, Ticket, Attendee
# Register your models here.

# Event admin
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'start_date', 'end_date', 'created_at',['organizer'], 'payment_page_url')
    search_fields = ('name', 'location')
    list_filter = ('start_date', 'end_date')

# Ticket admin
class TicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_type', 'event', 'price', 'quantity', 'created_at')
    search_fields = ('ticket_type', 'event__name')  # You can search by event name
    list_filter = ('event',)

# Attendee admin
class AttendeeAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'ticket', 'created_at')
    search_fields = ('user__username', 'event__name', 'ticket__ticket_type')
    list_filter = ('event',)



admin.site.register(Event)
admin.site.register(Ticket)
admin.site.register(Attendee)