from django.urls import path
from . import views

urlpatterns = [
    # Landing page and authentication
    path('', views.LandingPageView.as_view(), name='landing_page'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('signup/', views.SignupView.as_view(), name='signup'),

    # Profile Page
    path('profile/', views.ProfileView.as_view(), name='profile'),

    # Event-related URLs
    path('events/', views.UpcomingEventsView.as_view(), name='upcoming_events'),
    path('event/<int:event_id>/', views.EventDetailView.as_view(), name='event_detail'),
    path('<int:event_id>/ticket-select/', views.TicketSelectView.as_view(), name='ticket_select'),
    path('<int:event_id>/proceed-to-payment/', views.TicketPaymentView.as_view(), name='proceed_to_payment'),
    path('my-events/', views.MyEventsView.as_view(), name='my_events'),
    path('create-event/', views.CreateEventView.as_view(), name='create_event'),
    path('events/<int:event_id>/create-ticket/', views.CreateTicketView.as_view(), name='create_ticket'),
    path('events/<int:event_id>/confirm-integration/', views.ConfirmIntegrationView.as_view(), name='confirm_integration'),
    path('events/<int:event_id>/setup-razorpay/', views.RazorPaySetupView.as_view(), name='setup_razorpay'),

    # Password reset URLs
    path('password_reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', views.CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', views.CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),
]