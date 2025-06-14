from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .forms import SignUpForm, LoginForm
from .models import *
import json
from django.http import JsonResponse

# This is the main logic file. Each function (view) handles a web request
# and returns a response, typically by rendering an HTML template with context data.

# --- Authentication Views ---

def login_view(request):
    """Handles user login."""
    if request.user.is_authenticated:
        return redirect('Dashboards')
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('Dashboards')
        # If form is invalid or auth fails, re-render with the form (which now has errors)
    else:
        form = LoginForm()
    return render(request, 'frontend/template/login.html', {'form': form})

def signup_view(request):
    """Handles new user registration."""
    if request.user.is_authenticated:
        return redirect('Dashboards')
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.user_type = 'practitioner' # Default new signups to practitioners
            user.save()
            # Create a practitioner profile for the new user
            Practitioner.objects.create(user=user, business_name=f"{user.username}'s Practice")
            login(request, user)
            return redirect('Dashboards')
        # If form is invalid, re-render with the form (which now has errors)
    else:
        form = SignUpForm()
    return render(request, 'frontend/template/sign-up.html', {'form': form})

def logout_view(request):
    """Logs the current user out."""
    logout(request)
    return redirect('login')

# --- Main Page Views ---
# All main views now render the same portal shell.
# The `page` context variable tells the frontend JavaScript which content to load.

@login_required
def dashboard_view(request):
    """Renders the main dashboard page."""
    context = {'page': 'Dashboards'}
    return render(request, 'frontend/template/portal.html', context)

@login_required
def communications_view(request):
    """Renders the communications page."""
    context = {'page': 'Communications'}
    return render(request, 'frontend/template/portal.html', context)
    
@login_required
def calendar_view(request):
    """Renders the calendar page."""
    context = {'page': 'Calendar'}
    return render(request, 'frontend/template/portal.html', context)

@login_required
def appointments_view(request):
    """Renders the appointments management page."""
    context = {'page': 'Appointments'}
    return render(request, 'frontend/template/portal.html', context)

@login_required
def clients_view(request):
    """Renders the client management page."""
    # Backend can still fetch data, but it will be used by API calls from JS
    clients = Client.objects.filter(practitioners__user=request.user)
    context = {
        'page': 'Clients',
        # 'clients': clients # This data will be fetched by an API call instead
    }
    return render(request, 'frontend/template/portal.html', context)

@login_required
def ai_voice_assistant_view(request):
    """Renders the AI voice assistant page."""
    context = {'page': 'AI Voice Assistant'}
    return render(request, 'frontend/template/portal.html', context)
    
@login_required
def reports_view(request):
    """Renders the reports page."""
    context = {'page': 'Reports'}
    return render(request, 'frontend/template/portal.html', context)

@login_required
def web_services_view(request):
    """Renders the web services/plugins page."""
    context = {'page': 'Web Services'}
    return render(request, 'frontend/template/portal.html', context)

@login_required
def settings_view(request):
    """Renders the settings page."""
    context = {'page': 'Settings'}
    return render(request, 'frontend/template/portal.html', context)

@login_required
def my_payments_view(request):
    """Renders the payments dashboard for the practitioner."""
    context = {'page': 'My Payments'}
    return render(request, 'frontend/template/portal.html', context)

@login_required
def profile_view(request):
    """Renders the user profile page."""
    context = {'page': 'Profile'}
    return render(request, 'frontend/template/portal.html', context)

# --- Modal/Action Views ---
@login_required
def new_appointment_view(request):
    """View to handle creation of a new appointment (could be from a modal)."""
    # This view would handle the POST request from the new appointment modal
    # For now, it just redirects back to the dashboard.
    # In a full implementation, it would create an Appointment object via an API call.
    return redirect('Dashboards')


# --- API/AJAX Views ---

@login_required
def get_calendar_events(request):
    """
    Provides appointment data in JSON format for the full calendar.
    Filters events based on start and end dates provided in the request.
    """
    start = request.GET.get('start')
    end = request.GET.get('end')
    
    # Assuming practitioner is logged in
    try:
        practitioner = request.user.practitioner_profile
    except Practitioner.DoesNotExist:
        return JsonResponse({"error": "Practitioner profile not found"}, status=404)

    
    appointments = Appointment.objects.filter(
        practitioner=practitioner,
        date__range=[start, end]
    )
    
    events = []
    for appt in appointments:
        events.append({
            'id': appt.id,
            'title': f"{appt.client.user.first_name} - {appt.appointment_type.name}",
            'start': f"{appt.date}T{appt.start_time}",
            'end': f"{appt.date}T{appt.end_time}",
            'className': f"event-{getattr(appt.appointment_type, 'color', 'session') or 'session'}" # Example class
        })
        
    return JsonResponse(events, safe=False)
