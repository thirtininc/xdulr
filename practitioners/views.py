# practitioners/views.py

#<--PYTHON STANDARD LIBRARY IMPORTS-->
import base64
import calendar
import csv
import hashlib
import json
import logging
import os
import re
import secrets
import string
import xml.etree.ElementTree as ET
from datetime import date, datetime, time, timedelta
from decimal import Decimal, InvalidOperation
from io import BytesIO
from multiprocessing import Value
from operator import concat
from uuid import uuid4
import openai
from PIL import Image
import io
import fitz
import traceback
import uuid

#<--THIRD-PARTY LIBRARY IMPORTS-->
import aiohttp
import msal
import pyotp
import pytz
import qrcode
import requests
import stripe
import telnyx
import numpy as np
import re
from asgiref.sync import sync_to_async
from fuzzywuzzy import fuzz
from fuzzywuzzy import process as fuzzy_process
from google.api_core import exceptions as google_exceptions
from google.cloud import documentai
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

#<--DJANGO FRAMEWORK IMPORTS-->
from django.utils.dateparse import parse_datetime
from django.db.models import Exists
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import (authenticate, login, logout,
                                 update_session_auth_hash)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import (AuthenticationForm, PasswordChangeForm,
                                     PasswordResetForm)
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage, send_mail
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, F, Q, Sum, OuterRef, Subquery
from django.db.models.functions import Coalesce, TruncMonth, Concat
from django.forms import CharField, Form
from django.http import (Http404, HttpResponse, HttpResponseRedirect,
                         JsonResponse)
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from django.views.generic import TemplateView
from django.db.models import Value
from django.db.models.functions import Concat
from django.core import serializers
from django.forms.models import model_to_dict
import json
from django.core.serializers.json import DjangoJSONEncoder

#<--LOCAL APPLICATION IMPORTS-->
# Note: Some of these may need to be adjusted to absolute imports
from home.api_views import ApiWebsiteIntegrationView
from home import emails as custom_emails
from home.models import ClientForm
from home.emailHelper import send_email
from home.forms import ClientForm as ClientFormClass, Postform, PractitionerDataRequestForm, UserSignupForm
from home.helpers import (add_calendar_data, charge_through_stripe,
                    send_sms_via_telnyx, wallet_balance_required)
from home.models import ErrorLog, SystemService, User
from clients.models import Client
from .models import ( # Changed to relative import for this app
    AIAgent,
    Appointment,
    Availability,
    BillingDetails,
    CallLog,
    ClientConsent,
    ClientSubscriptionPlan,
    Conversation,
    Domain,
    EmailAccount,
    EmailLog,
    Form as AdvancedForm,
    PayStub,
    PractitionerDataRequest, Question,
    FormSubmission,
    Integration,
    KnowledgeBaseDocument,
    Message,
    Notification,
    NotificationSettings,
    Payment,
    PaymentHistory,
    PhoneOTP,
    Practitioner,
    PractitionerAPIKey,
    PractitionerSubscription,
    PractitionerWallet,
    Question,
    RecoveryCode,
    Service,
    SpecialAvailability,
    Staff,
    StaffAvailability,
    Subscription,
    SubscriptionPlan,
    Task,
    TelnyxLog,
    TelnyxPhoneNumber,
    VideoCall,
    WalletTransaction,
    WebsitePlugin,
)

#<--INITIALIZATIONS-->
logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY

# =============================================================================
# CORE APPLICATION VIEWS
# =============================================================================

#<-- DASHBOARD VIEW -->
@login_required
def Dashboard(request):
    """
    Dashboard view showing KPIs and visualizations for the logged-in practitioner.
    """
    if not hasattr(request.user, 'practitioner_profile'):
        # If the user is authenticated but not a practitioner, show a client dashboard.
        return render(request, 'frontend/template/index.html')

    practitioner = request.user.practitioner_profile
    activity_days = int(request.GET.get("activity_days", 90))

    today = timezone.now().date()
    start_date = today - timedelta(days=activity_days - 1)

    # --- KPI Calculations ---
    total_clients = Client.objects.filter(practitioners=practitioner).count()
    new_clients = Client.objects.filter(practitioners=practitioner, created_at__date__gte=start_date).count()
    appointments = Appointment.objects.filter(practitioner=practitioner, date__gte=start_date)
    total_appointments = appointments.count()

    total_revenue = Payment.objects.filter(
        appointment__practitioner=practitioner,
        payment_date__gte=start_date,
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or 0

    # --- Chart Data ---
    monthly_appointments = appointments.annotate(month=TruncMonth('date')).values('month').annotate(count=Count('id')).order_by('month')
    chart_labels = [entry['month'].strftime('%b %Y') for entry in monthly_appointments]
    chart_data = [entry['count'] for entry in monthly_appointments]

    # --- Context Preparation ---
    context = {
        'practitioner': practitioner,
        'total_clients': total_clients,
        'new_clients_this_month': new_clients,
        'total_appointments': total_appointments,
        'total_revenue_this_month': total_revenue,
        'upcoming_appointments': Appointment.objects.filter(practitioner=practitioner, date__gte=today, status__in=['pending', 'confirmed']).order_by('date', 'start_time')[:5],
        'recent_clients': Client.objects.filter(practitioners=practitioner).order_by('-created_at')[:5],
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
        "activity_days": activity_days,
    }

    # Add calendar data for the mini-calendar widget
    add_calendar_data(context, practitioner)

    return render(request, 'frontend/template/index.html', context)

#<-- USER PUBLIC BOOKING PAGE VIEW -->
class UserPublicPageView(View):
    """
    Renders the public booking page for a practitioner, accessed via a subdomain.
    """
    template_name = 'frontend/template/user_public_page.html'

    def get(self, request, *args, **kwargs):
        # The username is attached to the request by custom middleware
        username = request.subdomain_username

        try:
            user = User.objects.get(username=username)
            practitioner = Practitioner.objects.get(user=user)
            context = {'practitioner': practitioner}
            return render(request, self.template_name, context)
        except (User.DoesNotExist, Practitioner.DoesNotExist):
            return HttpResponse("Page not found", status=404)

#<-- PUBLIC PROFILE VIEW -->
class PublicProfile(LoginRequiredMixin, View):
    """
    Displays a practitioner's profile, services, and availability.
    Serves as both a public-facing page and a private overview for the owner.
    """
    template_name = 'frontend/template/public_profile.html'

    def get(self, request, practitioner_id=None):
        if not practitioner_id:
            if not hasattr(request.user, 'practitioner_profile'):
                messages.error(request, "You do not have a practitioner profile.")
                return redirect('practitioners:dashboard')
            practitioner = request.user.practitioner_profile
            is_owner = True
        else:
            practitioner = get_object_or_404(Practitioner, id=practitioner_id)
            is_owner = (hasattr(request.user, 'practitioner_profile') and
                       request.user.practitioner_profile.id == practitioner.id)

        context = {
            'practitioner': practitioner,
            'is_owner': is_owner,
            'services': Service.objects.filter(practitioner=practitioner, is_active=True).order_by('price'),
            'regular_availabilities': Availability.objects.filter(practitioner=practitioner, is_available=True).order_by('day_of_week', 'start_time')
        }

        # Add enhanced data for the profile owner's dashboard view
        if is_owner:
            context.update(self._get_owner_statistics(practitioner))

        return render(request, self.template_name, context)

    def _get_owner_statistics(self, practitioner):
        """Helper to calculate and return detailed statistics for the profile owner."""
        # This is a placeholder for the detailed statistics logic found in your original file.
        # In a production refactor, the extensive calculations from your original
        # PublicProfile view would go here to keep the GET method clean.
        stats = {
            'client_count': Client.objects.filter(practitioners=practitioner).count(),
            # ... other stats like revenue, appointments, etc.
        }
        return stats


#<-- SETTINGS VIEW -->
class Settings(LoginRequiredMixin, View):
    """
    Manages all practitioner settings across various tabs like Profile,
    Business Info, Account, Hours, Integrations, and Wallet.
    """
    template_name = 'frontend/template/settings.html'

    def get(self, request):
        practitioner = get_object_or_404(Practitioner, user=request.user)
        active_tab = request.GET.get('tab', 'profile')

        context = {
            'tab': active_tab,
            'practitioner': practitioner,
        }

        if active_tab == 'profile':
            data_request_settings, created = PractitionerDataRequest.objects.get_or_create(practitioner=practitioner)           
            data_request_form = PractitionerDataRequestForm(instance=data_request_settings)         
            context['data_request_form'] = data_request_form


        if active_tab == 'hours':
            availability_map = {avail.day_of_week: avail for avail in Availability.objects.filter(practitioner=practitioner)}
            weekdays_data = []
            for day_code, day_name in [(0, 'Sunday'), (1, 'Monday'), (2, 'Tuesday'), (3, 'Wednesday'), (4, 'Thursday'), (5, 'Friday'), (6, 'Saturday')]:
                weekdays_data.append({'code': day_code, 'name': day_name, 'availability': availability_map.get(day_code)})
            context['weekdays_data'] = weekdays_data

        elif active_tab == 'notifications':
            context['notification_settings'] = NotificationSettings.objects.get_or_create(practitioner=practitioner)[0]

        elif active_tab == 'account':
            context['remaining_codes'] = practitioner.recovery_codes.filter(used=False).count()

        elif active_tab == 'wallet':
            wallet, _ = PractitionerWallet.objects.get_or_create(practitioner=practitioner)
            context['wallet'] = wallet
            context['transactions'] = wallet.transactions.all().order_by('-created_at')[:20]
            context['stripe_publishable_key'] = settings.STRIPE_PUBLISHABLE_KEY

        elif active_tab == 'forms':
            context['forms'] = ClientForm.objects.filter(practitioner=practitioner)
            context['advanced_forms'] = AdvancedForm.objects.filter(practitioner=practitioner)

        elif active_tab == 'support':
            context['system_status'] = SystemService.objects.all().order_by('name')
            context['error_count_24h'] = ErrorLog.objects.filter(timestamp__gte=timezone.now() - timedelta(days=1)).count()
            context['recent_error_logs'] = ErrorLog.objects.all().order_by('-timestamp')[:10]

            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            context['user_ip'] = x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')
            context['is_secure_connection'] = request.is_secure()

        elif active_tab == 'subscription':
            context['active_subscriptions'] = {sub.subscription_type for sub in Subscription.objects.filter(practitioner=practitioner, is_active=True)}
            context['staff_count'] = Staff.objects.filter(practitioner=practitioner).count()

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        practitioner = get_object_or_404(Practitioner, user=request.user)
        action = request.POST.get('action')

        # --- Profile Tab ---
        if action == 'save_business_info':
            practitioner.business_name = request.POST.get('business_name', practitioner.business_name)
            practitioner.business_phone = request.POST.get('business_phone', practitioner.business_phone)
            practitioner.business_address = request.POST.get('business_address', practitioner.business_address)
            practitioner.website_url = request.POST.get('website_url', practitioner.website_url)
            practitioner.professional_bio = request.POST.get('professional_bio', practitioner.professional_bio)
            request.user.email = request.POST.get('email', request.user.email)
            practitioner.save()
            request.user.save()
            messages.success(request, 'Business profile updated successfully.')
            return redirect(f"{reverse('practitioners:settings')}?tab=profile")

        elif action == 'save_profile_details':
            if 'profile_picture' in request.FILES:
                practitioner_profile = request.user.practitioner_profile
                practitioner_profile.profile_pic = request.FILES['profile_picture']
                practitioner_profile.save()             
                messages.success(request, 'Profile picture updated successfully!')
            else:
                messages.error(request, 'No file was selected.')
                return redirect(reverse('practitioners:settings') + '?tab=profile')

        if action == 'save_consent_settings':
            data_request_settings = get_object_or_404(PractitionerDataRequest, practitioner=practitioner)
            form = PractitionerDataRequestForm(request.POST, instance=data_request_settings)
            
            if form.is_valid():
                form.save()
                messages.success(request, 'Client data and consent settings have been updated.')
            else:
                messages.error(request, 'There was an error saving your settings. Please check the form.')
            
            return redirect(f"{reverse('practitioners:settings')}?tab=profile")


        # --- Hours Tab ---
        elif action == 'save_availability':
            for i in range(7):
                is_available = f'available_{i}' in request.POST
                start_time_str = request.POST.get(f'start_time_{i}')
                end_time_str = request.POST.get(f'end_time_{i}')
                if is_available and start_time_str and end_time_str:
                    Availability.objects.update_or_create(
                        practitioner=practitioner, day_of_week=i,
                        defaults={'start_time': start_time_str, 'end_time': end_time_str, 'is_available': True}
                    )
                else:
                    Availability.objects.filter(practitioner=practitioner, day_of_week=i).update(is_available=False)
            messages.success(request, 'Availability updated successfully.')
            return redirect(f"{reverse('practitioners:settings')}?tab=hours")

        # --- Booking Rules Tab ---
        elif action == 'save_booking_rules':
            practitioner.minimum_booking_lead_time = request.POST.get('lead_time', 24)
            practitioner.cancellation_policy = request.POST.get('cancellation_policy', '')
            practitioner.save()
            messages.success(request, "Booking policies saved successfully.")
            return redirect(f"{reverse('practitioners:settings')}?tab=booking_rules")

        # --- Notifications Tab ---
        if action == 'save_notification_settings':
            settings, _ = NotificationSettings.objects.get_or_create(practitioner=practitioner)
            settings.booking_reminders = 'booking_reminders' in request.POST
            settings.new_bookings = 'new_bookings' in request.POST
            settings.changes_made = 'changes_made' in request.POST
            settings.platform_updates = 'platform_updates' in request.POST
            settings.marketing_offers = 'marketing_offers' in request.POST
            settings.save()
            messages.success(request, "Notification settings updated.")
            return redirect(f"{reverse('practitioners:settings')}?tab=notifications")

        elif action == 'save_wallet_settings':
            wallet = get_object_or_404(PractitionerWallet, practitioner=practitioner)
            wallet.auto_recharge_enabled = 'auto_recharge_enabled' in request.POST
            wallet.recharge_threshold = Decimal(request.POST.get('recharge_threshold', '10.00'))
            wallet.recharge_amount = Decimal(request.POST.get('recharge_amount', '20.00'))
            wallet.save()
            messages.success(request, "Auto-recharge settings updated.")
            return redirect(f"{reverse('practitioners:settings')}?tab=wallet")

        # --- Integrations Tab ---
        elif action == 'disconnect_google':
            practitioner.is_google_calendar_synced = False
            practitioner.google_credentials = None
            practitioner.save()
            messages.success(request, "Google Calendar has been disconnected.")
            return redirect(f"{reverse('practitioners:settings')}?tab=integrations")

        # --- Account Tab ---
        elif action == 'save_password':
            form = PasswordChangeForm(user=request.user, data=request.POST)
            if form.is_valid():
                form.save()
                update_session_auth_hash(request, form.user)
                messages.success(request, 'Your password was successfully updated!')
            else:
                for error in form.errors.values():
                    messages.error(request, error)
            return redirect(f"{reverse('practitioners:settings')}?tab=account")

        # --- Forms Tab ---
        elif action == 'save_form':
            form_id = request.POST.get('form_id')
            title = request.POST.get('title')
            content = request.POST.get('content')
            if form_id:
                ClientForm.objects.filter(id=form_id, practitioner=practitioner).update(title=title, content=content)
                messages.success(request, "Form updated successfully.")
            else:
                ClientForm.objects.create(practitioner=practitioner, title=title, content=content)
                messages.success(request, "Form created successfully.")
            return redirect(f"{reverse('practitioners:settings')}?tab=forms")

        elif action == 'delete_form':
            form_id = request.POST.get('form_id')
            get_object_or_404(ClientForm, id=form_id, practitioner=practitioner).delete()
            messages.success(request, "Form deleted successfully.")
            return redirect(f"{reverse('practitioners:settings')}?tab=forms")

        elif action == 'deactivate_account':
            user = request.user
            user.is_active = False
            user.save()
            logout(request)
            messages.success(request, "Your account has been deactivated.")
            return redirect('home:login') # Redirect to the login page after deactivation

        return redirect('practitioners:settings')

#<-- NOTIFICATIONS VIEW -->
class Notifications(LoginRequiredMixin, View):
    """
    Displays a paginated list of all notifications for the practitioner.
    """
    template_name = 'frontend/template/notifications.html'

    def get(self, request):
        notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
        paginator = Paginator(notifications, 10) # 10 notifications per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context = {
            'notifications': page_obj
        }
        return render(request, self.template_name, context)

#<-- MARK NOTIFICATIONS AS READ VIEW (API) -->
class MarkNotificationsAsReadView(LoginRequiredMixin, View):
    """
    API endpoint to mark all of the user's unread notifications as read.
    """
    def post(self, request, *args, **kwargs):
        try:
            Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
            return JsonResponse({'status': 'success'})
        except Exception as e:
            logger.error(f"Error marking notifications as read for user {request.user.id}: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

#<-- DEMAND FORECASTING VIEW -->
class DemandForecastingView(LoginRequiredMixin, View):
    """
    A placeholder view for a future demand forecasting feature.
    """
    template_name = 'frontend/template/demand_forecasting.html'

    def get(self, request):
        context = {
            'page_title': 'Demand Forecasting',
            'coming_soon': True,
        }
        return render(request, self.template_name, context)

# =============================================================================
# AUTHENTICATION & SECURITY VIEWS (MOVED FROM HOME APP)
# =============================================================================

#<-- SETUP AUTHENTICATOR VIEW (API) -->
@login_required
def setup_authenticator_view(request):
    """
    Generates a new TOTP secret and QR code for the user to scan.
    """
    practitioner = request.user.practitioner_profile

    # Generate a new secret key
    secret_key = pyotp.random_base32()

    # Store the temporary secret in the session until it's verified
    request.session['totp_secret_temp'] = secret_key

    # Create the provisioning URI
    totp = pyotp.TOTP(secret_key)
    provisioning_uri = totp.provisioning_uri(
        name=request.user.email,
        issuer_name="XDULR"
    )

    # Generate the QR code image
    img = qrcode.make(provisioning_uri)
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    qr_code_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

    return JsonResponse({
        'secret_key': secret_key,
        'qr_code': qr_code_base64
    })

#<-- VERIFY AUTHENTICATOR SETUP VIEW (API) -->
@login_required
@require_POST
def verify_authenticator_view(request):
    """
    Verifies the OTP from the user during setup and enables authenticator 2FA.
    """
    practitioner = request.user.practitioner_profile
    secret_key = request.session.get('totp_secret_temp')
    otp = request.POST.get('otp')

    if not secret_key or not otp:
        return JsonResponse({'success': False, 'error': 'Invalid request.'}, status=400)

    totp = pyotp.TOTP(secret_key)
    if totp.verify(otp):
        # OTP is correct, save the secret and enable the feature
        practitioner.totp_secret = secret_key
        practitioner.authenticator_2fa_enabled = True
        practitioner.save()

        if 'totp_secret_temp' in request.session:
            del request.session['totp_secret_temp']

        messages.success(request, "Authenticator app enabled successfully!")
        request.session['2fa_setup_complete'] = True # Set flag to show recovery codes
        return JsonResponse({'success': True, 'redirect_url': reverse('practitioners:show_recovery_codes')})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid code. Please try again.'})

#<-- DISABLE AUTHENTICATOR VIEW -->
@login_required
@require_POST
def disable_authenticator_view(request):
    """
    Disables Authenticator App 2FA for the user.
    """
    practitioner = request.user.practitioner_profile
    practitioner.authenticator_2fa_enabled = False
    practitioner.totp_secret = None
    practitioner.save()
    messages.success(request, "Authenticator app has been disabled.")
    return redirect(reverse('practitioners:settings') + '?tab=account')

#<-- GENERATE RECOVERY CODES (HELPER) -->
def generate_and_save_recovery_codes(practitioner):
    """
    Generates 10 new recovery codes, deletes old ones, saves hashed versions,
    and returns the plaintext codes to be shown to the user once.
    """
    practitioner.recovery_codes.all().delete()
    plaintext_codes = []

    for _ in range(10):
        code = f"{''.join(secrets.choice(string.ascii_uppercase + string.digits) for i in range(4))}-{''.join(secrets.choice(string.ascii_uppercase + string.digits) for i in range(4))}"
        plaintext_codes.append(code)
        RecoveryCode.objects.create(
            practitioner=practitioner,
            code=make_password(code) # Store hashed code
        )
    return plaintext_codes

#<-- SHOW RECOVERY CODES VIEW -->
class ShowRecoveryCodesView(LoginRequiredMixin, View):
    """
    Displays newly generated recovery codes to the user.
    This view is shown only once after setting up or re-enabling 2FA.
    """
    template_name = 'frontend/template/show_recovery_codes.html'

    def get(self, request):
        if not request.session.pop('2fa_setup_complete', False):
            messages.error(request, "You can only view new codes after setting up two-factor authentication.")
            return redirect(reverse('practitioners:settings') + '?tab=account')

        practitioner = get_object_or_404(Practitioner, user=request.user)
        codes = generate_and_save_recovery_codes(practitioner)

        return render(request, self.template_name, {'recovery_codes': codes})

#<-- REGENERATE RECOVERY CODES VIEW -->
@login_required
@require_POST
def regenerate_recovery_codes_view(request):
    """
    Sets the session flag and redirects to the view that generates and shows new codes.
    """
    request.session['2fa_setup_complete'] = True
    return redirect('practitioners:show_recovery_codes')

#<-- TOGGLE 2FA VIEW -->
@login_required
@require_POST
def toggle_2fa(request):
    """
    Toggles SMS-based two-factor authentication for the practitioner.
    """
    practitioner = get_object_or_404(Practitioner, user=request.user)
    
    # The checkbox sends 'on' when checked, and nothing when unchecked.
    is_enabled = 'two_factor_enabled' in request.POST
    
    practitioner.sms_2fa_enabled = is_enabled
    practitioner.save()
    
    if is_enabled:
        messages.success(request, "SMS two-factor authentication has been enabled.")
    else:
        messages.success(request, "SMS two-factor authentication has been disabled.")
        
    # Redirect back to the account settings tab
    return redirect(reverse('practitioners:settings') + '?tab=account')




# =============================================================================
# CLIENT MANAGEMENT VIEWS
# =============================================================================

#<-- CLIENTS LIST VIEW -->
class Clients(LoginRequiredMixin, View):
    """
    Displays a paginated and filterable list of all clients for a practitioner.
    """
    template_name = 'frontend/template/clients.html'

    def get(self, request):
        practitioner = get_object_or_404(Practitioner, user=request.user)

        # Filtering logic
        search_query = request.GET.get('search', '')
        status_filter = request.GET.get('status', 'all')
        sort_by = request.GET.get('sort', 'name_asc')


        # 1. Annotate the queryset with the last appointment date for sorting
        last_appointment_subquery = Appointment.objects.filter(
            client=OuterRef('pk'),
            practitioner=practitioner
        ).order_by('-date').values('date')[:1]

        # Use a new, non-conflicting name for the annotation
        clients = Client.objects.filter(practitioners=practitioner).annotate(
            annotated_last_appointment_date=Subquery(last_appointment_subquery)
        )

        # 2. Apply search and status filters
        if search_query:
            clients = clients.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(email__icontains=search_query)
            )

        if status_filter != 'all':
            clients = clients.filter(status=status_filter)

        # 3. Expanded sorting logic (using the new annotation name)
        if sort_by == 'recent':
            clients = clients.order_by('-created_at')
        elif sort_by == 'name_desc':
            clients = clients.order_by('-first_name', '-last_name')
        elif sort_by == 'status_asc':
            clients = clients.order_by('status')
        elif sort_by == 'status_desc':
            clients = clients.order_by('-status')
        elif sort_by == 'last_appt_asc':
            # Use the new name here
            clients = clients.order_by(F('annotated_last_appointment_date').asc(nulls_last=True))
        elif sort_by == 'last_appt_desc':
            # And here
            clients = clients.order_by(F('annotated_last_appointment_date').desc(nulls_first=True))
        else: # Default 'name_asc'
            clients = clients.order_by('first_name', 'last_name')

        paginator = Paginator(clients, 10)
        page_number = request.GET.get('page')
        clients_page = paginator.get_page(page_number)

        # This loop is still needed to get the full appointment object for display
        for client in clients_page:
            client.last_appointment = Appointment.objects.filter(client=client, practitioner=practitioner).order_by('-date').first()
            client.initials = f"{client.first_name[0] if client.first_name else ''}{client.last_name[0] if client.last_name else ''}".upper()

        context = {
            'clients': clients_page,
            'total_clients': paginator.count,
            'search_query': search_query,
            'status_filter': status_filter,
            'sort_by': sort_by,
            'is_paginated': clients_page.has_other_pages(),
            'page_obj': clients_page,
        }
        return render(request, self.template_name, context)

#<-- LIVE CLIENT SEARCH (API) -->
@login_required
def client_search_api(request):
    """
    API endpoint for live searching of clients from the database.
    Returns dynamically masked names and emails for enhanced privacy.
    """
    query = request.GET.get('q', '').strip().lower()
    
    # We only start searching after 2 characters for performance
    if len(query) < 2:
        return JsonResponse({'clients': []})

    practitioner = request.user.practitioner_profile
    
    # Build the search filter to query against multiple fields
    search_filter = (
        Q(first_name__istartswith=query) |
        Q(last_name__istartswith=query) |
        Q(email__istartswith=query) |
        Q(xdulr_id__istartswith=query)
    )
    
    # Find clients using the filter, excluding any already connected to the practitioner
    clients_found = Client.objects.filter(search_filter).exclude(practitioners=practitioner)[:5]

    results = []
    for client in clients_found:
        first_name = client.first_name
        last_name = client.last_name

        # --- 1. Dynamic Name Masking ---
        # This logic checks if the search query matches the beginning of the client's name
        # and masks the rest of the name accordingly.
        
        if first_name and first_name.lower().startswith(query):
            # If "jo" is typed, "John" becomes "Jo**"
            masked_first = first_name[:len(query)] + ('*' * (len(first_name) - len(query)))
            # The last name is partially masked for privacy
            masked_last = (last_name[0] + '****') if last_name else ''
        elif last_name and last_name.lower().startswith(query):
            # If "do" is typed, "Doe" becomes "Do*"
            masked_first = (first_name[0] + '****') if first_name else ''
            masked_last = last_name[:len(query)] + ('*' * (len(last_name) - len(query)))
        else:
            # Default masking if the client was found via email or ID search
            masked_first = first_name
            masked_last = (last_name[0] + '****') if last_name else ''
        
        masked_name = f"{masked_first} {masked_last}".strip()

        # --- 2. Email Masking ---
        # The client's email is always masked to protect their privacy in search results.
        email = client.email
        masked_email = 'Email hidden' # Default text if no email exists
        if email and '@' in email:
            local_part, domain_part = email.split('@', 1)
            # "jane.doe@example.com" becomes "j*******@example.com"
            masked_local = local_part[0] + ('*' * (len(local_part) - 1))
            masked_email = f"{masked_local}@{domain_part}"

        # The data sent back to the page now contains the masked details
        results.append({
            'id': client.id,
            'masked_name': masked_name,
            'email': masked_email,
        })
        
    return JsonResponse({'clients': results})


@login_required
@require_POST
def send_connection_otp(request):
    """
    Generates and sends a 6-digit OTP to a client's phone or email for connection verification.
    """
    try:
        data = json.loads(request.body)
        client_id = data.get('client_id')
        client = get_object_or_404(Client, id=client_id)

        # Generate OTP
        otp_code = str(secrets.randbelow(1_000_000)).zfill(6)
        otp_expiry = timezone.now() + timedelta(minutes=5)

        PhoneOTP.objects.update_or_create(
            client=client,
            defaults={'otp': otp_code, 'expires_at': otp_expiry}
        )

        # --- CORRECTED LOGIC: Prioritize phone, fallback to email ---
        # Use client.phone_number directly, as that's where it's stored.
        if client.phone_number:
            try:
                message = f"A request was made to connect to your profile. Use this verification code: {otp_code}. This code expires in 5 minutes."
                send_sms_via_telnyx(client.phone_number, message)
                return JsonResponse({'status': 'success', 'message': f"An OTP has been sent to the client's phone number ending in ...{client.phone_number[-4:]}."})
            except Exception as sms_error:
                logger.error(f"Failed to send SMS for client {client.id}. Error: {sms_error}", exc_info=True)
                # If SMS fails, we can fall through to try email
        
        # Fallback to email if phone doesn't exist or if sending SMS failed
        if client.email:
            try:
                custom_emails.send_connection_otp_email(client, otp_code)
                return JsonResponse({'status': 'success', 'message': f"An OTP has been sent to the client's email address."})
            except Exception as email_error:
                logger.error(f"Failed to send OTP email for client {client.id}. Error: {email_error}", exc_info=True)
                return JsonResponse({'status': 'error', 'message': 'Could not send the verification code via email.'}, status=500)

        # If we reach here, no contact method was available or worked
        return JsonResponse({
            'status': 'error', 
            'message': "This client does not have a registered phone number or email to send an OTP to."
        }, status=400)

    except Exception as e:
        logger.error(f"A critical error occurred in send_connection_otp. Traceback: {traceback.format_exc()}")
        return JsonResponse({
            'status': 'error', 
            'message': 'A critical server error occurred. The issue has been logged for review.'
        }, status=500)


#<-- CONNECT CLIENT VIEW -->

@login_required
@require_POST
def connect_client_api(request):
    """
    API endpoint to connect an existing client after PIN or OTP verification.
    """
    try:
        data = json.loads(request.body)
        client_id = data.get('client_id')
        code = data.get('code')
        method = data.get('method', 'pin')

        if not all([client_id, code, method]):
            return JsonResponse({'status': 'error', 'message': 'Client ID, verification code, and method are required.'}, status=400)

        client = get_object_or_404(Client, id=client_id)
        practitioner = request.user.practitioner_profile
        
        is_verified = False
        
        if method == 'pin':
            if client.check_pin(code):
                is_verified = True
        
        elif method == 'otp':
            try:
                phone_otp = PhoneOTP.objects.get(client=client, otp=code)
                if phone_otp.expires_at > timezone.now():
                    is_verified = True
                    phone_otp.delete()
                else:
                    phone_otp.delete()
                    return JsonResponse({'status': 'error', 'message': 'The OTP has expired. Please request a new one.'}, status=403)
            except PhoneOTP.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'The verification code is incorrect.'}, status=403)

        if is_verified:
            client.practitioners.add(practitioner)
            
            try:
                custom_emails.send_consent_request_notification(client, practitioner)
            except Exception as e:
                logger.error(f"Failed to send consent request for existing client {client.id}: {e}")

            return JsonResponse({'status': 'success', 'message': f'Successfully connected to {client.get_full_name()}. A consent request has been sent.'})
        else:
            # This will be the fallback for an incorrect PIN
            return JsonResponse({'status': 'error', 'message': 'The PIN entered is incorrect.'}, status=403)

    except (json.JSONDecodeError, Client.DoesNotExist):
        return JsonResponse({'status': 'error', 'message': 'Invalid request or client not found.'}, status=400)
    except Exception as e:
        logger.error(f"Error in connect_client_api: {e}", exc_info=True)
        return JsonResponse({'status': 'error', 'message': 'An unexpected server error occurred.'}, status=500)



#<-- CREATE CLIENT VIEW -->
class CreateClient(LoginRequiredMixin, View):
    """
    Handles the creation of a new client. Allows for shared emails/phones
    by treating each creation as a new, distinct individual.
    """
    template_name = 'frontend/template/create_client.html'

    def get(self, request):
        return render(request, self.template_name, {'form_data': {}})

    def post(self, request):
        practitioner = get_object_or_404(Practitioner, user=request.user)
        wallet, _ = PractitionerWallet.objects.get_or_create(practitioner=practitioner)

        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        phone_number = request.POST.get('phone', '').strip()

        if not all([first_name, last_name, email]):
            messages.error(request, "First Name, Last Name, and Email are required.")
            return render(request, self.template_name, {'form_data': request.POST})

        try:
            # Create the client record first. No User object is created to allow shared emails.
            client = Client.objects.create(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone_number=phone_number,
                status='active',
                notes=request.POST.get('notes', '')
            )
            client.practitioners.add(practitioner)

            plaintext_pin = getattr(client, '_temp_plaintext_pin', None)
            if not plaintext_pin:
                logger.error(f"CRITICAL: Could not retrieve plaintext PIN for new client ID {client.id}.")
                messages.error(request, f"Client '{client.get_full_name()}' was created, but credentials could not be generated. Please reset their PIN manually.")
                return redirect('practitioners:clients')

            # --- ROBUST NOTIFICATION LOGIC ---
            # Use separate try/except blocks for each step to provide specific feedback.
            
            success_notifications = []
            warning_notifications = []

            # 1. Attempt to send credentials email
            try:
                custom_emails.send_client_credentials(client, practitioner, plaintext_pin)
                success_notifications.append("Credentials email sent.")
            except Exception as e:
                logger.error(f"Error sending client credentials email for client {client.id}: {e}", exc_info=True)
                warning_notifications.append("Could not send the credentials email.")

            # 2. Attempt to send credentials SMS
            if client.phone_number:
                SMS_COST = Decimal('0.02')  # A reasonable assumed cost for a single SMS
                if wallet.balance < SMS_COST:
                    warning_notifications.append(f"Could not send SMS due to insufficient wallet balance.")
                else:
                    try:
                        send_sms_via_telnyx(
                            client.phone_number,
                            f"Your client portal login for {practitioner.business_name} - ID: {client.xdulr_id}, PIN: {plaintext_pin}"
                        )
                        success_notifications.append("Credentials SMS sent.")
                    except Exception as e:
                        logger.error(f"Error sending credentials SMS for client {client.id}: {e}", exc_info=True)
                        warning_notifications.append("Could not send the credentials via SMS.")

            # 3. Attempt to send consent request email
            try:
                custom_emails.send_consent_request_notification(client, practitioner)
                success_notifications.append("Consent request sent.")
            except Exception as e:
                logger.error(f"Error sending consent request email for client {client.id}: {e}", exc_info=True)
                warning_notifications.append("Could not send the data consent request email.")

            # 4. Provide consolidated, clear feedback to the user
            messages.success(request, f"Client '{client.get_full_name()}' was created successfully.")
            for warning in warning_notifications:
                messages.warning(request, warning)

        except Exception as e:
            logger.error(f"FATAL: Could not create client record in database. Error: {e}", exc_info=True)
            messages.error(request, "A database error occurred while creating the client.")
            return render(request, self.template_name, {'form_data': request.POST})

        return redirect('practitioners:clients')

#<-- SEND CONSENT REQUEST VIEW -->
class SendConsentRequestView(LoginRequiredMixin, View):
    """
    Handles the action of a practitioner sending a consent request to a client.
    """
    template_name = 'frontend/template/send_consent_request.html'

    def get(self, request, client_id):
        practitioner = get_object_or_404(Practitioner, user=request.user)
        client = get_object_or_404(Client, id=client_id, practitioners=practitioner)
        
        if not hasattr(practitioner, 'data_request_settings'):
            messages.error(request, "You must configure your data request settings before sending a request.")
            return redirect(reverse('practitioners:settings') + '?tab=profile')
        
        context = {
            'client': client,
            'practitioner': practitioner
        }
        return render(request, self.template_name, context)

    def post(self, request, client_id):
        practitioner = get_object_or_404(Practitioner, user=request.user)
        client = get_object_or_404(Client, id=client_id, practitioners=practitioner)

        # Check if an ACTIVE consent already exists for this practitioner and client.
        if ClientConsent.objects.filter(practitioner=practitioner, client=client, is_active=True).exists():
            messages.info(request, f"You already have active data consent from {client.get_full_name()}.")
        else:
            # The "sending" action is simply notifying the client. The client portal's
            # logic will automatically show this as a pending request because no
            # active consent record exists yet.
            try:
                custom_emails.send_consent_request_notification(client, practitioner)
                messages.success(request, f"A consent request notification has been sent to {client.get_full_name()}.")
            except Exception as e:
                logger.error(f"Failed to send consent request email for client {client.id}: {e}")
                messages.error(request, "Could not send the notification email. Please check your email settings.")

        return redirect('practitioners:client_detail', client_id=client.id)


#<-- CLIENT DETAIL VIEW -->
class ClientDetail(LoginRequiredMixin, View):
    """
    Displays a detailed view of a single client and handles inline editing of their details.
    """
    template_name = 'frontend/template/client_detail.html'

    def get(self, request, client_id):
        practitioner = get_object_or_404(Practitioner, user=request.user)
        client = get_object_or_404(Client, id=client_id, practitioners=practitioner)

        appointments = Appointment.objects.filter(client=client, practitioner=practitioner)
        payments = Payment.objects.filter(appointment__in=appointments).order_by('-payment_date')
        
        # Fetch consent and build the consented data dictionary with REAL data
        consent = ClientConsent.objects.filter(client=client, practitioner=practitioner, is_active=True).first()
        consented_data = {}
        if consent:
            # Get the practitioner's data request settings
            data_request_settings = PractitionerDataRequest.objects.filter(practitioner=practitioner).first()
            if data_request_settings:
                # This map defines the display name and the corresponding client model attribute
                # for every possible piece of consented data.
                field_map = {
                    # Personal & Identity
                    'request_middle_name': ('Middle Name', client.middle_name),
                    'request_preferred_name': ('Preferred Name', client.preferred_name),
                    'request_sin': ('Social Insurance Number', client.social_insurance_number),
                    'request_date_of_birth': ('Date of Birth', client.date_of_birth),
                    'request_sex_assigned_at_birth': ('Sex Assigned at Birth', client.sex_assigned_at_birth),
                    'request_gender_identity': ('Gender Identity', client.gender_identity),
                    'request_marital_status': ('Marital Status', client.marital_status),
                    # Contact Details
                    'request_address': ('Address', f"{client.address or ''}, {client.city or ''}, {client.province or ''}, {client.postal_code or ''}".strip(', ')),
                    'request_alternate_phone': ('Alternate Phone', client.alternate_phone_number),
                    # Citizenship & Language
                    'request_citizenship_status': ('Citizenship Status', client.citizenship_status),
                    'request_primary_language': ('Primary Language', client.primary_language),
                    # Health Profile
                    'request_health_card': ('Health Card Number', client.health_card_number),
                    'request_allergies': ('Allergies', client.allergies),
                    'request_medications': ('Current Medications', client.current_medications),
                    'request_conditions': ('Existing Conditions', client.existing_conditions),
                    # Insurance Details
                    'request_insurance': ('Insurance Provider', client.insurance_provider),
                    'request_policy_number': ('Policy Number', client.policy_number),
                }
                
                for setting_field, (display_name, client_value) in field_map.items():
                    # If the practitioner has requested this data (the setting is True)
                    # and the client has provided a value, add it to the dictionary.
                    if getattr(data_request_settings, setting_field, False) and client_value:
                        consented_data[display_name] = client_value

        context = {
            'client': client,
            'past_appointments': appointments.filter(date__lt=timezone.now().date()).order_by('-date')[:5],
            'upcoming_appointments': appointments.filter(date__gte=timezone.now().date()).order_by('date')[:5],
            'total_sessions': appointments.count(),
            'total_revenue': payments.filter(status='completed').aggregate(total=Sum('amount'))['total'] or 0,
            'consent': consent,
            'consented_data': consented_data,
        }
        return render(request, self.template_name, context)

    def post(self, request, client_id):
        practitioner = get_object_or_404(Practitioner, user=request.user)
        client = get_object_or_404(Client, id=client_id, practitioners=practitioner)
        
        action = request.POST.get('action')

        if action == 'update_details':
            # Update User model fields (if linked)
            if client.user:
                user = client.user
                user.first_name = request.POST.get('first_name', user.first_name)
                user.last_name = request.POST.get('last_name', user.last_name)
                user.email = request.POST.get('email', user.email)
                user.save()

            # Update Client model fields directly
            client.first_name = request.POST.get('first_name', client.first_name)
            client.last_name = request.POST.get('last_name', client.last_name)
            client.email = request.POST.get('email', client.email)
            client.phone_number = request.POST.get('phone', client.phone_number)
            client.save()

            messages.success(request, f"Successfully updated details for {client.get_full_name()}.")
        
        return redirect('practitioners:client_detail', client_id=client.id)

@login_required
@require_POST # Ensures this can only be called via a POST request for safety
def remove_client_connection(request, client_id):
    """
    Removes the connection between a practitioner and a client.
    This revokes access but does not delete the client's profile.
    """
    practitioner = get_object_or_404(Practitioner, user=request.user)
    client = get_object_or_404(Client, id=client_id)

    # 1. Remove the client from the practitioner's list
    practitioner.clients.remove(client)

    # 2. Revoke any data access consents that exist between them
    ClientConsent.objects.filter(practitioner=practitioner, client=client).delete()

    messages.info(request, f"You have successfully removed your connection to {client.get_full_name()}. They will no longer appear in your client list.")
    return redirect('practitioners:clients')


#<-- USER PUBLIC BOOKING PAGE VIEW -->
class UserPublicPageView(View):
    """
    Renders the public booking page for a practitioner, accessed via a subdomain or direct URL.
    """
    template_name = 'frontend/template/user_public_page.html'

    def get(self, request, username=None, *args, **kwargs): #<-- Add username parameter
        # Prioritize username from URL, otherwise use one from subdomain middleware
        username_to_use = username or getattr(request, 'subdomain_username', None)

        if not username_to_use:
             return HttpResponse("Page not found", status=404)
        
        try:
            user = User.objects.get(username=username_to_use)
            practitioner = Practitioner.objects.get(user=user)
            context = {'practitioner': practitioner}
            return render(request, self.template_name, context)
        except (User.DoesNotExist, Practitioner.DoesNotExist):
            return HttpResponse("Page not found", status=404)

# =============================================================================
# STAFF & SERVICES MANAGEMENT VIEWS
# =============================================================================


class StaffAndServicesView(LoginRequiredMixin, View):
    """
    Handles the GET request to display the combined Staff and Services page.
    """
    template_name = 'frontend/template/staff_and_services.html'

    def get(self, request):
        practitioner = get_object_or_404(Practitioner, user=request.user)
        active_tab = request.GET.get('tab', 'staff')

        staff_members = Staff.objects.filter(practitioner=practitioner).order_by('name')
        services = Service.objects.filter(practitioner=practitioner).prefetch_related('staff_members').order_by('name')

        # Prepare Staff data for JavaScript, including the profile picture URL
        staff_data_for_json = []
        for staff in staff_members:
            staff_dict = model_to_dict(staff, exclude=['services', 'profile_picture', 'user'])
            staff_dict['profile_pic_url'] = staff.profile_pic_url
            
            availability = StaffAvailability.objects.filter(staff=staff)
            availability_dict = {
                str(avail.day_of_week): {
                    'is_available': avail.is_available,
                    'start_time': avail.start_time.strftime('%H:%M') if avail.start_time else '',
                    'end_time': avail.end_time.strftime('%H:%M') if avail.end_time else ''
                } for avail in availability
            }
            staff_dict['availability'] = availability_dict
            
            staff_data_for_json.append({
                'pk': staff.pk,
                'model': 'practitioners.staff',
                'fields': staff_dict
            })

        # Prepare Service data for JavaScript, including the photo URL and assigned staff
        services_data_for_json = []
        for service in services:
            service_dict = model_to_dict(service, exclude=['photo'])
            service_dict['photo_url'] = service.photo_url
            service_dict['assigned_staff_ids'] = list(service.staff_members.values_list('id', flat=True))
            
            services_data_for_json.append({
                'pk': service.pk,
                'model': 'practitioners.service',
                'fields': service_dict
            })

        context = {
            'practitioner': practitioner,
            'active_tab': active_tab,
            'staff_members': staff_members,
            'services': services,
            'weekdays': {0: 'Sunday', 1: 'Monday', 2: 'Tuesday', 3: 'Wednesday', 4: 'Thursday', 5: 'Friday', 6: 'Saturday'},
            'staff_members_json': json.dumps(staff_data_for_json, cls=DjangoJSONEncoder),
            'services_json': json.dumps(services_data_for_json, cls=DjangoJSONEncoder),
        }

        return render(request, self.template_name, context)


@login_required
@require_POST
def add_or_edit_staff(request, staff_id=None):
    """
    API endpoint to add or edit a Staff member, including profile picture upload.
    """
    practitioner = get_object_or_404(Practitioner, user=request.user)
    
    try:
        with transaction.atomic():
            if staff_id:
                staff_instance = get_object_or_404(Staff, id=staff_id, practitioner=practitioner)
                staff_instance.name = request.POST.get('name')
                staff_instance.email = request.POST.get('email')
                staff_instance.phone = request.POST.get('phone')
                staff_instance.specialization = request.POST.get('specialization')
                staff_instance.is_active = request.POST.get('is_active') == 'true'
            else:
                staff_instance = Staff.objects.create(
                    practitioner=practitioner,
                    name=request.POST.get('name'),
                    email=request.POST.get('email'),
                    phone=request.POST.get('phone'),
                    specialization=request.POST.get('specialization'),
                    is_active=request.POST.get('is_active') == 'true'
                )

            # Handle profile picture upload
            if 'profile_picture' in request.FILES:
                staff_instance.profile_picture = request.FILES['profile_picture']
            
            staff_instance.save()

            # Process availability
            StaffAvailability.objects.filter(staff=staff_instance).delete()
            for day_code in range(7):
                if f'available_{day_code}' in request.POST:
                    start_time_str = request.POST.get(f'start_time_{day_code}')
                    end_time_str = request.POST.get(f'end_time_{day_code}')
                    if start_time_str and end_time_str:
                        StaffAvailability.objects.create(
                            staff=staff_instance,
                            day_of_week=day_code,
                            start_time=start_time_str,
                            end_time=end_time_str,
                            is_available=True
                        )
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_POST
def delete_staff_api(request, staff_id):
    """ API endpoint to delete a staff member. """
    practitioner = get_object_or_404(Practitioner, user=request.user)
    staff = get_object_or_404(Staff, id=staff_id, practitioner=practitioner)
    staff.delete()
    return JsonResponse({'success': True})


@login_required
@require_POST
def add_or_edit_service(request, service_id=None):
    """ API endpoint to add or edit a service, including photo upload and staff assignment. """
    practitioner = get_object_or_404(Practitioner, user=request.user)
    
    try:
        with transaction.atomic():
            data = request.POST
            form_data = {
                'name': data.get('name'),
                'duration': int(data.get('duration')),
                'price': Decimal(data.get('price')),
                'description': data.get('description', ''),
                'practitioner': practitioner
            }
            assigned_staff_ids = data.getlist('assigned_staff')

            if service_id:
                service_instance = get_object_or_404(Service, id=service_id, practitioner=practitioner)
                for key, value in form_data.items():
                    setattr(service_instance, key, value)
            else:
                service_instance = Service.objects.create(**form_data)

            if 'photo' in request.FILES:
                service_instance.photo = request.FILES['photo']
            
            service_instance.save()
            service_instance.staff_members.set(assigned_staff_ids)
            
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_POST
def delete_service_api(request, service_id):
    """ API endpoint to delete a service. """
    practitioner = get_object_or_404(Practitioner, user=request.user)
    service = get_object_or_404(Service, id=service_id, practitioner=practitioner)
    service.delete()
    return JsonResponse({'success': True})                           

#<-- APPOINTMENTS LIST & CALENDAR VIEW -->

@login_required
def appointment_client_search_api(request):
    """
    API endpoint for the calendar modal.
    - For connected clients, it returns full details.
    - For unconnected clients, it returns a masked name to protect privacy
      and indicates a PIN is required to connect.
    """
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'clients': []})

    practitioner = request.user.practitioner_profile
    search_filter = (
        Q(first_name__icontains=query) | Q(last_name__icontains=query) |
        Q(email__icontains=query) | Q(phone_number__icontains=query) |
        Q(xdulr_id__icontains=query)
    )

    connected_subquery = practitioner.clients.filter(pk=OuterRef('pk'))
    clients_found = Client.objects.filter(search_filter).annotate(
        is_connected=Exists(connected_subquery)
    ).order_by('-is_connected')[:10]

    results = []
    for client in clients_found:
        if client.is_connected:
            # If connected, send full details
            results.append({
                'id': client.id,
                'name': client.get_full_name(),
                'email': client.email,
                'is_connected': True,
            })
        else:
            # ✨ NEW: If not connected, send MASKED details
            results.append({
                'id': client.id,
                'name': f"{client.first_name} {client.last_name[0]}****", # Masked name
                'email': None, # Do not expose email
                'is_connected': False,
            })
            
    return JsonResponse({'clients': results})


class Appointments(LoginRequiredMixin, View):
    """
    Displays appointments in a filterable list and a full calendar view.
    """
    template_name = 'frontend/template/appointments.html'

    def get(self, request):
        practitioner = get_object_or_404(Practitioner, user=request.user)

        # Get filter parameters from request
        search_query = request.GET.get('search', '')
        start_date_str = request.GET.get('date_from', '')
        end_date_str = request.GET.get('date_to', '')
        status_filter = request.GET.get('status', 'all')
        view_mode = request.GET.get('view', 'upcoming') # 'upcoming', 'past', or 'calendar'

        # Base queryset
        appointments = Appointment.objects.filter(practitioner=practitioner).select_related(
            'client__user', 'service'
        )

        # Apply filters
        if search_query:
            appointments = appointments.filter(
                Q(client__user__first_name__icontains=search_query) |
                Q(client__user__last_name__icontains=search_query) |
                Q(service__name__icontains=search_query)
            )
        if status_filter != 'all':
            appointments = appointments.filter(status=status_filter)
        if start_date_str:
            appointments = appointments.filter(date__gte=start_date_str)
        if end_date_str:
            appointments = appointments.filter(date__lte=end_date_str)

        # Prepare context
        context = {
            'practitioner': practitioner,
            'services': Service.objects.filter(practitioner=practitioner, is_active=True),
            'clients': Client.objects.filter(practitioners=practitioner).select_related('user'),
            'search_query': search_query,
            'status_filter': status_filter,
            'start_date': start_date_str,
            'end_date': end_date_str,
            'active_tab': view_mode,
        }

        if view_mode == 'calendar':
            # Format appointments for FullCalendar.js
            calendar_events = []
            for appt in appointments:
                calendar_events.append({
                    'id': appt.id,
                    'title': f"{appt.client.user.get_full_name()} - {appt.service.name}",
                    'start': f"{appt.date.isoformat()}T{appt.start_time.isoformat()}",
                    'end': f"{appt.date.isoformat()}T{appt.end_time.isoformat()}",
                    'url': reverse('practitioners:appointment_detail', args=[appt.id]),
                    'color': appt.service.color or '#3788d8',
                })
            context['calendar_events'] = json.dumps(calendar_events)
        else:
            # Paginate for list views
            today = timezone.now().date()
            if view_mode == 'past':
                display_appointments = appointments.filter(date__lt=today).order_by('-date', '-start_time')
            else: # Default to upcoming
                display_appointments = appointments.filter(date__gte=today).order_by('date', 'start_time')

            paginator = Paginator(display_appointments, 10)
            page_number = request.GET.get('page')
            appointments_page = paginator.get_page(page_number)
            context['appointments'] = appointments_page

        return render(request, self.template_name, context)

#<-- DEDICATED CALENDAR VIEW -->

class Calendar(LoginRequiredMixin, View):
    """
    Renders the main calendar page. The event data will be fetched
    dynamically by FullCalendar.js.
    """
    template_name = 'frontend/template/calendar.html'

    def get(self, request):
        practitioner = get_object_or_404(Practitioner, user=request.user)
        
        context = {
            'practitioner': practitioner,
            'staff_list': Staff.objects.filter(practitioner=practitioner, is_active=True),
            'active_staff_id': request.GET.get('staff_id'),
        }
        return render(request, self.template_name, context)

@login_required
def get_calendar_events_api(request):
    """
    API endpoint that provides appointment data to FullCalendar.
    Accepts start, end, and optional staff_id query parameters.
    """
    try:
        start_str = request.GET.get('start')
        end_str = request.GET.get('end')
        staff_id = request.GET.get('staff_id')
        practitioner = request.user.practitioner_profile

        # Parse date strings from FullCalendar
        start_date = parse_datetime(start_str).date()
        end_date = parse_datetime(end_str).date()

        # Base query for appointments within the visible date range
        appointments_query = Appointment.objects.filter(
            practitioner=practitioner,
            date__range=[start_date, end_date]
        ).select_related('client__user', 'service')

        # Apply staff filter if provided
        if staff_id:
            appointments_query = appointments_query.filter(staff_id=staff_id)
        
        # Define color mapping
        color_map = {
            'primary': '#3788d8', 'success': '#28a745',
            'warning': '#ffc107', 'danger': '#dc3545',
        }

        # Format events for the calendar
        events = []
        for appt in appointments_query:
            if not hasattr(appt.client, 'user'): continue
            
            start_datetime = timezone.make_aware(datetime.combine(appt.date, appt.start_time))
            end_datetime = timezone.make_aware(datetime.combine(appt.date, appt.end_time))
            event_color = color_map.get(appt.service.color, '#6c757d')

            events.append({
                'id': appt.id,
                'title': f"{appt.client.user.get_full_name()} - {appt.service.name}",
                'start': start_datetime.isoformat(),
                'end': end_datetime.isoformat(),
                'color': event_color,
                'url': reverse('practitioners:appointment_detail', args=[appt.id]),
            })

        return JsonResponse(events, safe=False)

    except Exception as e:
        logger.error(f"Error in get_calendar_events_api: {e}")
        return JsonResponse({'error': 'An error occurred while fetching events.'}, status=500)


@login_required
@require_POST
def update_appointment_time_api(request, appointment_id):
    """
    API endpoint to update an appointment's time after a drag-and-drop action.
    """
    try:
        # Ensure the appointment belongs to the logged-in practitioner
        appointment = get_object_or_404(
            Appointment,
            id=appointment_id,
            practitioner=request.user.practitioner_profile
        )

        data = json.loads(request.body)
        new_start_str = data.get('new_start')

        if not new_start_str:
            return JsonResponse({'status': 'error', 'message': 'New start time not provided.'}, status=400)

        new_start_dt = parse_datetime(new_start_str)
        if not new_start_dt:
            return JsonResponse({'status': 'error', 'message': 'Invalid date format.'}, status=400)

        # Calculate the new end time based on the service's duration
        duration_delta = timedelta(minutes=appointment.service.duration)
        new_end_dt = new_start_dt + duration_delta

        # Update the appointment fields and save to the database
        appointment.date = new_start_dt.date()
        appointment.start_time = new_start_dt.time()
        appointment.end_time = new_end_dt.time()
        appointment.save()

        return JsonResponse({'status': 'success', 'message': 'Appointment updated.'})
    except Exception as e:
        # It's good practice to log errors
        logger.error(f"Error updating appointment {appointment_id} via drag-drop: {e}")
        return JsonResponse({'status': 'error', 'message': 'An unexpected server error occurred.'}, status=500)

#<-- CREATE APPOINTMENT VIEW -->
class CreateAppointment(LoginRequiredMixin, View):
    """
    Handles the creation of a new appointment from the practitioner's dashboard.
    This view is compatible with both standard form posts and AJAX requests.
    """
    template_name = 'frontend/template/create_appointment.html'

    @method_decorator(wallet_balance_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        practitioner = get_object_or_404(Practitioner, user=request.user)
        context = {
            'clients': Client.objects.filter(practitioners=practitioner).select_related('user'),
            'services': Service.objects.filter(practitioner=practitioner, is_active=True),
            'staff': Staff.objects.filter(practitioner=practitioner, is_active=True),
        }
        if 'client_id' in request.GET:
            context['selected_client'] = get_object_or_404(Client, id=request.GET['client_id'])
        return render(request, self.template_name, context)

    def post(self, request):
        practitioner = get_object_or_404(Practitioner, user=request.user)
        is_ajax = 'application/json' in request.headers.get('Accept', '')

        try:
            # Check for either 'client' (from calendar) or 'client_id' (from dedicated page)
            client_id = request.POST.get('client') or request.POST.get('client_id')
            if not client_id:
                raise ValueError("Client ID was not provided in the request.")

            client = get_object_or_404(Client, id=client_id)
            service = get_object_or_404(Service, id=request.POST.get('service'))
            
            # --- FIX STARTS HERE ---
            # Handle optional staff selection
            staff_id = request.POST.get('staff')
            staff = None # Default to None
            if staff_id:
                staff = get_object_or_404(Staff, id=staff_id)
            # --- FIX ENDS HERE ---

            appointment_date_str = request.POST.get('appointment_date')
            appointment_time_str = request.POST.get('appointment_time')

            if not all([appointment_date_str, appointment_time_str]):
                raise ValueError("A valid date and time are required.")

            appointment_date = datetime.strptime(appointment_date_str, '%Y-%m-%d').date()
            appointment_time = datetime.strptime(appointment_time_str, '%H:%M').time()

            start_datetime = datetime.combine(appointment_date, appointment_time)
            end_time = (start_datetime + timedelta(minutes=service.duration)).time()

            appointment = Appointment.objects.create(
                practitioner=practitioner,
                client=client,
                service=service,
                staff=staff, # This will be the Staff object or None
                date=appointment_date,
                start_time=appointment_time,
                end_time=end_time,
                status='pending',
                notes=request.POST.get('appointment_notes', ''),
                price=service.price
            )
            
            # --- FIX: Only send notification if staff is assigned and has an email ---
            if staff and staff.email:
                custom_emails.send_staff_new_appointment_notification(request, appointment)
            
            messages.success(request, f"Appointment successfully scheduled for {client.get_full_name()}.")
            
            if is_ajax:
                return JsonResponse({'status': 'success', 'redirect_url': reverse('practitioners:calendar')})
            else:
                return redirect('practitioners:calendar')

        except (Http404, ValueError, KeyError) as e:
            error_message = f"Invalid data provided. Please check all fields. Details: {str(e)}"
            if is_ajax:
                return JsonResponse({'status': 'error', 'message': error_message}, status=400)
            else:
                messages.error(request, error_message)
                return redirect('practitioners:create_appointment')




#<-- APPOINTMENT DETAIL VIEW -->
class AppointmentDetail(LoginRequiredMixin, View):
    """
    Displays all details for a single appointment.
    """
    template_name = 'frontend/template/appointment_detail.html'

    @method_decorator(wallet_balance_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, appointment_id):
        practitioner = get_object_or_404(Practitioner, user=request.user)
        appointment = get_object_or_404(Appointment, id=appointment_id, practitioner=practitioner)

        context = {
            'appointment': appointment,
            'client': appointment.client,
            'payment': Payment.objects.filter(appointment=appointment).first()
        }
        return render(request, self.template_name, context)

#<-- EDIT APPOINTMENT VIEW -->
class EditAppointment(LoginRequiredMixin, View):
    """
    Handles the modification of an existing appointment's details.
    """
    template_name = 'frontend/template/edit_appointment.html'

    @method_decorator(wallet_balance_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, appointment_id):
        practitioner = get_object_or_404(Practitioner, user=request.user)
        appointment = get_object_or_404(Appointment, id=appointment_id, practitioner=practitioner)
        context = {
            'appointment': appointment,
            'services': Service.objects.filter(practitioner=practitioner),
            'staff_list': Staff.objects.filter(practitioner=practitioner),
        }
        return render(request, self.template_name, context)

    def post(self, request, appointment_id):
        practitioner = get_object_or_404(Practitioner, user=request.user)
        appointment = get_object_or_404(Appointment, id=appointment_id, practitioner=practitioner)

        # Store old details for notification
        old_date = appointment.date
        old_time = appointment.start_time

        # Update appointment fields from POST data
        appointment.service = get_object_or_404(Service, id=request.POST.get('service'))
        appointment.staff = get_object_or_404(Staff, id=request.POST.get('staff'))
        appointment.date = datetime.strptime(request.POST.get('appointment_date'), '%Y-%m-%d').date()
        appointment.start_time = datetime.strptime(request.POST.get('appointment_time'), '%H:%M').time()
        appointment.end_time = (datetime.combine(appointment.date, appointment.start_time) + timedelta(minutes=appointment.service.duration)).time()
        appointment.status = request.POST.get('status', appointment.status)
        appointment.notes = request.POST.get('appointment_notes', appointment.notes)
        appointment.price = appointment.service.price
        appointment.save()

        # Send reschedule notification if date or time changed
        if appointment.date != old_date or appointment.start_time != old_time:
            custom_emails.send_appointment_rescheduled_email(request, appointment, old_date, old_time)

        messages.success(request, "Appointment has been updated successfully.")
        return redirect('practitioners:appointment_detail', appointment_id=appointment.id)

#<-- CONFIRM APPOINTMENT ACTION -->
@login_required
@require_POST
def confirm_appointment(request, appointment_id):
    """
    Action to change an appointment's status to 'confirmed'.
    """
    practitioner = get_object_or_404(Practitioner, user=request.user)
    appointment = get_object_or_404(Appointment, id=appointment_id, practitioner=practitioner)

    appointment.status = 'confirmed'
    appointment.save()

    custom_emails.send_appointment_confirmation_email(request, appointment)
    if appointment.client.user.phone:
        send_sms_via_telnyx(appointment.client.user.phone,f"Your appointment with {practitioner.user.get_full_name()} for {appointment.service.name} has been confirmed.")

    messages.success(request, "Appointment has been confirmed.")
    return redirect('practitioners:appointment_detail', appointment_id=appointment.id)

#<-- COMPLETE APPOINTMENT ACTION -->
@login_required
@require_POST
def complete_appointment(request, appointment_id):
    """
    Action to change an appointment's status to 'completed'.
    """
    practitioner = get_object_or_404(Practitioner, user=request.user)
    appointment = get_object_or_404(Appointment, id=appointment_id, practitioner=practitioner)

    appointment.status = 'completed'
    appointment.save()

    # Send post-appointment follow-ups
    custom_emails.send_feedback_request_email(request, appointment)

    messages.success(request, "Appointment has been marked as completed.")
    return redirect('practitioners:appointment_detail', appointment_id=appointment.id)

#<-- CANCEL APPOINTMENT ACTION -->
@login_required
@require_POST
def cancel_appointment(request, appointment_id):
    """
    Action to change an appointment's status to 'cancelled'.
    """
    practitioner = get_object_or_404(Practitioner, user=request.user)
    appointment = get_object_or_404(Appointment, id=appointment_id, practitioner=practitioner)

    appointment.status = 'cancelled'
    appointment.save()

    # Send cancellation notifications
    custom_emails.send_appointment_cancellation_email(request, appointment)
    if appointment.staff and appointment.staff.email:
        custom_emails.send_staff_cancellation_notification(request, appointment)

    messages.success(request, "The appointment has been cancelled.")
    return redirect('practitioners:appointment_detail', appointment_id=appointment.id)

#<-- GET STAFF AVAILABILITY (API) -->
@login_required
@require_http_methods(["GET"])
def get_staff_availability(request):
    """
    API endpoint to check if a staff member is free at a specific date and time.
    Used for preventing double bookings in the appointment forms.
    """
    try:
        staff = get_object_or_404(Staff, id=request.GET.get('staff_id'))
        appointment_date = datetime.strptime(request.GET.get('date'), '%Y-%m-%d').date()
        start_time = datetime.strptime(request.GET.get('start_time'), '%H:%M').time()
        duration = int(request.GET.get('duration', 60))
        end_time = (datetime.combine(appointment_date, start_time) + timedelta(minutes=duration)).time()

        # Check against regular schedule
        is_in_schedule = StaffAvailability.objects.filter(
            staff=staff, day_of_week=appointment_date.weekday(), is_available=True,
            start_time__lte=start_time, end_time__gte=end_time
        ).exists()

        # Check for conflicting appointments
        has_conflict = Appointment.objects.filter(
            staff=staff, date=appointment_date, status__in=['pending', 'confirmed'],
            start_time__lt=end_time, end_time__gt=start_time
        ).exists()

        return JsonResponse({'available': is_in_schedule and not has_conflict})

    except (Staff.DoesNotExist, ValueError, KeyError):
        return JsonResponse({'error': 'Invalid parameters'}, status=400)

    #<-- PUBLIC APPOINTMENT BOOKING VIEW -->
class BookAppointmentView(View):
    """
    Handles the public, multi-step appointment booking process that can be embedded
    on a practitioner's website or used as a standalone page.
    """
    template_name = 'frontend/template/plugin.html'

    def get(self, request, practitioner_id):
        practitioner = get_object_or_404(Practitioner, id=practitioner_id)
        services = Service.objects.filter(practitioner=practitioner, is_active=True)
        staff_members = Staff.objects.filter(practitioner=practitioner, is_active=True)

        # Manages the state of the booking process across multiple pages
        context = {
            'practitioner': practitioner,
            'services': services,
            'staff_members': staff_members,
            'step': request.GET.get('step', '1'),
            'selected_service_id': request.session.get('selected_service_id'),
            'selected_staff_id': request.session.get('selected_staff_id'),
            'selected_date': request.session.get('selected_date'),
        }
        return render(request, self.template_name, context)

    def post(self, request, practitioner_id):
        action = request.POST.get('action')

        # Store selections in session to maintain state
        if action == 'select_service':
            request.session['selected_service_id'] = request.POST.get('service_id')
            return redirect(reverse('practitioners:book_appointment_step', args=[practitioner_id, 2]))
        elif action == 'select_staff':
            request.session['selected_staff_id'] = request.POST.get('staff_id')
            return redirect(reverse('practitioners:book_appointment_step', args=[practitioner_id, 3]))
        elif action == 'select_datetime':
            request.session['selected_date'] = request.POST.get('date')
            request.session['selected_time'] = request.POST.get('time')
            return redirect(reverse('practitioners:book_appointment_step', args=[practitioner_id, 4]))
        elif action == 'book_appointment':
            return self.create_appointment(request, practitioner_id)

        return redirect('practitioners:book_appointment', args=[practitioner_id])

    def create_appointment(self, request, practitioner_id):
        """
        Final step of the booking process. Creates the client (if new),
        deducts the fee from the practitioner's wallet, and creates the appointment.
        """
        practitioner = get_object_or_404(Practitioner, id=practitioner_id)

        # Retrieve all data from session
        service_id = request.session.get('selected_service_id')
        staff_id = request.session.get('selected_staff_id')
        date_str = request.session.get('selected_date')
        time_str = request.session.get('selected_time')

        try:
            # Create or find the client
            client = self._get_or_create_client(request.POST, practitioner)
            service = get_object_or_404(Service, id=service_id)
            staff = get_object_or_404(Staff, id=staff_id)

            #<-- START OF WALLET DEDUCTION LOGIC -->
            # Determine the fee based on the practitioner's plan and age of account.
            appointment_fee = Decimal('0.90') # Default pay-as-you-go fee
            if getattr(practitioner, 'subscription_plan', 'pay_as_go') == 'growth':
                appointment_fee = Decimal('0.70')

            # Apply 50% discount for the first year
            if (timezone.now() - practitioner.user.date_joined).days < 365:
                appointment_fee /= 2

            wallet, _ = PractitionerWallet.objects.get_or_create(practitioner=practitioner)
            if wallet.balance < appointment_fee:
                # In a real scenario, this would block the booking and notify the practitioner.
                # For now, we'll log an error but allow the booking.
                logger.error(f"Practitioner {practitioner.id} has insufficient funds for appointment booking.")
                messages.error(request, "Booking failed due to insufficient practitioner funds.")
                return redirect('practitioners:book_appointment', args=[practitioner.id])
            #<-- END OF WALLET DEDUCTION LOGIC -->

            # Use a transaction to ensure appointment and wallet deduction happen together
            with transaction.atomic():
                # Deduct the fee from the wallet
                wallet.balance -= appointment_fee
                wallet.save()

                # Log the transaction
                WalletTransaction.objects.create(
                    wallet=wallet, amount=-appointment_fee, transaction_type='charge',
                    description=f"Fee for appointment with {client.user.get_full_name()}"
                )

                # Create the appointment
                appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                appointment_time = datetime.strptime(time_str, '%H:%M').time()
                appointment = Appointment.objects.create(
                    practitioner=practitioner, client=client, service=service, staff=staff,
                    date=appointment_date, start_time=appointment_time,
                    end_time=(datetime.combine(appointment_date, appointment_time) + timedelta(minutes=service.duration)).time(),
                    status='confirmed', # Public bookings are auto-confirmed
                    price=service.price
                )

            # Clear session data after successful booking
            for key in ['selected_service_id', 'selected_staff_id', 'selected_date', 'selected_time']:
                if key in request.session:
                    del request.session[key]

            messages.success(request, "Your appointment has been successfully booked!")
            # Redirect to a confirmation page
            return redirect('practitioners:booking_confirmation_page', args=[appointment.id])

        except Exception as e:
            messages.error(request, f"An error occurred: {e}")
            return redirect('practitioners:book_appointment', args=[practitioner.id])

    def _get_or_create_client(self, post_data, practitioner):
        """Helper method to find an existing client or create a new one."""
        email = post_data.get('email', '').strip()
        user, user_created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': email,
                'first_name': post_data.get('first_name'),
                'last_name': post_data.get('last_name'),
                'password': make_password(User.objects.make_random_password())
            }
        )
        client, client_created = Client.objects.get_or_create(user=user)
        client.practitioners.add(practitioner) # Associate with this practitioner
        return client

#<-- GET AVAILABLE SLOTS (API) -->
@require_http_methods(["GET"])
def get_available_slots(request):
    """
    API endpoint to get available time slots for a staff member, service, and date.
    """
    try:
        staff = get_object_or_404(Staff, id=request.GET.get('staff_id'))
        service = get_object_or_404(Service, id=request.GET.get('service_id'))
        date_str = request.GET.get('date')

        # This logic should be robust, checking StaffAvailability and existing Appointments
        # For simplicity, we assume a helper function exists.
        view = BookAppointmentView() # Re-use the method
        available_times = view.get_available_times(staff, date_str, service.duration)

        return JsonResponse({'slots': available_times})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

#<-- PLUGIN SETTINGS (API) -->
@csrf_exempt
def plugin_settings_api(request, practitioner_id):
    """
    API endpoint to provide the website widget with its custom settings.
    """
    plugin = get_object_or_404(WebsitePlugin, practitioner_id=practitioner_id)
    return JsonResponse({
        'primary_color': plugin.primary_color,
        'button_text': plugin.button_text,
    })

#<-- BOOK APPOINTMENT FROM PLUGIN (API) -->
@csrf_exempt
@require_POST
def book_appointment_api(request, practitioner_id):
    """
    API endpoint for the external website widget to create a new appointment.
    This must be CSRF exempt.
    """
    try:
        data = json.loads(request.body)
        practitioner = get_object_or_404(Practitioner, id=practitioner_id)

        # This view would replicate the logic from BookAppointmentView.create_appointment,
        # including finding/creating the client, calculating the fee, checking the
        # practitioner's wallet, and creating the appointment within a transaction.

        #<-- This is where you would also place the wallet deduction logic -->

        return JsonResponse({'status': 'success', 'message': 'Appointment booked successfully.'})
    except Exception as e:
        logger.error(f"Book Appointment API Error: {e}")
        return JsonResponse({'status': 'error', 'message': 'Could not book appointment.'}, status=500)


# =============================================================================
# STRIPE CONNECT & ONBOARDING VIEWS
# =============================================================================

#<-- MY FINANCES VIEW -->
class MyFinancesView(LoginRequiredMixin, View):
    """
    The main hub for a practitioner's financial overview, including their Stripe
    balance, payouts, transactions, and client subscription management.
    """
    template_name = 'frontend/template/my_finances.html'

    def get(self, request):
        practitioner = get_object_or_404(Practitioner, user=request.user)
        active_tab = request.GET.get('tab', 'dashboard')

        if active_tab == 'salary':
            return redirect('practitioners:salary_management')

        context = {
            'tab': active_tab,
            'practitioner': practitioner,
            'stripe_onboarding_complete': practitioner.stripe_onboarding_complete,
            'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
        }

        if active_tab == 'dashboard' and practitioner.stripe_account_id:
            try:
                # Fetch live data from Stripe for the connected account
                balance = stripe.Balance.retrieve(stripe_account=practitioner.stripe_account_id)
                payouts = stripe.Payout.list(limit=5, stripe_account=practitioner.stripe_account_id)
                charges = stripe.Charge.list(limit=10, stripe_account=practitioner.stripe_account_id, expand=['data.balance_transaction'])
                context.update({
                    'balance': {'available': balance.available[0], 'pending': balance.pending[0]},
                    'payouts': payouts.data,
                    'recent_transactions': charges.data,
                })
            except stripe.error.StripeError as e:
                messages.error(request, f"Could not fetch financial data from Stripe: {e}")

        elif active_tab == 'client_plans':
            client_plans = ClientSubscriptionPlan.objects.filter(practitioner=practitioner)
            for plan in client_plans:
                plan.features_list = plan.features.splitlines() if plan.features else []
            context['client_plans'] = client_plans

        return render(request, self.template_name, context)

#<-- STRIPE AUTHORIZE (ONBOARDING START) -->
@login_required
def stripe_authorize(request):
    """
    Redirects the practitioner to Stripe's authorization page to connect their account.
    This is the first step in the Stripe Connect onboarding process.
    """
    if not settings.STRIPE_CONNECT_CLIENT_ID:
        messages.error(request, "Stripe Connect integration is not configured correctly.")
        return redirect('practitioners:my_finances')

    authorize_url = (
        f"https://connect.stripe.com/oauth/authorize?"
        f"response_type=code&client_id={settings.STRIPE_CONNECT_CLIENT_ID}"
        f"&scope=read_write&redirect_uri={request.build_absolute_uri(reverse('practitioners:stripe_callback'))}"
    )
    return redirect(authorize_url)

#<-- STRIPE CALLBACK (ONBOARDING FINISH) -->
@login_required
def stripe_callback(request):
    """
    Handles the redirect back from Stripe after the user authorizes the connection.
    """
    code = request.GET.get('code')
    if not code:
        messages.error(request, "Invalid authorization request. Please try connecting again.")
        return redirect('practitioners:my_finances')

    try:
        response = stripe.OAuth.token(grant_type='authorization_code', code=code)
        stripe_account_id = response.get('stripe_user_id')

        practitioner = get_object_or_404(Practitioner, user=request.user)
        practitioner.stripe_account_id = stripe_account_id

        # Immediately check the account status after connecting
        if stripe_account_id:
            account = stripe.Account.retrieve(stripe_account_id)
            if account.details_submitted:
                practitioner.stripe_onboarding_complete = True

        practitioner.save()

        messages.success(request, "Congratulations! Your Stripe account has been successfully connected.")
    except stripe.error.StripeError as e:
        messages.error(request, f"Could not finalize the connection with Stripe: {e}")

    return redirect('practitioners:my_finances')

#<-- STRIPE CHOOSE AC-->
class ChooseAccountTypeView(LoginRequiredMixin, TemplateView):
    template_name = 'frontend/template/choose_stripe_account.html'

@login_required
def stripe_create_express_account(request):
    """
    Creates a new Stripe Express account for the practitioner.
    """
    practitioner = get_object_or_404(Practitioner, user=request.user)
    try:
        # Create the Express account
        account = stripe.Account.create(
            type="express",
            email=request.user.email,
            business_type="individual",
            # Add more capabilities as needed
            capabilities={"card_payments": {"requested": True}, "transfers": {"requested": True}},
        )

        # Save the new account ID and type
        practitioner.stripe_account_id = account.id
        practitioner.stripe_account_type = 'express'
        practitioner.save()

        # Create an account link for onboarding
        account_link = stripe.AccountLink.create(
            account=account.id,
            refresh_url=request.build_absolute_uri(reverse('practitioners:stripe_create_express')),
            return_url=request.build_absolute_uri(reverse('practitioners:stripe_express_return')),
            type="account_onboarding",
        )
        return redirect(account_link.url)

    except stripe.error.StripeError as e:
        messages.error(request, f"Could not create Stripe account: {e}")
        return redirect('practitioners:my_finances')

@login_required
def stripe_express_return(request):
    """
    Handles the redirect back from Stripe Express onboarding.
    """
    messages.success(request, "You have successfully connected your Stripe Express account!")
    return redirect('practitioners:my_finances')

#<-- STRIPE DASHBOARD LINK -->
@login_required
@login_required
def stripe_dashboard_link(request):
    """
    Redirects the practitioner to the correct Stripe dashboard based on their account type.
    """
    practitioner = get_object_or_404(Practitioner, user=request.user)
    if not practitioner.stripe_account_id:
        messages.error(request, "Your Stripe account is not connected.")
        return redirect('practitioners:my_finances')

    if practitioner.stripe_account_type == 'express':
        try:
            link = stripe.Account.create_login_link(practitioner.stripe_account_id)
            return redirect(link.url)
        except stripe.error.StripeError as e:
            messages.error(request, f"Could not access the Stripe dashboard: {e}")
            return redirect('practitioners:my_finances')
    else:
        # For Standard accounts (or any other case), redirect them directly.
        return redirect("https://dashboard.stripe.com/")

#<-- SALARY MANAGEMENT VIEW -->
class SalaryManagementView(LoginRequiredMixin, View):
    """
    Handles displaying staff pay structures and their pay history.
    """
    template_name = 'frontend/template/salary_management.html'

    def get(self, request, *args, **kwargs):
        practitioner = get_object_or_404(Practitioner, user=request.user)
        all_staff = Staff.objects.filter(practitioner=practitioner).order_by('name')
        
        selected_staff_id = request.GET.get('staff_id')
        selected_staff = None
        pay_stubs = None
        pay_stubs_json = '[]'

        if selected_staff_id:
            selected_staff = get_object_or_404(Staff, id=selected_staff_id, practitioner=practitioner)
            # Fetch the pay history for the selected staff member
            pay_stubs = selected_staff.pay_stubs.all()
            # Serialize the pay stubs to JSON for our JavaScript to use
            pay_stubs_json = serializers.serialize('json', pay_stubs)

        context = {
            'all_staff': all_staff,
            'selected_staff': selected_staff,
            'pay_stubs': pay_stubs,
            'pay_stubs_json': pay_stubs_json, # Add JSON data to the context
            'tab': 'salary',
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """ Handles saving the Pay Structure form """
        practitioner = get_object_or_404(Practitioner, user=request.user)
        staff_id_to_update = request.POST.get('staff_id')
        staff_to_update = get_object_or_404(Staff, id=staff_id_to_update, practitioner=practitioner)
        
        staff_to_update.pay_type = request.POST.get('pay_type')
        staff_to_update.pay_rate = Decimal(request.POST.get('pay_rate')) if request.POST.get('pay_rate') else None
        
        # Save deduction settings
        staff_to_update.income_tax_rate = Decimal(request.POST.get('income_tax_rate', 0))
        staff_to_update.cpp_rate = Decimal(request.POST.get('cpp_rate', 0))
        staff_to_update.ei_rate = Decimal(request.POST.get('ei_rate', 0))
        staff_to_update.benefits_deduction = Decimal(request.POST.get('benefits_deduction', 0))
        staff_to_update.other_deductions = Decimal(request.POST.get('other_deductions', 0))
        
        staff_to_update.save()
        
        return redirect(f"{reverse('practitioners:salary_management')}?staff_id={staff_to_update.id}")


# --- API endpoint for Gross Pay calculation ---
@login_required
def calculate_gross_pay_api(request, staff_id):
    practitioner = get_object_or_404(Practitioner, user=request.user)
    staff = get_object_or_404(Staff, id=staff_id, practitioner=practitioner)

    start_date_str = request.GET.get('start')
    end_date_str = request.GET.get('end')

    if not start_date_str or not end_date_str:
        return JsonResponse({'error': 'Start and end dates are required.'}, status=400)

    start_date = date.fromisoformat(start_date_str)
    end_date = date.fromisoformat(end_date_str)
    
    total_hours = Decimal(0)
    gross_pay = Decimal(0)

    if staff.pay_type == 'HOURLY' and staff.pay_rate:
        availabilities = StaffAvailability.objects.filter(staff=staff, is_available=True)
        current_date = start_date
        while current_date <= end_date:
            day_of_week = current_date.weekday()
            # In Python, Monday is 0 and Sunday is 6. Django's choices might be different.
            # Assuming your DAY_CHOICES are Monday=0...Sunday=6
            for availability in availabilities.filter(day_of_week=day_of_week):
                duration = (datetime.combine(date.today(), availability.end_time) - datetime.combine(date.today(), availability.start_time)).total_seconds() / 3600
                total_hours += Decimal(duration)
            current_date += timedelta(days=1)
        
        gross_pay = total_hours * staff.pay_rate

    elif staff.pay_type == 'SALARY' and staff.pay_rate:
        days_in_period = (end_date - start_date).days + 1
        gross_pay = (staff.pay_rate / Decimal(365)) * Decimal(days_in_period)

    return JsonResponse({
        'hours_worked': round(total_hours, 2),
        'gross_pay': round(gross_pay, 2),
    })


# --- API endpoint for the 'Create Pay Stub' modal ---

@login_required
@require_POST
def create_pay_stub_api(request, staff_id):
    """
    API endpoint to create a new PayStub for a staff member.
    """
    practitioner = get_object_or_404(Practitioner, user=request.user)
    staff = get_object_or_404(Staff, id=staff_id, practitioner=practitioner)

    try:
        data = request.POST
        
        pay_period_start = data.get('pay_period_start')
        pay_period_end = data.get('pay_period_end')
        gross_pay_str = data.get('gross_pay')
        deductions_str = data.get('deductions', '0')
        hours_worked_str = data.get('hours_worked')
        notes = data.get('notes', '')

        if not all([pay_period_start, pay_period_end, gross_pay_str]):
            return JsonResponse({'success': False, 'error': 'Missing required fields.'}, status=400)
            
        gross_pay = Decimal(gross_pay_str)
        deductions = Decimal(deductions_str)
        hours_worked = Decimal(hours_worked_str) if hours_worked_str and hours_worked_str.strip() else None

        new_stub = PayStub.objects.create(
            staff=staff,
            pay_period_start=pay_period_start,
            pay_period_end=pay_period_end,
            gross_pay=gross_pay,
            deductions=deductions,
            net_pay=gross_pay - deductions,
            hours_worked=hours_worked,
            notes=notes
        )
        
        # --- START OF FIX ---
        # Instead of serializing the whole object, create a simple dictionary
        stub_data = {
            'pk': new_stub.pk,
            'fields': {
                'pay_period_start': new_stub.pay_period_start.isoformat(),
                'pay_period_end': new_stub.pay_period_end.isoformat(),
                'gross_pay': str(new_stub.gross_pay),
                'deductions': str(new_stub.deductions),
                'net_pay': str(new_stub.net_pay),
            }
        }
        return JsonResponse({'success': True, 'stub': stub_data})
        # --- END OF FIX ---

    except (InvalidOperation, TypeError, ValueError):
        return JsonResponse({'success': False, 'error': 'Invalid number format provided for pay or hours.'}, status=400)
    except Exception as e:
        logger.error(f"Error creating pay stub for staff {staff_id}: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': 'An unexpected server error occurred. The issue has been logged.'}, status=500)


@login_required
@require_POST
def update_pay_stub_api(request, stub_id):
    """ API endpoint to update an existing PayStub. """
    practitioner = get_object_or_404(Practitioner, user=request.user)
    stub = get_object_or_404(PayStub, id=stub_id, staff__practitioner=practitioner)
    
    try:
        data = request.POST
        
        pay_period_start = data.get('pay_period_start')
        pay_period_end = data.get('pay_period_end')
        gross_pay_str = data.get('gross_pay')
        deductions_str = data.get('deductions', '0')
        hours_worked_str = data.get('hours_worked')
        notes = data.get('notes', '')

        if not all([pay_period_start, pay_period_end, gross_pay_str]):
            return JsonResponse({'success': False, 'error': 'Missing required fields.'}, status=400)

        gross_pay = Decimal(gross_pay_str)
        deductions = Decimal(deductions_str)
        hours_worked = Decimal(hours_worked_str) if hours_worked_str and hours_worked_str.strip() else None

        stub.pay_period_start = pay_period_start
        stub.pay_period_end = pay_period_end
        stub.gross_pay = gross_pay
        stub.deductions = deductions
        stub.net_pay = gross_pay - deductions
        stub.hours_worked = hours_worked
        stub.notes = notes
        stub.save()
        
        # --- START OF FIX ---
        # Instead of serializing the whole object, create a simple dictionary
        stub_data = {
            'pk': stub.pk,
            'fields': {
                'pay_period_start': stub.pay_period_start.isoformat(),
                'pay_period_end': stub.pay_period_end.isoformat(),
                'gross_pay': str(stub.gross_pay),
                'deductions': str(stub.deductions),
                'net_pay': str(stub.net_pay),
            }
        }
        return JsonResponse({'success': True, 'stub': stub_data})
        # --- END OF FIX ---
        
    except (InvalidOperation, TypeError, ValueError):
        return JsonResponse({'success': False, 'error': 'Invalid number format provided for pay or hours.'}, status=400)
    except Exception as e:
        logger.error(f"Error updating pay stub {stub_id}: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': 'An unexpected server error occurred.'}, status=500)

# --- API endpoint for deleting a Pay Stub ---
@login_required
@require_POST
def delete_pay_stub_api(request, stub_id):
    practitioner = get_object_or_404(Practitioner, user=request.user)
    stub = get_object_or_404(PayStub, id=stub_id, staff__practitioner=practitioner)
    stub.delete()
    return JsonResponse({'success': True})

#<-- MANAGE PLATFORM SUBSCRIPTIONS VIEW -->
class ManageSubscriptionsView(LoginRequiredMixin, View):
    """
    Redirects the user to the subscription management tab within the main Settings page.
    """
    def get(self, request, *args, **kwargs):
        settings_url = reverse('practitioners:settings')
        return HttpResponseRedirect(f"{settings_url}?tab=subscription")

#<-- PLATFORM SUBSCRIPTION PLANS VIEW -->
class SubscriptionPlansView(LoginRequiredMixin, View):
    """
    Displays available platform subscription plans (e.g., White Label, Storage)
    and handles the purchase or cancellation of these recurring plans.
    """
    template_name = 'frontend/template/subscription_plans.html'

    def get(self, request):
        practitioner = get_object_or_404(Practitioner, user=request.user)
        active_subscriptions = {sub.subscription_type for sub in Subscription.objects.filter(practitioner=practitioner, is_active=True)}
        context = {'active_subscriptions': active_subscriptions}
        return render(request, self.template_name, context)

    def post(self, request):
        """Handles purchasing or canceling a subscription."""
        practitioner = get_object_or_404(Practitioner, user=request.user)
        wallet = get_object_or_404(PractitionerWallet, practitioner=practitioner)
        action = request.POST.get('action')
        sub_type = request.POST.get('subscription_type')

        # 1. Handle One-Time Purchases first
        if sub_type == 'ai_website':
            price = Decimal('78.00')
            if action == 'subscribe':
                if wallet.balance < price:
                    messages.error(request, "Insufficient wallet balance for this purchase.")
                    return redirect('practitioners:wallet') # Redirect to wallet to add funds

                with transaction.atomic():
                    wallet.balance -= price
                    wallet.save()
                    WalletTransaction.objects.create(
                        wallet=wallet,
                        amount=-price,
                        transaction_type='subscription',
                        description="Purchase of AI Generated Website"
                    )
                    Subscription.objects.create(
                        practitioner=practitioner,
                        subscription_type=sub_type,
                        is_active=True,
                        stripe_subscription_id=f"one-time_{sub_type}" # Mark as one-time
                    )
                messages.success(request, "Successfully purchased the AI Generated Website!")
            return redirect('practitioners:subscription_plans')

        # 2. Handle Recurring Subscriptions
        recurring_subscription_details = {
            'white_label': {'price': Decimal('399.00'), 'stripe_price_id': settings.STRIPE_WHITELABEL_PRICE_ID},
            'storage': {'price': Decimal('9.00'), 'stripe_price_id': settings.STRIPE_STORAGE_PRICE_ID},
        }

        detail = recurring_subscription_details.get(sub_type)
        if not detail:
            messages.error(request, "Invalid subscription type.")
            return redirect('practitioners:subscription_plans')

        if action == 'subscribe':
            if not wallet.stripe_payment_method_id:
                messages.error(request, "Please add a payment method to your wallet for subscriptions.")
                return redirect('practitioners:wallet')

            try:
                stripe_sub = stripe.Subscription.create(
                    customer=practitioner.stripe_customer_id,
                    items=[{'price': detail['stripe_price_id']}],
                    default_payment_method=wallet.stripe_payment_method_id,
                    metadata={'practitioner_id': practitioner.id, 'subscription_type': sub_type}
                )
                Subscription.objects.create(
                    practitioner=practitioner,
                    subscription_type=sub_type,
                    stripe_subscription_id=stripe_sub.id,
                    is_active=True
                )
                messages.success(request, f"Successfully subscribed to {sub_type.replace('_', ' ').title()}!")
            except stripe.error.StripeError as e:
                messages.error(request, f"Stripe Error: {e.user_message}")

        elif action == 'cancel':
            try:
                subscription_to_cancel = Subscription.objects.get(practitioner=practitioner, subscription_type=sub_type, is_active=True)
                stripe.Subscription.delete(subscription_to_cancel.stripe_subscription_id)
                subscription_to_cancel.is_active = False
                subscription_to_cancel.save()
                messages.success(request, "Subscription canceled successfully.")
            except (Subscription.DoesNotExist, stripe.error.StripeError) as e:
                messages.error(request, f"Could not cancel subscription: {e}")

        return redirect('practitioners:subscription_plans')

#<-- CREATE STRIPE PAYMENT INTENT (FOR APPOINTMENTS) -->
@login_required
def create_payment_intent(request, appointment_id):
    """
    Creates a Stripe PaymentIntent for a specific appointment, enabling a client-side
    payment flow. Includes application fee logic for Stripe Connect.
    """
    appointment = get_object_or_404(Appointment, id=appointment_id)
    practitioner = appointment.practitioner

    if not practitioner.stripe_account_id:
        return JsonResponse({'error': 'Practitioner account is not connected to Stripe.'}, status=400)

    payment_intent = stripe.PaymentIntent.create(
        amount=int(appointment.price * 100),
        currency="cad",
        application_fee_amount=int(appointment.price * 100 * 0.05), # Example 5% platform fee
        transfer_data={"destination": practitioner.stripe_account_id},
    )
    return JsonResponse({"client_secret": payment_intent.client_secret})

#<-- STRIPE TERMINAL: CREATE CONNECTION TOKEN (API) -->
@login_required
def create_terminal_connection_token(request):
    """
    Creates and returns a Stripe Terminal ConnectionToken for Tap to Pay.
    """
    try:
        token = stripe.terminal.ConnectionToken.create()
        return JsonResponse({'secret': token.secret})
    except Exception as e:
        logger.error(f"Stripe ConnectionToken Error: {e}")
        return JsonResponse({'error': str(e)}, status=500)

#<-- STRIPE TERMINAL: CREATE PAYMENT INTENT (API) -->
@login_required
@require_POST
def create_terminal_payment_intent(request):
    """
    Creates a PaymentIntent specifically for a Stripe Terminal transaction.
    """
    try:
        data = json.loads(request.body)
        appointment = get_object_or_404(Appointment, id=data.get('appointment_id'), practitioner=request.user.practitioner_profile)

        payment_intent = stripe.PaymentIntent.create(
            amount=int(appointment.price * 100),
            currency="cad",
            payment_method_types=['card_present'],
            capture_method='manual', # Crucial for two-step Terminal flow
            transfer_data={"destination": appointment.practitioner.stripe_account_id},
        )
        return JsonResponse({'client_secret': payment_intent.client_secret})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

#<-- STRIPE CONNECT: CREATE PAYMENT LINK -->
@login_required
def create_payment_link(request):
    """
    Creates a Stripe Checkout Session to accept a payment on behalf of a practitioner.
    This uses the practitioner's connected Stripe account as the destination for the funds.
    """
    practitioner = get_object_or_404(Practitioner, user=request.user)
    if not practitioner.stripe_account_id or not practitioner.stripe_onboarding_complete:
        messages.error(request, "Cannot create payment links until your Stripe account is fully connected.")
        return redirect('practitioners:my_finances')

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'cad',
                    'product_data': {'name': f'Service from {practitioner.business_name}'},
                    'unit_amount': 5000  # Example: $50.00
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.build_absolute_uri(reverse('practitioners:my_finances')) + '?payment=success',
            cancel_url=request.build_absolute_uri(reverse('practitioners:my_finances')) + '?payment=cancelled',
            # This is the key part for Stripe Connect
            payment_intent_data={
                'application_fee_amount': 500,  # Example: $5.00 platform fee
                'transfer_data': {
                    'destination': practitioner.stripe_account_id
                },
            },
        )
        return redirect(checkout_session.url)
    except stripe.error.StripeError as e:
        messages.error(request, f"Could not create a payment session: {e}")
        return redirect('practitioners:my_finances')

#<-- STRIPE TERMINAL: CAPTURE PAYMENT (API) -->
@csrf_exempt
@require_POST
@login_required
def capture_terminal_payment(request):
    """
    Captures a previously created and processed Terminal PaymentIntent.
    """
    try:
        data = json.loads(request.body)
        intent = stripe.PaymentIntent.capture(data.get('payment_intent_id'))

        # Here you would find the associated appointment and create your local Payment record.

        return JsonResponse({'status': 'succeeded'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

# =============================================================================
# PRACTITIONER WALLET MANAGEMENT VIEWS
# =============================================================================

#<-- WALLET VIEW -->
class WalletView(LoginRequiredMixin, View):
    """
    Displays the practitioner's wallet balance, transaction history,
    and settings for manual and automatic deposits on a dedicated page.
    """
    template_name = 'frontend/template/wallet.html'

    def get(self, request):
        practitioner = get_object_or_404(Practitioner, user=request.user)
        wallet, _ = PractitionerWallet.objects.get_or_create(practitioner=practitioner)
        transactions = wallet.transactions.all().order_by('-created_at')[:20]

        context = {
           'wallet': wallet,
           'transactions': transactions,
           'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """Handles updates to auto-recharge settings."""
        practitioner = get_object_or_404(Practitioner, user=request.user)
        wallet = get_object_or_404(PractitionerWallet, practitioner=practitioner)

        wallet.auto_recharge_enabled = 'auto_recharge_enabled' in request.POST
        try:
            wallet.recharge_threshold = Decimal(request.POST.get('recharge_threshold', '10.00'))
            wallet.recharge_amount = Decimal(request.POST.get('recharge_amount', '20.00'))
            wallet.save()
            messages.success(request, "Auto-recharge settings updated successfully.")
        except InvalidOperation:
            messages.error(request, "Please enter valid decimal numbers for recharge settings.")

        return redirect('practitioners:wallet')

#<-- CREATE CHECKOUT SESSION FOR WALLET TOP-UP -->
class CreateCheckoutSessionView(LoginRequiredMixin, View):
    """
    Creates a Stripe Checkout session for manually adding funds to the wallet.
    """
    def post(self, request, *args, **kwargs):
        try:
            amount = int(request.POST.get('amount'))
            if amount < 5: # Enforce a minimum
                messages.error(request, "The minimum amount to add is $5.00.")
                return redirect(reverse('practitioners:settings') + "?tab=wallet")

            practitioner = get_object_or_404(Practitioner, user=request.user)

            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': { 'currency': 'cad', 'product_data': {'name': 'Wallet Top-Up'}, 'unit_amount': amount * 100 },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=request.build_absolute_uri(reverse('practitioners:wallet_recharge_success')),
                cancel_url=request.build_absolute_uri(reverse('practitioners:wallet_recharge_cancel')),
                metadata={'practitioner_id': practitioner.id, 'type': 'wallet_deposit'}
            )
            return redirect(checkout_session.url, code=303)
        except Exception as e:
            messages.error(request, f"An error occurred while creating the payment session: {e}")
            return redirect(reverse('practitioners:settings') + "?tab=wallet")

#<-- WALLET RECHARGE SUCCESS VIEW -->
class WalletRechargeSuccessView(LoginRequiredMixin, TemplateView):
    """
    Renders a success page after a Stripe checkout. The actual balance update
    is handled by the webhook to ensure reliability.
    """
    template_name = 'frontend/template/wallet_recharge_success.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        messages.info(self.request, "Your payment is processing. Your new balance will be reflected in your wallet shortly.")
        return context

#<-- WALLET RECHARGE CANCEL VIEW -->
class WalletRechargeCancelView(LoginRequiredMixin, View):
    """
    Redirects with a message if the user cancels the Stripe checkout process.
    """
    def get(self, request, *args, **kwargs):
        messages.warning(request, "The transaction was cancelled. Your wallet has not been charged.")
        return redirect(reverse('practitioners:settings') + "?tab=wallet")

#<-- SETUP PAYMENT METHOD FOR FUTURE USE (API) -->
@login_required
def setup_payment_method_for_future_usage(request):
    """
    Creates a Stripe SetupIntent to save a card for features like auto-recharging.
    Returns a client_secret for the frontend to use with Stripe.js.
    """
    practitioner, _ = Practitioner.objects.get_or_create(user=request.user)
    if not practitioner.stripe_customer_id:
        customer = stripe.Customer.create(email=practitioner.user.email, name=practitioner.user.get_full_name())
        practitioner.stripe_customer_id = customer.id
        practitioner.save()

    try:
        setup_intent = stripe.SetupIntent.create(
            customer=practitioner.stripe_customer_id,
            payment_method_types=['card'],
            usage='off_session',
            metadata={'practitioner_id': practitioner.id}
        )
        return JsonResponse({'clientSecret': setup_intent.client_secret})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

#<-- GET WALLET BALANCE (API) -->
@login_required
@require_http_methods(["GET"])
def get_wallet_balance(request):
    """
    API endpoint to retrieve the current wallet balance for the logged-in practitioner.
    """
    try:
        practitioner = get_object_or_404(Practitioner, user=request.user)
        wallet, _ = PractitionerWallet.objects.get_or_create(practitioner=practitioner)
        return JsonResponse({'balance': float(wallet.balance)})
    except Exception as e:
        logger.error(f"Error fetching wallet balance for user {request.user.id}: {e}")
        return JsonResponse({'error': 'Could not retrieve wallet balance.'}, status=500)

#<-- ATTACH PAYMENT METHOD (API) -->
class AttachPaymentMethodView(LoginRequiredMixin, View):
    """
    Attaches a new payment method to the Stripe customer and updates the wallet.
    This view is called by the frontend JavaScript on the wallet page.
    """
    def post(self, request, *args, **kwargs):
        practitioner = get_object_or_404(Practitioner, user=request.user)
        wallet = get_object_or_404(PractitionerWallet, practitioner=practitioner)
        payment_method_id = request.POST.get('payment_method_id')

        if not payment_method_id:
            return JsonResponse({'error': 'Payment method ID is required.'}, status=400)

        try:
            # Attach the new payment method to the Stripe Customer
            stripe.PaymentMethod.attach(payment_method_id, customer=practitioner.stripe_customer_id)

            # Set it as the default payment method for future charges
            stripe.Customer.modify(
                practitioner.stripe_customer_id,
                invoice_settings={'default_payment_method': payment_method_id}
            )

            # Save the card's last 4 digits for display purposes
            pm = stripe.PaymentMethod.retrieve(payment_method_id)
            wallet.stripe_payment_method_id = payment_method_id
            wallet.card_last4 = pm.card.last4
            wallet.save()

            return JsonResponse({'success': True, 'card_last4': pm.card.last4})
        except stripe.error.StripeError as e:
            return JsonResponse({'error': str(e)}, status=400)

# =============================================================================
# CLIENT SUBSCRIPTION PLAN VIEWS
# =============================================================================

#<-- MANAGE CLIENT SUBSCRIPTION PLANS -->
class ClientSubscriptionPlanManageView(LoginRequiredMixin, View):
    """
    Handles creating, editing, and deleting client subscription plans.
    """
    def post(self, request):
        practitioner = get_object_or_404(Practitioner, user=request.user)
        action = request.POST.get('action', 'save')
        plan_id = request.POST.get('plan_id')

        if action == 'delete' and plan_id:
            try:
                plan = ClientSubscriptionPlan.objects.get(id=plan_id, practitioner=practitioner)
                # You might want to check if any clients are subscribed before deleting
                plan_name = plan.name
                plan.delete()
                messages.success(request, f"The plan '{plan_name}' has been deleted.")
            except ClientSubscriptionPlan.DoesNotExist:
                messages.error(request, "The plan you tried to delete was not found.")
        else: # Save or Create
            form_data = {
                'name': request.POST.get('plan_name'),
                'price': Decimal(request.POST.get('price')),
                'features': request.POST.get('features')
            }
            if plan_id:
                ClientSubscriptionPlan.objects.filter(id=plan_id, practitioner=practitioner).update(**form_data)
                messages.success(request, f"Plan '{form_data['name']}' updated successfully.")
            else:
                ClientSubscriptionPlan.objects.create(practitioner=practitioner, **form_data)
                messages.success(request, f"New plan '{form_data['name']}' created successfully.")

        return redirect(f"{reverse('practitioners:my_finances')}?tab=client_plans")

#<-- CREATE CLIENT SUBSCRIPTION LINK -->
@login_required
def create_client_subscription_link(request):
    """
    Creates a Stripe Checkout session in 'setup' mode to pre-authorize a client's
    payment method for a recurring subscription on the practitioner's Stripe account.
    """
    if request.method == 'POST':
        practitioner = get_object_or_404(Practitioner, user=request.user)
        if not practitioner.stripe_account_id:
            messages.error(request, "You must connect your Stripe account before creating subscription links.")
            return redirect(reverse('practitioners:my_finances') + '?tab=client_plans')

        try:
            client = get_object_or_404(Client, id=request.POST.get('client_id'))
            plan = get_object_or_404(ClientSubscriptionPlan, id=request.POST.get('plan_id'))

            # Create a Stripe Customer on the connected account for the client
            stripe_customer = stripe.Customer.create(
                email=client.user.email, name=client.user.get_full_name(),
                stripe_account=practitioner.stripe_account_id,
            )

            # The webhook will handle creating the actual subscription after setup
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                mode='setup',
                customer=stripe_customer.id,
                success_url=request.build_absolute_uri(reverse('practitioners:my_finances')) + '?sub_success=true',
                cancel_url=request.build_absolute_uri(reverse('practitioners:my_finances')) + '?sub_cancel=true',
                metadata={
                    'type': 'client_subscription_setup', 'client_id': client.id,
                    'plan_id': plan.id, 'practitioner_stripe_id': practitioner.stripe_account_id,
                },
                stripe_account=practitioner.stripe_account_id,
            )

            # For demonstration, we show the link. In a real app, you would email this to the client.
            messages.success(request, f"Share this link with your client to subscribe: {session.url}")

        except (Http404, stripe.error.StripeError) as e:
            messages.error(request, f"Could not create subscription link: {e}")

    return redirect(reverse('practitioners:my_finances') + '?tab=client_plans')

#<-- CREATE STRIPE ACCOUNT SESSION (API) -->
@login_required
def create_stripe_account_session(request):
    """
    API endpoint to create a Stripe Account Session for the frontend.
    """
    practitioner = get_object_or_404(Practitioner, user=request.user)
    if not practitioner.stripe_account_id:
        return JsonResponse({'error': 'Stripe account not connected.'}, status=400)

    try:
        # Define your App IDs here
        quickbooks_app_id = "com.example.acodeistripeapp" # Replace with your actual QuickBooks App ID from Stripe
        xero_app_id = "com.xero.stripeapp" # Replace with your actual Xero App ID from Stripe

        # Create the account session with the correct components for embedded apps
        account_session = stripe.AccountSession.create(
            account=practitioner.stripe_account_id,
            components={
                "app_install": {"enabled": True, "allowed_apps": [quickbooks_app_id, xero_app_id]},
                "app_viewport": {"enabled": True, "allowed_apps": [quickbooks_app_id, xero_app_id]},
            }
        )

        # Return the client_secret AND the app IDs that the frontend needs
        return JsonResponse({
            'client_secret': account_session.client_secret,
            'quickbooks_app_id': quickbooks_app_id,
            'xero_app_id': xero_app_id,
        })
    except stripe.error.StripeError as e:
        logger.error(f"Error creating Stripe Account Session: {e}")
        return JsonResponse({'error': str(e)}, status=500)

# =============================================================================
# COMMUNICATIONS & CHAT VIEWS
# =============================================================================

#<-- COMMUNICATIONS VIEW -->
class CommunicationsView(LoginRequiredMixin, View):
    """
    Renders the main communications page, ensuring a conversation exists
    for every client and ordering them by the most recent message.
    """
    template_name = 'frontend/template/communications.html'

    def get(self, request):
        practitioner = get_object_or_404(Practitioner, user=request.user)

        # Get all clients associated with the practitioner
        all_clients = practitioner.clients.all()

        # Find which of these clients already have a conversation record
        clients_with_conversations = Conversation.objects.filter(
            practitioner=practitioner
        ).values_list('client_id', flat=True)

        # Identify clients who are missing a conversation object
        clients_to_create_conv_for = all_clients.exclude(id__in=clients_with_conversations)

        # Create the missing conversation objects in a single, efficient batch query
        if clients_to_create_conv_for.exists():
            new_conversations = [
                Conversation(practitioner=practitioner, client=client)
                for client in clients_to_create_conv_for
            ]
            Conversation.objects.bulk_create(new_conversations)

        # Now, it's safe to fetch all conversations to display.
        # This will include any duplicates until they are cleaned from the database.
        conversations = Conversation.objects.filter(
            practitioner=practitioner
        ).select_related('client__user').order_by('-last_message_at')

        context = {'conversations': conversations}
        return render(request, self.template_name, context)

#<-- CONVERSATION DETAIL (API) -->
@login_required
def conversation_detail_api(request, conversation_id):
    """
    API endpoint to fetch all messages for a specific conversation.
    This version is hardened against missing user or attachment data.
    """
    practitioner = get_object_or_404(Practitioner, user=request.user)
    conversation = get_object_or_404(Conversation, id=conversation_id, practitioner=practitioner)

    # Safely process messages, especially attachment URLs
    messages_data = []
    for msg in conversation.messages.all().order_by('timestamp'):
        attachment_url = None
        try:
            if msg.attachment:
                attachment_url = msg.attachment.url
        except Exception:
            # This handles cases where the file is missing from storage
            attachment_url = None 
            
        messages_data.append({
            'sender_type': msg.sender_type,
            'content': msg.content,
            'timestamp': msg.timestamp.strftime('%b %d, %I:%M %p'),
            'send_type': msg.send_type,
            'attachment_url': attachment_url
        })

    client = conversation.client
    client_name = "Unknown Client"
    client_initials = "??"

    # Safely get client name and initials, checking if a user is linked
    if hasattr(client, 'user') and client.user:
        client_name = client.user.get_full_name()
        if client.user.first_name and client.user.last_name:
            client_initials = f"{client.user.first_name[0]}{client.user.last_name[0]}".upper()
    elif client.first_name: # Fallback to client's own name fields
        client_name = client.get_full_name()
        if client.first_name and client.last_name:
            client_initials = f"{client.first_name[0]}{client.last_name[0]}".upper()

    client_info = {
        'name': client_name,
        'initials': client_initials,
    }

    return JsonResponse({'client': client_info, 'messages': messages_data})

#<-- SEND MESSAGE (API) -->

@login_required
@require_POST
def send_message_api(request, conversation_id):
    """
    API endpoint for the practitioner to send a message to a client.
    """
    practitioner = get_object_or_404(Practitioner, user=request.user)
    conversation = get_object_or_404(Conversation, id=conversation_id, practitioner=practitioner)

    content = request.POST.get('content', '')
    attachment = request.FILES.get('attachment')
    send_type = request.POST.get('send_type', 'secure')

    if not content and not attachment:
        return JsonResponse({'error': 'Message cannot be empty.'}, status=400)

    # Handle sending SMS via Telnyx if selected
    if send_type == 'sms':
        if not conversation.client.phone_number:
            return JsonResponse({'error': 'Client does not have a phone number.'}, status=400)
        # This function sends the SMS via Telnyx
        send_sms_via_telnyx(conversation.client.phone_number, content)

    # Save the message to our database with the correct type
    message = Message.objects.create(
        conversation=conversation, sender_type='practitioner',
        content=content, attachment=attachment, send_type=send_type
    )
    conversation.last_message_at = timezone.now()
    conversation.save(update_fields=['last_message_at'])

    # Return the full message object, including the send_type
    return JsonResponse({
        'status': 'success',
        'message': {
            'sender_type': message.sender_type,
            'content': message.content,
            'timestamp': message.timestamp.strftime('%b %d, %I:%M %p'),
            'attachment_url': message.attachment.url if message.attachment else None,
            'send_type': message.send_type
        }
    })

@login_required
def create_video_call_api(request, conversation_id):
    if request.method == 'POST':
        practitioner = get_object_or_404(Practitioner, user=request.user)
        conversation = get_object_or_404(Conversation, id=conversation_id, practitioner=practitioner)

        video_call = VideoCall.objects.create(
            conversation=conversation,
            created_by=request.user,
            room_name=uuid.uuid4().hex
        )

        # --- THIS IS THE KEY FIX ---
        # Manually construct the full URL for the client's subdomain.
        client_domain = getattr(settings, 'CLIENT_PORTAL_URL', 'https://client.xdulr.com')
        client_join_url = f"{client_domain}/video-call/{video_call.room_name}/"
        # --- END OF FIX ---
        
        message_content = f"I've started a video call. <a href='{client_join_url}' target='_blank'>Click here to join.</a>"

        message = Message.objects.create(
            conversation=conversation,
            sender_type='practitioner',
            content=message_content,
            send_type='secure'
        )

        return JsonResponse({
            'status': 'success',
            'room_name': video_call.room_name,
            'message': {
                'sender_type': message.sender_type,
                'content': message.content,
                'timestamp': message.timestamp.strftime('%b %d, %I:%M %p'),
                'attachment_url': None,
                'send_type': 'secure'
            }
        })
    return JsonResponse({'error': 'Invalid request method'}, status=405)


#<-- SEND VIDEO LINK (API) -->
@require_http_methods(["POST"])
@login_required
def send_video_link_api(request):
    """
    API endpoint to send a one-off message (like a video link) to a client via SMS.
    Note: It's recommended to use the main 'send_message_api' instead to maintain
    a complete conversation history.
    """
    try:
        data = json.loads(request.body)
        client_id = data.get('client_id')
        message = data.get('message')

        if not client_id or not message:
            return JsonResponse({'status': 'error', 'message': 'Client ID and message are required.'}, status=400)

        client = get_object_or_404(Client, id=client_id)

        if not client.user.phone:
            return JsonResponse({'status': 'error', 'message': 'Client does not have a phone number.'}, status=400)

        send_sms_via_telnyx(client.user.phone, message)

        return JsonResponse({'status': 'success', 'message': 'Video link sent successfully.'})

    except Client.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Client not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
def video_call_view(request, room_name):
    # Ensure the video call exists and belongs to this practitioner
    get_object_or_404(
        VideoCall, 
        room_name=room_name, 
        conversation__practitioner=request.user.practitioner_profile
    )
    context = {
        'room_name': room_name,
        'user_name': request.user.get_full_name()
    }
    return render(request, 'frontend/template/video_call.html', context)

# =============================================================================
# AI VOICE ASSISTANT VIEWS
# =============================================================================

class AIVoiceAssistantView(LoginRequiredMixin, View):
    """
    Manages the AI Voice Assistant, including settings, phone numbers,
    knowledge base, and call logs.
    """
    template_name = 'frontend/template/ai_voice_assistant.html'

    def get(self, request):
        practitioner = get_object_or_404(Practitioner, user=request.user)
        active_tab = request.GET.get('tab', 'overview')
        agent, _ = AIAgent.objects.get_or_create(practitioner=practitioner)

        context = {
            'tab': active_tab,
            'agent': agent,
            'practitioner': practitioner,
        }

        # Add the specific context needed for each tab
        if active_tab == 'overview' or not active_tab:
            context['call_logs_today'] = CallLog.objects.filter(practitioner=practitioner, timestamp__date=timezone.now().date()).count()
            context['active_number'] = TelnyxPhoneNumber.objects.filter(practitioner=practitioner, is_active=True).first()

        elif active_tab == 'phone_numbers':
            phone_numbers = TelnyxPhoneNumber.objects.filter(practitioner=practitioner).order_by('phone_number')
            context['phone_numbers'] = phone_numbers
            context['is_first_number'] = not phone_numbers.exists()

        elif active_tab == 'knowledge_base':
            context['documents'] = KnowledgeBaseDocument.objects.filter(practitioner=practitioner).order_by('-uploaded_at')

        elif active_tab == 'call_logs':
            context['call_logs'] = CallLog.objects.filter(practitioner=practitioner).order_by('-timestamp')

        return render(request, self.template_name, context)

    def post(self, request):
        practitioner = get_object_or_404(Practitioner, user=request.user)
        action = request.POST.get('action')
        telnyx.api_key = settings.TELNYX_API_KEY

        if action == 'save_ai_settings':
            agent, _ = AIAgent.objects.get_or_create(practitioner=practitioner)
            agent.voice = request.POST.get('voice', agent.voice)
            agent.personality_prompt = request.POST.get('personality_prompt', agent.personality_prompt)
            agent.is_active = 'agent_status' in request.POST
            agent.save()
            messages.success(request, "AI Agent settings saved successfully.")
            return redirect(f"{reverse('practitioners:ai_voice_assistant')}?tab=settings")

        elif action == 'upload_document':
            if 'document' in request.FILES:
                doc_file = request.FILES['document']
                KnowledgeBaseDocument.objects.create(
                    practitioner=practitioner, file=doc_file,
                    file_name=doc_file.name, file_type=os.path.splitext(doc_file.name)[1].upper().replace('.', '')
                )
                messages.success(request, f"Document '{doc_file.name}' uploaded successfully.")
            return redirect(f"{reverse('practitioners:ai_voice_assistant')}?tab=knowledge_base")

        elif action == 'delete_document':
            doc_id = request.POST.get('doc_id')
            doc = get_object_or_404(KnowledgeBaseDocument, id=doc_id, practitioner=practitioner)
            doc_name = doc.file_name
            doc.delete()
            messages.success(request, f"Document '{doc_name}' deleted.")
            return redirect(f"{reverse('practitioners:ai_voice_assistant')}?tab=knowledge_base")

        elif action == 'buy_number':
            phone_number_to_buy = request.POST.get('phone_number')
            telnyx_monthly_cost = Decimal(request.POST.get('telnyx_monthly_cost', '0.00'))
            telnyx_setup_cost = Decimal(request.POST.get('telnyx_setup_cost', '0.00'))
            is_first_number = not TelnyxPhoneNumber.objects.filter(practitioner=practitioner).exists()

            platform_fee = Decimal('0.00') if is_first_number else Decimal('5.00')
            total_cost_from_wallet = platform_fee + telnyx_monthly_cost + telnyx_setup_cost

            try:
                with transaction.atomic():
                    wallet, _ = PractitionerWallet.objects.get_or_create(practitioner=practitioner)
                    if wallet.balance < total_cost_from_wallet:
                        return JsonResponse({'success': False, 'error': 'Insufficient wallet balance. Please add funds to continue.'})

                    # --- FIX: Fetch the billing group and add it and the username to the API call. ---
                    billing_groups = telnyx.BillingGroup.list()
                    if not billing_groups.data:
                        return JsonResponse({'success': False, 'error': 'No billing groups found in your Telnyx account. Please configure one first.'})
                    
                    billing_group_id = billing_groups.data[0].id
                    customer_reference = request.user.username

                    telnyx.NumberOrder.create(
                        phone_numbers=[{
                            'phone_number': phone_number_to_buy,
                            'connection_id': settings.TELNYX_VOICE_CONNECTION_ID,
                            'messaging_profile_id': settings.TELNYX_MESSAGING_PROFILE_ID,
                            'billing_group_id': billing_group_id,
                            'customer_reference': customer_reference,
                        }]
                    )

                    wallet.balance -= total_cost_from_wallet
                    wallet.save()
                    WalletTransaction.objects.create(
                        wallet=wallet, amount=-total_cost_from_wallet, transaction_type='charge',
                        description=f"Purchase of number {phone_number_to_buy}"
                    )

                    TelnyxPhoneNumber.objects.create(
                        practitioner=practitioner,
                        phone_number=phone_number_to_buy,
                        monthly_cost=telnyx_monthly_cost,
                        setup_cost=telnyx_setup_cost,
                        is_active=True
                    )
                    return JsonResponse({'success': True})

            except Exception as e:
                logger.error(f"Error buying Telnyx number for practitioner {practitioner.id}: {e}")
                return JsonResponse({'success': False, 'error': 'An external error occurred while purchasing the number. Please try again later.'})

        elif action == 'delete_number':
            number_id = request.POST.get('number_id')
            number_to_delete = get_object_or_404(TelnyxPhoneNumber, id=number_id, practitioner=practitioner)
            
            try:
                number_instance = telnyx.PhoneNumber.retrieve(number_to_delete.phone_number)
                number_instance.delete()

                number_to_delete.delete()
                messages.success(request, f"Phone number {number_to_delete.phone_number} released successfully.")
            except Exception as e:
                logger.error(f"Error deleting Telnyx number {number_to_delete.phone_number}: {e}")
                messages.error(request, "Could not release the phone number at this time. An external error occurred.")

            return redirect(f"{reverse('practitioners:ai_voice_assistant')}?tab=phone_numbers")

        return redirect('practitioners:ai_voice_assistant')


@login_required
def search_available_numbers(request):
    """
    API endpoint to search for available phone numbers from Telnyx.
    """
    area_code = request.GET.get('area_code')
    if not area_code or not area_code.isdigit() or len(area_code) != 3:
        return JsonResponse({'error': 'A valid 3-digit area code is required.'}, status=400)

    try:
        telnyx.api_key = settings.TELNYX_API_KEY
        # --- FIX: Added 'country_code' to the filter. ---
        # This makes the search more specific and can resolve issues with trial accounts
        # that are restricted to certain countries.
        available_numbers = telnyx.AvailablePhoneNumber.list(
            filter={
                'national_destination_code': area_code,
                'country_code': 'CA', # Assuming a Canadian user base
                'features': ['voice', 'sms'],
                'limit': 10
            }
        )
        
        numbers = []
        if available_numbers.data:
            for num in available_numbers.data:
                cost_info = num.cost_information or {}
                numbers.append({
                    'phone_number': num.phone_number,
                    'monthly_cost': float(cost_info.get('monthly_price', 0.0)),
                    'setup_cost': float(cost_info.get('setup_price', 0.0)),
                    'currency': cost_info.get('currency', 'CAD')
                })

        return JsonResponse({'numbers': numbers})
    except Exception as e:
        logger.error(f"Telnyx number search failed for area code {area_code}: {e}")
        # Provide a more user-friendly error message
        return JsonResponse({'error': 'Could not search for numbers at this time. This may be due to an invalid area code or an issue with the provider.'}, status=500)


# =============================================================================
# REPORTS
# =============================================================================

#<-- REPORTS VIEW -->
class Reports(LoginRequiredMixin, View):
    """
    Generates complex reports for financials, appointments, and clients
    based on a selected date range and displays them in various tabs.
    """
    template_name = 'frontend/template/reports.html'

    def get(self, request):
        practitioner = get_object_or_404(Practitioner, user=request.user)

        active_tab = request.GET.get('tab', 'overview')
        date_range_filter = request.GET.get('date_range', 'last30')
        end_date = timezone.now().date()

        if date_range_filter == 'last90':
            start_date = end_date - timedelta(days=89)
        elif date_range_filter == 'thisyear':
            start_date = end_date.replace(month=1, day=1)
        else: # Default to last30
            start_date = end_date - timedelta(days=29)

        context = {
            'tab': active_tab,
            'date_range': date_range_filter,
            'practitioner': practitioner,
        }

        # Call the appropriate data generation method based on the active tab
        if active_tab == 'overview':
            context.update(self._generate_overview_report(practitioner, start_date, end_date))
        elif active_tab == 'financials':
            context.update(self._generate_financials_report(practitioner, start_date, end_date))
        elif active_tab == 'appointments':
            context.update(self._generate_appointments_report(practitioner, start_date, end_date))
        elif active_tab == 'clients':
            context.update(self._generate_clients_report(practitioner, start_date, end_date))
        elif active_tab == 'demand_forecasting':
            context.update(self._generate_demand_forecasting_report(practitioner, start_date, end_date))

        return render(request, self.template_name, context)

    def _generate_overview_report(self, practitioner, start_date, end_date):
        """Generates data for the Overview tab."""
        period_days = (end_date - start_date).days + 1
        prev_start_date = start_date - timedelta(days=period_days)
        prev_end_date = start_date - timedelta(days=1)

        appointments = Appointment.objects.filter(practitioner=practitioner, date__range=[start_date, end_date])
        prev_appointments = Appointment.objects.filter(practitioner=practitioner, date__range=[prev_start_date, prev_end_date])

        total_revenue = Payment.objects.filter(appointment__in=appointments, status='completed').aggregate(total=Sum('amount'))['total'] or 0
        prev_revenue = Payment.objects.filter(appointment__in=prev_appointments, status='completed').aggregate(total=Sum('amount'))['total'] or 0

        new_clients = Client.objects.filter(practitioners=practitioner, created_at__date__range=[start_date, end_date]).count()
        prev_new_clients = Client.objects.filter(practitioners=practitioner, created_at__date__range=[prev_start_date, prev_end_date]).count()

        revenue_by_month = Payment.objects.filter(appointment__practitioner=practitioner, status='completed', payment_date__range=[start_date, end_date]).annotate(
            month=TruncMonth('payment_date')
        ).values('month').annotate(total=Sum('amount')).order_by('month')

        return {
            'summary': {
                'total_revenue': total_revenue,
                'total_appointments': appointments.count(),
                'new_clients': new_clients,
                'avg_revenue_per_appt': total_revenue / appointments.count() if appointments.count() > 0 else 0,
                'revenue_change': total_revenue - prev_revenue,
                'appointments_change': appointments.count() - prev_appointments.count(),
                'clients_change': new_clients - prev_new_clients,
            },
            'chart_labels': [r['month'].strftime('%b %Y') for r in revenue_by_month],
            'chart_data': [float(r['total']) for r in revenue_by_month],
        }

    def _generate_financials_report(self, practitioner, start_date, end_date):
        """Generates data for the Financials tab."""
        payments = Payment.objects.filter(
            appointment__practitioner=practitioner,
            payment_date__range=[start_date, end_date]
        ).select_related('appointment__client__user', 'appointment__service').order_by('-payment_date')
        return {'payments': payments}

    def _generate_appointments_report(self, practitioner, start_date, end_date):
        """Generates data for the Appointments tab."""
        appointments = Appointment.objects.filter(practitioner=practitioner, date__range=[start_date, end_date])
        total_appts = appointments.count()
        cancelled_appts = appointments.filter(status='cancelled').count()

        types_data = appointments.values('service__name').annotate(count=Count('id')).order_by('-count')

        return {
            'cancellation_rate': (cancelled_appts / total_appts * 100) if total_appts > 0 else 0,
            'cancelled_count': cancelled_appts,
            'chart_labels': [t['service__name'] for t in types_data],
            'chart_data': [t['count'] for t in types_data],
        }

    def _generate_clients_report(self, practitioner, start_date, end_date):
        """Generates data for the Clients tab."""
        client_growth = Client.objects.filter(practitioners=practitioner, created_at__date__range=[start_date, end_date]).annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(count=Count('id')).order_by('month')

        return {
            'chart_labels': [c['month'].strftime('%b %Y') for c in client_growth],
            'chart_data': [c['count'] for c in client_growth],
        }

    def _generate_demand_forecasting_report(self, practitioner, start_date, end_date):
        """Generates data for the Demand Forecasting tab."""
        # This is a simplified forecast. A real one would use a predictive model.
        appointments = Appointment.objects.filter(practitioner=practitioner, date__range=[start_date, end_date])
        total_revenue = Payment.objects.filter(appointment__in=appointments, status='completed').aggregate(total=Sum('amount'))['total'] or 0

        return {
            'forecast': {
                'predicted_revenue': total_revenue * Decimal('1.2'),
                'predicted_appointments': int(appointments.count() * 1.15),
                'predicted_new_clients': int(Client.objects.filter(practitioners=practitioner, created_at__date__range=[start_date, end_date]).count() * 1.1),
            },
            'chart_labels': ['Past Period', 'Next Period (Forecast)'],
            'chart_data': [appointments.count(), int(appointments.count() * 1.15)],
        }

# =============================================================================
# FORMS
# =============================================================================

#<-- FORM BUILDER VIEW -->
@login_required
def form_builder_view(request, form_id=None):
    """
    A view for practitioners to create and edit forms and their questions.
    """
    practitioner = get_object_or_404(Practitioner, user=request.user)
    if form_id:
        form_instance = get_object_or_404(Form, id=form_id, practitioner=practitioner)
    else:
        form_instance = None

    if request.method == 'POST':
        # Logic to save the form title, header, and consent text
        title = request.POST.get('title')
        header_text = request.POST.get('header_text')
        consent_text = request.POST.get('consent_text')

        if not form_instance:
            form_instance = Form.objects.create(practitioner=practitioner, title=title)

        form_instance.title = title
        form_instance.header_text = header_text
        form_instance.consent_text = consent_text
        form_instance.save()

        # Logic to save, update, and delete questions
        form_instance.questions.all().delete() # Simple approach: delete and re-create
        question_texts = request.POST.getlist('question_text')
        question_types = request.POST.getlist('question_type')

        for i, text in enumerate(question_texts):
            if text:
                Question.objects.create(
                    form=form_instance,
                    text=text,
                    question_type=question_types[i],
                    is_required='is_required_' + str(i) in request.POST,
                    order=i
                )
        return redirect('practitioners:form_builder', form_id=form_instance.id)

    context = {'form': form_instance}
    return render(request, 'frontend/template/form_builder.html', context)

#<-- CLIENT FORM FILL VIEW -->
def fill_form_view(request, form_id, client_id):
    """
    Displays the form for the client to fill out.
    """
    form_instance = get_object_or_404(Form, id=form_id)
    client = get_object_or_404(Client, id=client_id)

    if request.method == 'POST':
        answers = {}
        for question in form_instance.questions.all():
            answers[question.text] = request.POST.get(f'question_{question.id}')

        FormSubmission.objects.create(
            form=form_instance,
            client=client,
            answers=answers,
            consent_given='consent_given' in request.POST
        )
        return render(request, 'frontend/template/form_submitted.html')

    context = {'form': form_instance, 'client': client}
    return render(request, 'frontend/template/fill_form.html', context)

#<-- ADVANCED FORM BUILDER VIEW -->
@login_required
def custom_form_builder_view(request, form_id=None):
    """
    A view for practitioners to create and edit advanced, field-based forms.
    """
    practitioner = get_object_or_404(Practitioner, user=request.user)
    form_instance = None
    if form_id:
        form_instance = get_object_or_404(AdvancedForm, id=form_id, practitioner=practitioner)

    if request.method == 'POST':
        title = request.POST.get('title')
        header_text = request.POST.get('header_text')
        consent_text = request.POST.get('consent_text')

        if form_instance:
            form_instance.title = title
            form_instance.header_text = header_text
            form_instance.consent_text = consent_text
            form_instance.save()
        else:
            form_instance = AdvancedForm.objects.create(
                practitioner=practitioner,
                title=title,
                header_text=header_text,
                consent_text=consent_text
            )

        # --- THIS IS THE CORRECTED PART ---
        # Use the correct relationship name: .questions
        form_instance.questions.all().delete()

        question_texts = request.POST.getlist('question_text')
        question_types = request.POST.getlist('question_type')

        for i, text in enumerate(question_texts):
            if text:
                is_required = request.POST.get(f'is_required_{i+1}') == 'on'
                # Use the correct model name: Question
                Question.objects.create(
                    form=form_instance,
                    text=text,
                    question_type=question_types[i],
                    is_required=is_required,
                    order=i
                )
        # --- END OF CORRECTION ---

        messages.success(request, f"Successfully saved the form '{form_instance.title}'.")
        return redirect(reverse('practitioners:settings') + '?tab=forms')

    context = {'form': form_instance}
    return render(request, 'frontend/template/form_builder.html', context)

#<-- CLIENT FILL ADVANCED FORM VIEW -->
def fill_custom_form_view(request, form_id, client_id):
    """
    Displays the advanced form for the client to fill out.
    """
    form_instance = get_object_or_404(AdvancedForm, id=form_id)
    client = get_object_or_404(Client, id=client_id)

    if request.method == 'POST':
        answers = {}
        for field in form_instance.fields.all():
            answer_value = request.POST.get(f'field_{field.id}')
            answers[field.text] = answer_value

        FormSubmission.objects.create(
            form=form_instance,
            client=client,
            answers=answers,
            consent_given='consent_given' in request.POST
        )
        # Note: You will need to create this 'form_submitted.html' template
        return render(request, 'frontend/template/form_submitted.html')

    context = {'form': form_instance, 'client': client}
    # Note: You will need to create this 'fill_form.html' template
    return render(request, 'frontend/template/fill_form.html', context)


#<-- SEND FORM TO CLIENT VIEW -->
@login_required
def send_form_to_client(request, form_id):
    """
    Provides a UI to select a client and sends them a link to a specific form.
    """
    practitioner = get_object_or_404(Practitioner, user=request.user)
    client_form = get_object_or_404(ClientForm, id=form_id, practitioner=practitioner)

    if request.method == 'POST':
        client = get_object_or_404(Client, id=request.POST.get('client_id'), practitioners=practitioner)

        # In production, this link would include a unique, secure token.
        unique_form_link = f"{settings.BASE_DOMAIN}/forms/fill/{client_form.id}/{client.id}/"

        # Use your custom email sending function here.
        custom_emails.send_form_request_email(client, practitioner, client_form, unique_form_link)

        messages.success(request, f"Form '{client_form.title}' sent to {client.user.get_full_name()}.")
        return redirect(f"{reverse('practitioners:settings')}?tab=forms")

    context = {
        'form': client_form,
        'clients': Client.objects.filter(practitioners=practitioner).select_related('user'),
    }
    # You would need to create this template
    return render(request, 'frontend/template/send_form_to_client.html', context)

#<-- GET CALL TRANSCRIPT (API) -->
@login_required
def get_call_transcript_api(request, log_id):
    """
    API endpoint to retrieve the transcript for a specific call log.
    """
    call_log = get_object_or_404(CallLog, id=log_id, practitioner=request.user.practitioner_profile)
    return JsonResponse({'transcript': call_log.transcript})


# =============================================================================
# AI DASHBOARD COMMAND PROCESSOR
# =============================================================================

#<-- AI COMMAND PROCESSOR (API) -->

# Helper function to convert a PDF to an image
def convert_pdf_to_image(pdf_bytes):
    """
    Converts the first page of a PDF into a JPEG image using PyMuPDF's
    built-in capabilities for a more direct and reliable conversion.
    """
    try:
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
        first_page = pdf_document.load_page(0)  # Load the first page
        # Render at high resolution and get JPEG bytes directly from PyMuPDF
        pix = first_page.get_pixmap(dpi=300)
        return pix.tobytes("jpeg")
    except Exception as e:
        logger.error(f"Error converting PDF to image: {e}")
        return None

# Helper function to compress the image before sending
def compress_image(file_content, max_size_kb=1024, quality=85):
    """
    Compresses an image to be under a certain file size before sending to the API.
    """
    try:
        img = Image.open(io.BytesIO(file_content))

        # Convert to RGB if it has an alpha channel (like in PNGs)
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')

        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=quality, optimize=True)

        # If the image is still too large, progressively reduce quality
        while buffer.tell() / 1024 > max_size_kb and quality > 10:
            buffer = io.BytesIO()
            quality -= 5
            img.save(buffer, format="JPEG", quality=quality, optimize=True)

        return buffer.getvalue()
    except Exception as e:
        logger.error(f"Error compressing image: {e}")
        return file_content

# Helper function to call the IONOS Vision API
def extract_data_with_ionos_api(file_content, mime_type):
    """
    Uses the IONOS AI Model Hub to analyze an ID card image directly
    and return structured data.
    """
    try:
        if not settings.IONOS_API_KEY or not settings.IONOS_API_URL:
            return {'status': 'error', 'message': 'IONOS API is not configured.'}

        client = openai.OpenAI(
            api_key=settings.IONOS_API_KEY,
            base_url=settings.IONOS_API_URL,
        )

        encoded_image = base64.b64encode(file_content).decode('utf-8')

        response = client.chat.completions.create(
            model="mistralai/Mistral-Small-24B-Instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """
                            You are an expert data extraction assistant. Analyze this image of an ID card and extract the key information.
                            Return the information ONLY in a valid JSON object with the following keys: "full_name", "id_number", "dob".
                            If a piece of information cannot be found, set its value to "N/A".
                            """
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{encoded_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=300,
        )
        
        json_string = response.choices[0].message.content

        if json_string:
            json_string = json_string.strip().replace('```json', '').replace('```', '').strip()
        
        if not json_string:
            return {
                'status': 'error',
                'message': 'The AI model returned an empty response. This may be a temporary issue with the API or the uploaded image.'
            }

        extracted_data = json.loads(json_string)
        return {'status': 'success', 'data': extracted_data}

    except Exception as e:
        error_message = f"An error occurred with the IONOS AI API: {e}"
        logger.error(error_message)
        return {'status': 'error', 'message': error_message}

# Helper function to create the client profile
def create_client_from_extracted_data(practitioner, extracted_data):
    """Creates a client record from a dictionary of extracted data."""
    full_name = extracted_data.get('full_name', '').strip()
    if not full_name or full_name.lower() == 'n/a':
        return {'status': 'error', 'response_html': 'The AI could not determine a name from the document.'}

    dummy_email = f"{full_name.replace(' ', '').lower()}.{uuid4().hex[:4]}@xdulr.com"
    first_name = full_name.split()[0]
    last_name = " ".join(full_name.split()[1:]) if len(full_name.split()) > 1 else 'N/A'

    user, created = User.objects.get_or_create(
        email=dummy_email,
        defaults={'username': dummy_email, 'first_name': first_name, 'last_name': last_name}
    )

    new_client = Client.objects.create(user=user)
    new_client.practitioners.add(practitioner)

    client_data_for_card = {
        'client_id': new_client.id,
        'name': full_name,
        'address': 'N/A',
        'policy_number': extracted_data.get('id_number', 'N/A'),
        'expiry_date': 'N/A',
        'issuer': 'N/A',
    }

    return {
        'status': 'success',
        'response_html': f"Success! A client profile for <strong>{full_name}</strong> has been created.",
        'card_type': 'id-card',
        'client_data': client_data_for_card
    }

# Main view that ties everything together
@login_required
async def process_ai_command(request):
    """
    Asynchronous view that handles AI commands, compresses uploaded images,
    and uses the IONOS API for document processing.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)
    try:
        command = request.POST.get('command', '').lower().strip()
        attachment = request.FILES.get('attachment')
        practitioner = await sync_to_async(lambda: request.user.practitioner_profile)()

        if attachment:
            file_data = attachment.read()
            mime_type = attachment.content_type
            image_bytes = None

            # --- Handle PDF uploads ---
            if mime_type == 'application/pdf':
                image_bytes = await sync_to_async(convert_pdf_to_image)(file_data)
                if not image_bytes:
                    return JsonResponse({'status': 'error', 'response_html': 'Failed to convert PDF to an image.'})
            else:
                image_bytes = file_data
            
            compressed_file_data = await sync_to_async(compress_image)(image_bytes)
            
            api_result = await sync_to_async(extract_data_with_ionos_api)(
                compressed_file_data, 'image/jpeg'  # Mime type is now always jpeg
            )

            if api_result.get('status') == 'success':
                client_data = api_result.get('data', {})
                result = await sync_to_async(create_client_from_extracted_data)(practitioner, client_data)
            else:
                result = {
                    'status': 'error',
                    'response_html': api_result.get('message', 'An unknown API error occurred.'),
                    'card_type': 'error-card'
                }
            return JsonResponse(result)

        if command:
            result = await handle_intelligent_command(command, practitioner)
            return JsonResponse(result)

        return JsonResponse({'status': 'error', 'response_html': 'No command provided.'})
    except Exception as e:
        logger.error(f"Error in process_ai_command for user {request.user.id}: {e}", exc_info=True)
        return JsonResponse({'status': 'error', 'response_html': 'An unexpected server error occurred.'}, status=500)

# =============================================================================
# SYNCHRONOUS CARD GENERATORS
# =============================================================================

def _get_time_card():
    """Generates the HTML card for the current time."""
    now = datetime.now()
    response_html = f'<div class="card-content" style="text-align: center;"><h3>Current Time</h3><div style="font-size: 2rem; font-weight: bold;">{now.strftime("%I:%M %p")}</div></div>'
    return {'status': 'success', 'response_html': response_html, 'card_type': 'time-card'}

def _get_client_count_card(practitioner):
    """Generates the HTML card for the active client count."""
    active_clients_count = Client.objects.filter(practitioners=practitioner, status='active').count()
    response_html = f'<div class="card-content" style="text-align: center;"><h3>Active Clients</h3><div style="font-size: 2rem; font-weight: bold;">{active_clients_count}</div></div>'
    return {'status': 'success', 'response_html': response_html, 'card_type': 'client-count-card'}

def _get_appointments_today_card(practitioner):
    """Generates the HTML card for today\'s appointments."""
    today_appointments = Appointment.objects.filter(practitioner=practitioner, date=date.today()).order_by('start_time')
    if today_appointments.exists():
        response_html = "<p>Here are your appointments for today:</p><ul>"
        for appt in today_appointments:
            client_name = appt.client.user.get_full_name() if hasattr(appt.client, 'user') else 'N/A'
            service_name = appt.service.name if hasattr(appt, 'service') and appt.service else 'N/A'
            response_html += f"<li><strong>{appt.start_time.strftime('%I:%M %p')}:</strong> <span>{client_name} - {service_name}</span></li>"
        response_html += "</ul>"
    else:
        response_html = "<p>You have no appointments scheduled for today.</p>"
    return {'status': 'success', 'response_html': response_html, 'card_type': 'my-day-card'}

def _get_dashboard_summary_card(practitioner):
    """Generates the HTML card for the dashboard summary."""
    total_revenue = Payment.objects.filter(appointment__practitioner=practitioner, status='completed').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    total_appointments = Appointment.objects.filter(practitioner=practitioner).count()
    new_clients = Client.objects.filter(practitioners=practitioner, created_at__date__gte=date.today().replace(day=1)).count()
    avg_revenue = (total_revenue / total_appointments) if total_appointments > 0 else Decimal('0.00')
    response_html = f"""
        <p>Here's your quick performance overview:</p>
        <div class="stats-grid">
            <div class="stat-item"><div class="stat-label">Total Revenue</div><div class="stat-value">${total_revenue:,.2f}</div></div>
            <div class="stat-item"><div class="stat-label">Total Appointments</div><div class="stat-value">{total_appointments}</div></div>
            <div class="stat-item"><div class="stat-label">New Clients (This Month)</div><div class="stat-value">{new_clients}</div></div>
            <div class="stat-item"><div class="stat-label">Avg. Revenue/Appt</div><div class="stat-value">${avg_revenue:,.2f}</div></div>
        </div>
    """
    return {'status': 'success', 'response_html': response_html, 'card_type': 'summary-stats-card'}

def _get_wallet_balance_card(practitioner):
    """Generates the HTML card for the wallet balance."""
    wallet, _ = PractitionerWallet.objects.get_or_create(practitioner=practitioner)
    response_html = f"""
        <p>Your current wallet balance is:</p>
        <div class="balance-value">${wallet.balance:,.2f}</div>
        <div class="balance-note">This balance is used for per-appointment fees and one-time purchases.</div>
    """
    return {'status': 'success', 'response_html': response_html, 'card_type': 'balance-card'}

def _get_client_list_card(practitioner):
    """Generates the HTML card for the recent clients list."""
    clients = Client.objects.filter(practitioners=practitioner).select_related('user').order_by('-created_at')[:5]
    if clients.exists():
        client_grid_html = ""
        for client in clients:
            initials = f"{client.user.first_name[0] if client.user.first_name else ''}{client.user.last_name[0] if client.user.last_name else ''}".upper() or "CL"
            client_grid_html += f"""
                <div class="client-item">
                    <div class="client-avatar">{initials}</div>
                    <div class="client-name">{client.user.get_full_name()}</div>
                    <div class="client-email">{client.user.email or 'N/A'}</div>
                </div>
            """
        response_html = f'<p>Here are your 5 most recent clients:</p><div class="client-grid">{client_grid_html}</div>'
    else:
        response_html = "<p>You don't have any clients recorded yet.</p>"
    return {'status': 'success', 'response_html': response_html, 'card_type': 'client-list-card'}

def _get_pending_tasks_card(practitioner):
    """Generates the HTML card for pending tasks."""
    pending_tasks = Task.objects.filter(practitioner=practitioner, is_completed=False).order_by('due_date', 'created_at')
    if pending_tasks.exists():
        response_html = "<p>Here are your pending tasks:</p><ul>"
        for task in pending_tasks:
            due_date_str = task.due_date.strftime('%b %d, %Y') if task.due_date else 'N/A'
            response_html += f"<li><span class='task-title'>{task.title}</span> <span class='task-due-date'>Due: {due_date_str}</span></li>"
        response_html += "</ul>"
    else:
        response_html = "<p>You have no pending tasks. Great job!</p>"
    return {'status': 'success', 'response_html': response_html, 'card_type': 'task-list-card'}

def _get_contact_card(practitioner, command):
    """Searches for a client and returns their contact details in a card."""
    keywords_to_remove = ['contact', 'get', 'find', 'client', 'details', 'for']
    client_name_query = command
    for keyword in keywords_to_remove:
        client_name_query = client_name_query.lower().replace(keyword, "")
    client_name_query = client_name_query.strip()

    if not client_name_query:
        return {'status': 'error', 'response_html': '<p>Please specify which client you are looking for, for example: "contact Jane Doe".</p>', 'card_type': 'error-card'}

    clients_found = Client.objects.filter(practitioners=practitioner).annotate(
        full_name=Concat('user__first_name', Value(' '), 'user__last_name')
    ).filter(full_name__icontains=client_name_query)

    if clients_found.count() == 1:
        client = clients_found.first()
        response_html = f"""
            <p>Here are the contact details for {client.user.get_full_name()}:</p>
            <div class="contact-details">
                <div class="contact-item">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-3.37-3.37A19.79 19.79 0 0 1 2 4.18 2 2 0 0 1 4 2h3a2 2 0 0 1 2 2v1.72a2 2 0 0 1-.46 1.28l-2.38 2.38a2 2 0 0 0 .46 3.42l2.38 2.38a2 2 0 0 1 1.28.46z"/></svg>
                    <span class="contact-value">{client.phone_number or 'Not available'}</span>
                </div>
                <div class="contact-item">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path><polyline points="22,6 12,13 2,6"></polyline></svg>
                    <span class="contact-value">{client.user.email or 'Not available'}</span>
                </div>
            </div>
        """
        return {'status': 'success', 'response_html': response_html, 'card_type': 'contact-card'}
    elif clients_found.count() > 1:
        response_html = f'<p>I found multiple clients matching "{client_name_query}". Please be more specific:</p><ul>'
        for c in clients_found:
            response_html += f'<li>{c.user.get_full_name()}</li>'
        response_html += '</ul>'
        return {'status': 'error', 'response_html': response_html, 'card_type': 'error-card'}
    else:
        response_html = f'<p>I could not find a client named "{client_name_query}". Please check the spelling or try a different name.</p>'
        return {'status': 'error', 'response_html': response_html, 'card_type': 'error-card'}

def _book_appointment_card(practitioner, command):
    """Parses a command to book an appointment, creates it, and returns a confirmation card."""
    match = re.search(r'book appointment for (.*?) on (.*?) at (.*)', command, re.IGNORECASE)
    if not match:
        return {'status': 'error', 'response_html': '<p>I couldn\'t understand the appointment details. Please use the format: "Book appointment for [Client Name] on [Date] at [Time]".</p>', 'card_type': 'error-card'}

    client_name, date_str, time_str = match.groups()

    client = Client.objects.annotate(
        full_name=Concat('user__first_name', Value(' '), 'user__last_name')
    ).filter(practitioners=practitioner, full_name__icontains=client_name).first()

    if not client:
        return {'status': 'error', 'response_html': f'<p>Could not find a client named "{client_name}". Please create the client first.</p>', 'card_type': 'error-card'}

    try:
        # This parsing is very basic. A more robust solution might use dateparser library
        appointment_datetime = datetime.strptime(f"{date_str} {time_str}", "%d %B %Y %I:%M%p")
    except ValueError:
        return {'status': 'error', 'response_html': f'<p>I couldn\'t understand the date "{date_str}" or time "{time_str}". Please use a clear format like "7 August 2025 at 12:00PM".</p>', 'card_type': 'error-card'}

    service = Service.objects.filter(practitioner=practitioner, is_active=True).first()
    if not service:
        return {'status': 'error', 'response_html': '<p>You have no active services available to book.</p>', 'card_type': 'error-card'}

    Appointment.objects.create(
        practitioner=practitioner, client=client, service=service,
        date=appointment_datetime.date(), start_time=appointment_datetime.time(),
        end_time=(appointment_datetime + timedelta(minutes=service.duration)).time(),
        status='confirmed'
    )

    response_html = f"""
        <p>I've scheduled the appointment for you:</p>
        <div class="appointment-details">
            <div><strong>Client:</strong> <span>{client.user.get_full_name()}</span></div>
            <div><strong>Service:</strong> <span>{service.name}</span></div>
            <div><strong>Date:</strong> <span>{appointment_datetime.strftime('%A, %B %d, %Y')}</span></div>
            <div><strong>Time:</strong> <span>{appointment_datetime.strftime('%I:%M %p')}</span></div>
            <div><strong>Status:</strong> <span class="status-badge confirmed">Confirmed</span></div>
        </div>
    """
    return {'status': 'success', 'response_html': response_html, 'card_type': 'appointment-booking'}

def _add_client_card(practitioner, command):
    """Parses a command to add a new client, creates them, and returns a confirmation card."""
    details_str = command.lower().replace("add client", "").strip()
    if not details_str:
        return {'status': 'error', 'response_html': '<p>Please provide the client\'s details. Format: "add client [Full Name] email [email] phone [phone]".</p>', 'card_type': 'error-card'}

    email_match = re.search(r'email\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', details_str)
    phone_match = re.search(r'phone\s+([\d\s\-\(\)]+)', details_str)
    email = email_match.group(1) if email_match else None
    phone = phone_match.group(1).strip() if phone_match else None
    name_str = details_str
    if email_match: name_str = name_str.replace(email_match.group(0), "")
    if phone_match: name_str = name_str.replace(phone_match.group(0), "")
    full_name = name_str.strip()

    if not full_name:
        return {'status': 'error', 'response_html': '<p>A client name is required. Format: "add client [Full Name]".</p>', 'card_type': 'error-card'}
    if not email:
        return {'status': 'error', 'response_html': '<p>An email is required to create a client. Format: "add client [Full Name] email [email]".</p>', 'card_type': 'error-card'}
    if User.objects.filter(email=email).exists():
        return {'status': 'error', 'response_html': f'<p>A user with the email "{email}" already exists.</p>', 'card_type': 'error-card'}

    name_parts = full_name.split()
    first_name = name_parts[0]
    last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ''

    user = User.objects.create_user(
        username=email,
        email=email,
        first_name=first_name,
        last_name=last_name
    )
    new_client = Client.objects.create(user=user, phone_number=phone)
    new_client.practitioners.add(practitioner)

    # --- FIX ---
    # Generate the URL using reverse() before the f-string
    appointment_url = reverse('practitioners:create_appointment') + f'?client_id={new_client.id}'

    initials = f"{first_name[0] if first_name else ''}{last_name[0] if last_name else ''}".upper() or "CL"
    response_html = f"""
        <p>Success! The following client profile has been created:</p>
        <div class="client-item-card">
            <div class="client-avatar">{initials}</div>
            <div class="client-details">
                <div class="client-name">{new_client.user.get_full_name()}</div>
                <div class="client-email">{new_client.user.email or 'No email provided'}</div>
                <div class="client-phone">{new_client.phone_number or 'No phone provided'}</div>
            </div>
        </div>
        <div class="id-card-actions">
            <a href="{appointment_url}" class="btn-primary">Book Appointment</a>
        </div>
    """
    return {'status': 'success', 'response_html': response_html, 'card_type': 'client-creation-card'}


# =============================================================================
# AI INTELLIGENT COMMAND HANDLER (UPGRADED)
# =============================================================================

#<-- AI HELPER: INTELLIGENT COMMAND HANDLER -->

async def handle_intelligent_command(command, practitioner):
    """
    Uses fuzzy matching to determine the user's intent and calls the appropriate handler.
    This is more resilient to spelling and grammatical errors.
    """
    command_map = {
        'ADD_CLIENT': {
            'keywords': ['add client', 'new client', 'create client', 'register client'],
            'handler': _add_client_card, 'requires_arg': True,
        },
        'BOOK_APPOINTMENT': {
            'keywords': ['book appointment', 'schedule appointment', 'new appointment', 'set appointment'],
            'handler': _book_appointment_card, 'requires_arg': True,
        },
        'GET_CONTACT': {
            'keywords': ['contact', 'get contact', 'find contact', 'client details'],
            'handler': _get_contact_card, 'requires_arg': True,
        },
        'GET_TIME': {
            'keywords': ['what time is it', 'current time', 'get time', 'time now'],
            'handler': lambda p, cmd: _get_time_card(), 'requires_arg': False,
        },
        'GET_CLIENT_COUNT': {
            'keywords': ['how many clients', 'client count', 'total clients'],
            'handler': lambda p, cmd: _get_client_count_card(p), 'requires_arg': False,
        },
        'GET_TODAY_APPOINTMENTS': {
            'keywords': ['appointments today', 'my day', 'today schedule', "what's on today", "today's appointments"],
            'handler': lambda p, cmd: _get_appointments_today_card(p), 'requires_arg': False,
        },
        'GET_DASHBOARD_SUMMARY': {
            'keywords': ['dashboard summary', 'summary', 'performance', 'overview', 'revenue'],
            'handler': lambda p, cmd: _get_dashboard_summary_card(p), 'requires_arg': False,
        },
        'GET_WALLET_BALANCE': {
            'keywords': ['wallet balance', 'check balance', 'my wallet', 'balance'],
            'handler': lambda p, cmd: _get_wallet_balance_card(p), 'requires_arg': False,
        },
        'GET_CLIENT_LIST': {
            'keywords': ['show my clients', 'list clients', 'recent clients', 'show me my clients', 'show clients'],
            'handler': lambda p, cmd: _get_client_list_card(p), 'requires_arg': False,
        },
        'GET_PENDING_TASKS': {
            'keywords': ['pending tasks', 'my tasks', 'show tasks', 'to-do list', 'show me pending tasks'],
            'handler': lambda p, cmd: _get_pending_tasks_card(p), 'requires_arg': False,
        },
    }

    all_keywords = [keyword for details in command_map.values() for keyword in details['keywords']]
    best_match, score = fuzzy_process.extractOne(command, all_keywords, scorer=fuzz.WRatio)

    CONFIDENCE_THRESHOLD = 75
    if score < CONFIDENCE_THRESHOLD:
        # Check for simple redirects
        if 'notification' in command:
             return {'status': 'redirect', 'url': reverse('practitioners:notifications')}
        if 'subscription' in command or 'plan' in command:
            return {'status': 'redirect', 'url': reverse('practitioners:subscription_plans')}

        return {
            'status': 'error',
            'response_html': '<p>I\'m sorry, I don\'t understand that command. Please try rephrasing, or see the welcome card for available commands.</p>',
            'card_type': 'error-card'
        }

    matched_command_key = None
    for key, details in command_map.items():
        if best_match in details['keywords']:
            matched_command_key = key
            break

    if not matched_command_key:
        return {'status': 'error', 'response_html': '<p>An internal error occurred while understanding your command.</p>', 'card_type': 'error-card'}

    command_details = command_map[matched_command_key]
    handler_func = command_details['handler']

    # Use sync_to_async to run the synchronous DB queries in an async context
    if command_details['requires_arg']:
        result = await sync_to_async(handler_func)(practitioner, command)
    else:
        result = await sync_to_async(handler_func)(practitioner, command)

    return result


# =============================================================================
# CALENDAR INTEGRATION VIEWS
# =============================================================================

#<-- GOOGLE CALENDAR INITIALIZATION -->
class GoogleCalendarInitView(LoginRequiredMixin, View):
    """
    Initiates the OAuth 2.0 flow by redirecting the user to Google's consent screen.
    """
    def get(self, request, *args, **kwargs):
        flow = Flow.from_client_config(
            client_config={
                "web": {
                    "client_id": settings.GOOGLE_OAUTH2_CLIENT_ID,
                    "client_secret": settings.GOOGLE_OAUTH2_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [settings.GOOGLE_OAUTH2_REDIRECT_URI],
                }
            },
            scopes=['https://www.googleapis.com/auth/calendar'],
            redirect_uri=settings.GOOGLE_OAUTH2_REDIRECT_URI
        )
        authorization_url, state = flow.authorization_url(access_type='offline', prompt='consent')
        request.session['google_oauth_state'] = state
        return redirect(authorization_url)


#<-- GOOGLE CALENDAR REDIRECT HANDLER -->
class GoogleCalendarRedirectView(LoginRequiredMixin, View):
    """
    Handles the callback from Google after user consent, exchanging the auth
    code for credentials and saving them to the practitioner's profile.
    """
    def get(self, request, *args, **kwargs):
        # Rebuild the flow with the full client configuration
        flow = Flow.from_client_config(
            client_config={
                "web": {
                    "client_id": settings.GOOGLE_OAUTH2_CLIENT_ID,
                    "client_secret": settings.GOOGLE_OAUTH2_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [settings.GOOGLE_OAUTH2_REDIRECT_URI],
                }
            },
            scopes=['https://www.googleapis.com/auth/calendar'],
            state=request.session.get('google_oauth_state', ''),
            redirect_uri=settings.GOOGLE_OAUTH2_REDIRECT_URI
        )
        flow.fetch_token(authorization_response=request.build_absolute_uri())

        # Store credentials securely
        practitioner = request.user.practitioner_profile
        practitioner.google_credentials = flow.credentials.to_json()
        practitioner.is_google_calendar_synced = True
        practitioner.save()

        messages.success(request, "Successfully connected your Google Calendar!")
        return redirect(reverse('practitioners:settings') + '?tab=integrations')


#<-- MICROSOFT CALENDAR INITIALIZATION -->
class MicrosoftCalendarInitView(LoginRequiredMixin, View):
    """
    Initiates the OAuth 2.0 flow for Microsoft Calendar.
    """
    def get(self, request, *args, **kwargs):
        msal_app = msal.ConfidentialClientApplication(
            settings.MICROSOFT_GRAPH_CLIENT_ID,
            authority="https://login.microsoftonline.com/common",
            client_credential=settings.MICROSOFT_GRAPH_CLIENT_SECRET
        )
        flow = msal_app.initiate_auth_code_flow(
            scopes=settings.MICROSOFT_GRAPH_SCOPES,
            redirect_uri=settings.MICROSOFT_GRAPH_REDIRECT_URI
        )
        request.session['ms_auth_flow'] = flow
        return redirect(flow["auth_uri"])

#<-- MICROSOFT CALENDAR REDIRECT HANDLER -->
class MicrosoftCalendarRedirectView(LoginRequiredMixin, View):
    """
    Handles the callback from Microsoft after user consent.
    """
    def get(self, request, *args, **kwargs):
        auth_flow = request.session.pop('ms_auth_flow', {})

        # Rebuild the MSAL app with your app's credentials
        msal_app = msal.ConfidentialClientApplication(
            settings.MICROSOFT_GRAPH_CLIENT_ID,
            authority="https://login.microsoftonline.com/common",
            client_credential=settings.MICROSOFT_GRAPH_CLIENT_SECRET
        )

        result = msal_app.acquire_token_by_auth_code_flow(auth_flow, request.GET)

        if "error" in result:
            messages.error(request, f"Microsoft Login Failed: {result.get('error_description')}")
        else:
            practitioner = request.user.practitioner_profile
            practitioner.microsoft_credentials = result
            practitioner.is_microsoft_calendar_synced = True
            practitioner.save()
            messages.success(request, "Successfully connected your Microsoft Calendar!")

        return redirect(reverse('practitioners:settings') + '?tab=integrations')


# =============================================================================
# WEB SERVICES & DOMAIN REGISTRATION
# =============================================================================

#<-- WEB SERVICES & API VIEW -->
@login_required
def web_services(request, tab='booking-url'):
    """
    Main view for the Web Services section, handling tabs for Booking URL,
    Website Plugin, API Keys, Domains, and Email.
    """
    practitioner = get_object_or_404(Practitioner, user=request.user)

    if request.method == 'POST':
        # Handle various form submissions based on an 'action' field
        action = request.POST.get('action')
        if action == 'update_username':
            # Logic to update user's username (booking URL)
            pass
        elif action == 'generate_api_key':
            # Logic to create a new PractitionerAPIKey
            pass
        # ... other POST actions for domains, email, etc.
        return redirect('practitioners:web_services_tab', tab=request.POST.get('current_tab'))

    # Prepare context for GET request
    context = {
        'practitioner': practitioner, 'tab': tab,
        'api_keys': practitioner.api_keys.all(),
        'plugin_settings': WebsitePlugin.objects.filter(practitioner=practitioner).first(),
        'user_domains': Domain.objects.filter(practitioner=practitioner),
    }
    return render(request, 'frontend/template/webservices.html', context)

#<-- API DOCUMENTATION VIEW -->
@login_required
def api_documentation(request):
    """
    Renders the static API documentation page for developers.
    """
    api_key = PractitionerAPIKey.objects.filter(practitioner=request.user.practitioner_profile).first()
    context = {
        'example_api_key': api_key.key if api_key else 'YOUR_GENERATED_API_KEY'
    }
    return render(request, 'frontend/template/api_documentation.html', context)

#<-- OPENSRS API CLIENT (HELPER CLASS) -->
class OpenSRSClient:
    """
    A client to interact with the Tucows OpenSRS XML API for domain registration.
    (Contains methods for building, signing, and sending XML requests)
    """
    def __init__(self, use_test_mode=False):
        self.username = settings.OPENSRS_USERNAME
        self.private_key = settings.OPENSRS_PRIVATE_KEY
        self.api_url = settings.OPENSRS_API_TEST_URL if use_test_mode else settings.OPENSRS_API_URL

    # ... methods like _build_request_xml, _send_request, lookup_domain, etc.

#<-- SEARCH DOMAINS (API) -->
@login_required
def search_domains(request):
    """
    AJAX view to search for domain availability and price via the OpenSRS API.
    """
    domain_name = request.GET.get('domain', '').strip().lower()
    if not domain_name:
        return JsonResponse({'error': 'Domain name cannot be empty.'}, status=400)

    try:
        # This function encapsulates the logic to call the OpenSRSClient
        api_response = opensrs_search_domain(domain_name)
        return JsonResponse(api_response)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

#<-- REGISTER DOMAIN (API) -->
@login_required
@require_POST
def register_domain(request):
    """
    Handles the registration of a domain via AJAX. It validates practitioner
    details, checks wallet balance, and calls the OpenSRS API.
    """
    try:
        data = json.loads(request.body)
        domain_name = data.get('domain')
        practitioner = request.user.practitioner_profile

        # This function encapsulates the complex registration logic:
        # 1. Fetch Price & Check Wallet
        # 2. Get Billing Details & Build Contact Set
        # 3. Execute API Call
        # 4. Deduct from wallet and save Domain object
        opensrs_register_domain(domain_name, practitioner)

        messages.success(request, f"Domain {domain_name} registered successfully!")
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# =============================================================================
# WEBHOOK HANDLERS
# =============================================================================

@method_decorator(csrf_exempt, name='dispatch')
class PostmarkWebhookView(View):
    """
    Receives and logs email event webhooks from Postmark.
    """
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)

            # Extract relevant information from the Postmark payload
            message_id = data.get('MessageID')
            recipient = data.get('Recipient')
            event_type = data.get('RecordType')
            details = f"Email to {recipient} {event_type}."
            
            if event_type == 'Bounce':
                details = data.get('Description')

            # Create a log entry
            EmailLog.objects.create(
                raw_data=data,
                message_id=message_id,
                recipient=recipient,
                event_type=event_type,
                details=details
            )

            return JsonResponse({'status': 'success'}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            # In a production environment, you might want to log this error
            # to a file or a logging service for debugging.
            logger.error(f"Error in Postmark webhook: {e}")
            return JsonResponse({'error': 'An internal server error occurred'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class TelnyxWebhookView(View):
    """
    Receives and logs various event webhooks from Telnyx (SMS, Calls).
    """
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body).get('data', {})

            # Extract common information
            event_type = data.get('event_type')
            event_id = data.get('id')
            payload = data.get('payload', {})
            
            from_number = payload.get('from', {}).get('phone_number')
            to_number = payload.get('to', [{}])[0].get('phone_number')
            
            details = f"Event: {event_type}"

            # Customize details based on event type
            if event_type == 'message.received':
                details = f"SMS received from {from_number}: {payload.get('text')}"
            elif event_type == 'message.sent':
                 details = f"SMS sent to {to_number}."
            elif event_type == 'call.initiated':
                details = f"Call initiated from {from_number} to {to_number}. Direction: {payload.get('direction')}"
            elif event_type == 'call.answered':
                details = f"Call answered by {to_number}."
            elif event_type == 'call.hangup':
                details = f"Call hung up. Duration: {payload.get('hangup_duration_secs')} seconds."


            # Create a log entry
            TelnyxLog.objects.create(
                raw_data=data,
                event_id=event_id,
                event_type=event_type,
                phone_number_from=from_number,
                phone_number_to=to_number,
                details=details
            )

            return JsonResponse({'status': 'success'}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"Error in Telnyx webhook: {e}")
            return JsonResponse({'error': 'An internal server error occurred'}, status=500)

