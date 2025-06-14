from django.urls import path
from . import views

# This file maps URL patterns to views in the 'home' app.
# Each path() call defines a route, the view function to execute, and a name for easy reference.

urlpatterns = [
    # Main Dashboard
    path('', views.dashboard_view, name='Dashboards'),

    # Page Views
    path('communications/', views.communications_view, name='Communications'),
    path('calendar/', views.calendar_view, name='Calendar'),
    path('appointments/', views.appointments_view, name='Appointments'),
    path('clients/', views.clients_view, name='Clients'),
    path('ai-voice-assistant/', views.ai_voice_assistant_view, name='AI Voice Assistant'),
    path('reports/', views.reports_view, name='Reports'),
    path('web-services/', views.web_services_view, name='Web Services'),
    path('settings/', views.settings_view, name='Settings'),
    path('my-payments/', views.my_payments_view, name='My Payments'),
    path('profile/', views.profile_view, name='Profile'),

    # Authentication
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),

    # AJAX/API endpoints (examples)
    path('api/calendar-events/', views.get_calendar_events, name='api_calendar_events'),
    
    # Modals and Actions
    path('appointments/new/', views.new_appointment_view, name='new_appointment'),
]
