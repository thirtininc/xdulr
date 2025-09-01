# practitioners/models.py
import secrets
from decimal import Decimal
from django.conf import settings
from django.db import models
from django.utils import timezone
from datetime import date, timedelta, time
import uuid
import json
import random
import string
from django.contrib.auth.hashers import make_password

# This custom field can remain as it's a utility used within this app.
class JSONField(models.TextField):
    """Custom JSON field to store JSON data in a TextField."""
    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return json.loads(value)

    def to_python(self, value):
        if isinstance(value, dict) or value is None:
            return value
        return json.loads(value)

    def get_prep_value(self, value):
        if value is None:
            return value
        return json.dumps(value)


def practitioner_profile_pic_path(instance, filename):
    """Generate file path for practitioner profile pictures."""
    return f'practitioners/{instance.id}/profile/{filename}'


def gallery_image_path(instance, filename):
    """Generate file path for gallery images."""
    return f'practitioners/{instance.practitioner.id}/gallery/{filename}'


class Practitioner(models.Model):
    """
    The central model for a practitioner, linking to all their settings and data.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='practitioner_profile'
    )
    wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    BUSINESS_TYPE_CHOICES = (
        ('healthcare', 'Healthcare'),
        ('education', 'Education'),
        ('beauty_and_aesthetics', 'Beauty and Aesthetics'),
        ('wellness', 'Wellness'),
        ('maintenance', 'Maintenance'),
        ('legal_practice', 'Legal Practice'),
        ('other', 'Other'),
    )
    
    profile_pic = models.ImageField(upload_to=practitioner_profile_pic_path, null=True, blank=True)
    professional_bio = models.TextField(blank=True, null=True)
    sms_2fa_enabled = models.BooleanField(default=False)
    totp_secret = models.CharField(max_length=255, blank=True, null=True)
    authenticator_2fa_enabled = models.BooleanField(default=False)
    business_name = models.CharField(max_length=255, blank=True, null=True)
    business_type = models.CharField(max_length=255, choices=BUSINESS_TYPE_CHOICES, blank=True, null=True)    
    business_phone = models.CharField(max_length=255, blank=True, null=True)
    business_address = models.TextField(blank=True, null=True)
    postal_code = models.CharField(blank=True, null=True, max_length=400)
    website_url = models.URLField(blank=True, null=True)
    specialization = models.CharField(max_length=255, blank=True, null=True, default="General Practitioner")
    last_seen = models.DateTimeField(null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_google_calendar_synced = models.BooleanField(default=False)
    google_credentials = models.JSONField(null=True, blank=True)
    is_microsoft_calendar_synced = models.BooleanField(default=False)
    microsoft_credentials = models.JSONField(null=True, blank=True)
    minimum_booking_lead_time = models.IntegerField(default=24, help_text="Minimum notice required for bookings, in hours.")
    cancellation_policy = models.TextField(blank=True, default="Cancellations must be made at least 24 hours in advance.")
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_account_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_onboarding_complete = models.BooleanField(default=False)
    
    ACCOUNT_TYPE_CHOICES = [('standard', 'Standard'), ('express', 'Express')]
    stripe_account_type = models.CharField(max_length=10, choices=ACCOUNT_TYPE_CHOICES, null=True, blank=True)

    subscription_plan = models.CharField(max_length=20, choices=[('pay_as_go', 'Pay As You Go'), ('growth_monthly', 'Growth Plan (Monthly)'), ('growth_yearly', 'Growth Plan (Yearly)'), ('scale_monthly', 'Scale Plan (Monthly)'), ('scale_yearly', 'Scale Plan (Yearly)')], default='pay_as_go')
    stripe_subscription_id = models.CharField(max_length=100, blank=True, null=True)
    subscription_status = models.CharField(max_length=20, choices=[('active', 'Active'), ('canceled', 'Canceled'), ('past_due', 'Past Due'), ('unpaid', 'Unpaid')], blank=True, null=True)
    subscription_current_period_end = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
  
    @property
    def is_online(self):
        if not self.last_seen:
            return False
        return timezone.now() < self.last_seen + timedelta(minutes=5)

    def __str__(self):
        if self.user:
            return self.user.get_full_name() or self.user.username
        return "Practitioner (no user)"

    def is_subscription_active(self):
        return self.subscription_status == 'active'

    @property
    def active_services_count(self):
        return self.services.filter(is_active=True).count()

    @property
    def total_services_count(self):
        return self.services.count()

    def has_services(self):
        return self.services.exists()


class ErrorLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    status_code = models.IntegerField()
    path = models.CharField(max_length=1024)
    traceback = models.TextField()

    def __str__(self):
        return f"Error {self.id} at {self.timestamp}"


class PhoneOTP(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.id:
            self.expires_at = timezone.now() + timedelta(minutes=5)
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expires_at

    @staticmethod
    def generate_otp(user):
        PhoneOTP.objects.filter(user=user).delete()
        otp_code = str(random.randint(100000, 999999))
        return PhoneOTP.objects.create(user=user, otp=otp_code)


class ClientSubscriptionPlan(models.Model):
    practitioner = models.ForeignKey(Practitioner, on_delete=models.CASCADE, related_name='client_subscription_plans')
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    features = models.TextField(help_text="List of features, one per line.")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - {self.practitioner.business_name}"


class ClientSubscription(models.Model):
    # CORRECTED: Pointing to the new Client model in the 'clients' app.
    client = models.ForeignKey('clients.Client', on_delete=models.CASCADE, related_name='client_subscriptions') 
    plan = models.ForeignKey(ClientSubscriptionPlan, on_delete=models.CASCADE)
    start_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.client.get_full_name()} subscribed to {self.plan.name}"


# =============================================================================
# NEW DYNAMIC PATH FUNCTIONS
# =============================================================================

def staff_profile_pic_path(instance, filename):
    """Generate file path for a staff member's profile picture."""
    # Saves to: media/practitioners/<practitioner_id>/staff_pics/<staff_id>/<filename>
    return f'practitioners/{instance.practitioner.id}/staff_pics/{instance.id}/{filename}'

def service_photo_path(instance, filename):
    """Generate file path for a service's photo."""
    # Saves to: media/practitioners/<practitioner_id>/service_photos/<service_id>/<filename>
    return f'practitioners/{instance.practitioner.id}/service_photos/{instance.id}/{filename}'

# =============================================================================
# UPDATED SERVICE and STAFF MODELS
# =============================================================================

class Service(models.Model):
    practitioner = models.ForeignKey(Practitioner, on_delete=models.CASCADE, related_name='services')
    name = models.CharField(max_length=100)
    duration = models.IntegerField(help_text="Duration in minutes")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    color = models.CharField(max_length=20, default="primary")
    description = models.TextField(blank=True, null=True)
    is_virtual = models.BooleanField(default=False)
    is_in_person = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    photo = models.ImageField(upload_to=service_photo_path, null=True, blank=True)

    @property
    def photo_url(self):
        """Returns the URL of the photo, or None if it doesn't exist."""
        if self.photo and hasattr(self.photo, 'url'):
            return self.photo.url
        return None

    def __str__(self):
        return f"{self.name} ({self.duration} mins) - ${self.price}"


class Staff(models.Model):

    PAY_TYPE_CHOICES = (
        ('HOURLY', 'Hourly'),
        ('SALARY', 'Annual Salary'),
    )

    practitioner = models.ForeignKey(Practitioner, on_delete=models.CASCADE, related_name='staff_members')
    services = models.ManyToManyField(Service, related_name='staff_members', blank=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='staff_data_record',
        null=True, 
        blank=True
    )
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    specialization = models.CharField(max_length=255, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)

    profile_picture = models.ImageField(upload_to=staff_profile_pic_path, blank=True, null=True)
    pay_type = models.CharField(max_length=10, choices=PAY_TYPE_CHOICES, null=True, blank=True)
    pay_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Enter the hourly rate or annual salary.")

    income_tax_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00,
        help_text="Enter the total income tax percentage to deduct (e.g., 20.5 for 20.5%)."
    )
    cpp_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=5.95,
        help_text="Canada Pension Plan contribution rate (%)."
    )
    ei_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=1.63,
        help_text="Employment Insurance premium rate (%)."
    )
    benefits_deduction = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00,
        help_text="Enter a fixed deduction amount for recurring benefits per pay period."
    )
    other_deductions = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00,
        help_text="Enter any other one-time or miscellaneous fixed deductions for this pay period."
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def profile_pic_url(self):
        """Returns the URL of the profile picture, or None if it doesn't exist."""
        if self.profile_picture and hasattr(self.profile_picture, 'url'):
            return self.profile_picture.url
        return None

    def __str__(self):
        return f"{self.name} - {self.practitioner.business_name}"

class PayStub(models.Model):
    """
    Represents a single pay record or pay stub for a staff member.
    """

    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='pay_stubs')
    pay_period_start = models.DateField()
    pay_period_end = models.DateField()
    
    # Financial Details
    gross_pay = models.DecimalField(max_digits=10, decimal_places=2)
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    net_pay = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Additional Information
    hours_worked = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-pay_period_end'] # Show the most recent pay stubs first

    def __str__(self):
        return f"Pay Stub for {self.staff.name} ({self.pay_period_start} to {self.pay_period_end})"


class StaffAvailability(models.Model):
    DAY_CHOICES = ((0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'), (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday'))
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='availabilities')
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.staff.name} - {self.get_day_of_week_display()}: {self.start_time} - {self.end_time}"
    
    class Meta:
        verbose_name_plural = "Staff Availabilities"


class ImagesGallery(models.Model):
    practitioner = models.ForeignKey(Practitioner, on_delete=models.CASCADE, related_name='gallery_images')
    image_field = models.ImageField(upload_to=gallery_image_path, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.image_field.name or f"Image for {self.practitioner.business_name}"


class NotificationSettings(models.Model):
    practitioner = models.OneToOneField(Practitioner, on_delete=models.CASCADE, related_name="notification_settings")
    changes_made = models.BooleanField(default=True, verbose_name="Changes made to your account")
    new_bookings = models.BooleanField(default=True, verbose_name="New appointment bookings")
    booking_reminders = models.BooleanField(default=True, verbose_name="Appointment reminders")
    platform_updates = models.BooleanField(default=True, verbose_name="Product updates from our platform")
    marketing_offers = models.BooleanField(default=False, verbose_name="Marketing and promotional offers")

    def __str__(self):
        return f"Notification Settings for {self.practitioner.user.username}"


class PractitionerAPIKey(models.Model):
    practitioner = models.ForeignKey(Practitioner, on_delete=models.CASCADE, related_name="api_keys")
    key = models.CharField(max_length=64, unique=True, editable=False)
    name = models.CharField(max_length=100, help_text="A name for you to identify this key")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"API Key for {self.practitioner.user.username} ({self.name})"


class PractitionerWallet(models.Model):
    practitioner = models.OneToOneField(Practitioner, on_delete=models.CASCADE, related_name="wallet")
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    auto_recharge_enabled = models.BooleanField(default=False)
    recharge_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('10.00'))
    recharge_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('20.00'))
    stripe_payment_method_id = models.CharField(max_length=255, blank=True, null=True)
    card_last4 = models.CharField(max_length=4, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.practitioner.user.username}'s Wallet: ${self.balance}"


class WalletTransaction(models.Model):
    TRANSACTION_TYPES = (('deposit', 'Deposit'), ('charge', 'Charge'), ('subscription', 'Subscription Fee'), ('refund', 'Refund'))
    wallet = models.ForeignKey(PractitionerWallet, on_delete=models.CASCADE, related_name="transactions")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    description = models.CharField(max_length=255)
    stripe_charge_id = models.CharField(max_length=255, blank=True, null=True)
    related_appointment_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_transaction_type_display()} of ${self.amount} for {self.wallet.practitioner.user.username}"


class Subscription(models.Model):
    SUBSCRIPTION_TYPES = (('ai_website', 'AI Generated Website'), ('white_label', 'White Label'), ('storage', '1TB Storage'))
    practitioner = models.ForeignKey(Practitioner, on_delete=models.CASCADE, related_name="subscriptions")
    subscription_type = models.CharField(max_length=20, choices=SUBSCRIPTION_TYPES)
    stripe_subscription_id = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.practitioner.user.username} - {self.get_subscription_type_display()}"


class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    appointment_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.90)
    features = models.TextField()
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name


class PractitionerSubscription(models.Model):
    practitioner = models.OneToOneField(Practitioner, on_delete=models.CASCADE, related_name='practitioner_subscription')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    payment_info = JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.practitioner.business_name} - {self.plan.name}"


class Availability(models.Model):
    DAY_CHOICES = ((0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'), (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday'))
    practitioner = models.ForeignKey(Practitioner, on_delete=models.CASCADE, related_name='practitioner_availabilities')
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.get_day_of_week_display()}: {self.start_time} - {self.end_time}"
    
    class Meta:
        verbose_name_plural = "Availabilities"


class SpecialAvailability(models.Model):
    practitioner = models.ForeignKey(Practitioner, on_delete=models.CASCADE, related_name='special_availabilities')
    date = models.DateField()
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    is_available = models.BooleanField(default=False)
    title = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        status = "Available" if self.is_available else "Unavailable"
        return f"{self.date} - {status}: {self.title}"
    
    class Meta:
        verbose_name_plural = "Special Availabilities"


class WebsitePlugin(models.Model):
    practitioner = models.OneToOneField(Practitioner, on_delete=models.CASCADE, related_name='website_plugin')
    widget_id = models.CharField(max_length=50, unique=True)
    primary_color = models.CharField(max_length=20, default="#4361ee")
    font_family = models.CharField(max_length=50, default="System Default")
    button_text = models.CharField(max_length=50, default="Book an Appointment")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Website Plugin for {self.practitioner.business_name}"


class Integration(models.Model):
    TYPE_CHOICES = (('calendar', 'Calendar'), ('payment', 'Payment'), ('video', 'Video Conferencing'), ('email', 'Email Marketing'))
    STATUS_CHOICES = (('active', 'Active'), ('inactive', 'Inactive'), ('error', 'Error'))
    practitioner = models.ForeignKey(Practitioner, on_delete=models.CASCADE, related_name='integrations')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    provider = models.CharField(max_length=50)
    credentials = JSONField(blank=True, null=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='inactive')
    last_synced = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.get_type_display()} integration with {self.provider} for {self.practitioner.business_name}"


class BillingDetails(models.Model):
    practitioner = models.OneToOneField(Practitioner, on_delete=models.CASCADE, related_name='billing_details')
    payment_method_id = models.CharField(max_length=100, blank=True, null=True)
    last4 = models.CharField(max_length=4, blank=True, null=True)
    is_paid_plan = models.BooleanField(default=False)
    last_billing_date = models.DateField(null=True, blank=True)
    full_name = models.CharField(max_length=100)
    email_address = models.EmailField()
    phone_number = models.CharField(max_length=20)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, default="CA")
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default="United States")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Billing info for {self.practitioner.business_name}"
    
    class Meta:
        verbose_name_plural = "Billing Details"


class PaymentHistory(models.Model):
    STATUS_CHOICES = (('paid', 'Paid'), ('pending', 'Pending'), ('failed', 'Failed'), ('refunded', 'Refunded'))
    practitioner = models.ForeignKey(Practitioner, on_delete=models.CASCADE, related_name='payment_history')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='paid')
    date = models.DateTimeField(auto_now_add=True)
    invoice_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    payment_type = models.CharField(max_length=20, choices=[('pay_as_go', 'Pay As You Go'), ('subscription', 'Monthly Subscription')], default='pay_as_go')
    
    def __str__(self):
        return f"Payment of ${self.amount} - {self.invoice_name}"
    
    class Meta:
        verbose_name_plural = "Payment Histories"
        ordering = ['-date']


class Conversation(models.Model):
    practitioner = models.ForeignKey(Practitioner, on_delete=models.CASCADE, related_name='conversations')
    # Pointing to the Client model in the 'clients' app.
    client = models.ForeignKey('clients.Client', on_delete=models.CASCADE, related_name='client_conversations')
    practitioner_phone_number = models.CharField(max_length=20, null=True, blank=True)
    last_message_at = models.DateTimeField(auto_now=True)

    class Meta:
        # This constraint prevents the creation of duplicate conversations
        # for the same practitioner and client pair.
        unique_together = ('practitioner', 'client')
        # Default ordering to show the most recently active conversations first.
        ordering = ['-last_message_at']

    def __str__(self):
        client_name = "N/A"
        practitioner_name = "N/A"

        if self.client and hasattr(self.client, 'get_full_name'):
            client_name = self.client.get_full_name()
        
        if self.practitioner and hasattr(self.practitioner.user, 'get_full_name'):
            practitioner_name = self.practitioner.user.get_full_name()
            
        return f"Conversation between {practitioner_name} and {client_name}"


def message_attachment_path(instance, filename):
    """
    Generate a unique file path for message attachments to avoid name collisions.
    Saves to: media/practitioners/<practitioner_id>/attachments/<unique_id>/<filename>
    """
    return f'practitioners/{instance.conversation.practitioner.id}/attachments/{uuid.uuid4()}/{filename}'


class Message(models.Model):
    SENDER_CHOICES = (('practitioner', 'Practitioner'), ('client', 'Client'))
    SEND_TYPE_CHOICES = (('secure', 'Secure Message'), ('sms', 'SMS'))
    
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages', null=True)
    sender_type = models.CharField(max_length=12, choices=SENDER_CHOICES, default='practitioner')
    content = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now)
    telnyx_message_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
    send_type = models.CharField(max_length=10, choices=SEND_TYPE_CHOICES, default='secure')
    
    attachment = models.FileField(upload_to=message_attachment_path, blank=True, null=True)
    
    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"Message from {self.get_sender_type_display()} at {self.timestamp}"


class AIAgent(models.Model):
    practitioner = models.OneToOneField(Practitioner, on_delete=models.CASCADE, related_name='ai_agent')
    is_active = models.BooleanField(default=True)
    voice = models.CharField(max_length=50, default="female")
    personality_prompt = models.TextField(default="You are a friendly and helpful receptionist.")
    
    def __str__(self):
        return f"AI Agent for {self.practitioner.user.get_full_name()}"


class KnowledgeBaseDocument(models.Model):
    practitioner = models.ForeignKey(Practitioner, on_delete=models.CASCADE, related_name='knowledge_base_documents')
    file = models.FileField(upload_to='knowledge_base/')
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=10)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file_name


class CallLog(models.Model):
    STATUS_CHOICES = (('completed', 'Completed'), ('failed', 'Failed'), ('in-progress', 'In Progress'))
    practitioner = models.ForeignKey(Practitioner, on_delete=models.CASCADE, related_name='call_logs')
    phone_number = models.CharField(max_length=20)
    duration = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    transcript = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"Call with {self.phone_number} at {self.timestamp}"


class TelnyxPhoneNumber(models.Model):
    practitioner = models.ForeignKey(Practitioner, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20, unique=True)
    telnyx_phone_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    monthly_cost = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    setup_cost = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.phone_number} ({self.practitioner.business_name})"

    
class Appointment(models.Model):
    practitioner = models.ForeignKey(Practitioner, on_delete=models.CASCADE, related_name='practitioner_appointments')
    # CORRECTED: Pointing to the new Client model in the 'clients' app.
    client = models.ForeignKey('clients.Client', on_delete=models.CASCADE, related_name='client_appointments')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='appointment_services')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=50, default='upcoming')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    location = models.CharField(max_length=255, default="Office")
    is_virtual = models.BooleanField(default=False)
    meeting_link = models.URLField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    staff = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, blank=True, related_name='staff_appointments')

    class Meta:
        ordering = ['date', 'start_time']

    def __str__(self):
        return f"Appointment for {self.client.get_full_name()} on {self.date} at {self.start_time}"


class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = (('credit_card', 'Credit Card'), ('cash', 'Cash'), ('bank_transfer', 'Bank Transfer'))
    STATUS_CHOICES = (('pending', 'Pending'), ('completed', 'Completed'), ('failed', 'Failed'), ('refunded', 'Refunded'))
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='appointment_payment')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    payment_date = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment of ${self.amount} for {self.appointment} - {self.get_status_display()}"


class Notification(models.Model):
    TYPE_CHOICES = (('appointment', 'Appointment'), ('message', 'Message'), ('payment', 'Payment'), ('system', 'System'))
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_notifications_practitioners')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=255)
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.type} notification for {self.user.username}: {self.title}"


class Task(models.Model):
    practitioner = models.ForeignKey(Practitioner, on_delete=models.CASCADE, related_name='practitioner_tasks')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    due_date = models.DateField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['due_date', 'created_at']

    def __str__(self):
        return self.title


class Domain(models.Model):
    STATUS_CHOICES = (('active', 'Active'), ('expired', 'Expired'), ('pending', 'Pending Transfer'))
    practitioner = models.ForeignKey(Practitioner, on_delete=models.CASCADE, related_name='domains')
    name = models.CharField(max_length=255, unique=True)
    registrar = models.CharField(max_length=100, default='OpenSRS')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    registered_date = models.DateField()
    expiry_date = models.DateField()
    opensrs_order_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class EmailAccount(models.Model):
    practitioner = models.ForeignKey(Practitioner, on_delete=models.CASCADE, related_name='email_accounts')
    domain = models.ForeignKey(Domain, on_delete=models.CASCADE, related_name='email_accounts')
    email_address = models.EmailField(unique=True)
    password_placeholder = models.CharField(max_length=255, default="Managed by OpenSRS")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email_address


class RecoveryCode(models.Model):
    practitioner = models.ForeignKey(Practitioner, on_delete=models.CASCADE, related_name='recovery_codes')
    code = models.CharField(max_length=128, help_text="The hashed recovery code.")
    used = models.BooleanField(default=False)

    def __str__(self):
        return f"Recovery Code for {self.practitioner.user.username} (Used: {self.used})"


class Form(models.Model):
    practitioner = models.ForeignKey(Practitioner, on_delete=models.CASCADE, related_name='forms')
    title = models.CharField(max_length=255)
    header_text = models.TextField(blank=True, null=True)
    consent_text = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Question(models.Model):
    QUESTION_TYPES = (('text', 'Text (Single Line)'), ('textarea', 'Textarea (Multi-line)'), ('email', 'Email'), ('date', 'Date'), ('checkbox', 'Checkbox'))
    form = models.ForeignKey(Form, on_delete=models.CASCADE, related_name='questions')
    text = models.CharField(max_length=500)
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    is_required = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.text


class FormSubmission(models.Model):
    form = models.ForeignKey(Form, on_delete=models.CASCADE, related_name='submissions')
    # CORRECTED: Pointing to the new Client model in the 'clients' app.
    client = models.ForeignKey('clients.Client', on_delete=models.CASCADE, related_name='form_submissions')
    appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    answers = models.JSONField()
    consent_given = models.BooleanField(default=False)

    def __str__(self):
        return f"Submission for {self.form.title} by {self.client.get_full_name()}"

class VideoCall(models.Model):
    """Represents a video call session between a practitioner and a client."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='video_calls')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    room_name = models.CharField(max_length=255, unique=True, help_text="The unique name for the signaling room.")
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Video Call for Conversation {self.conversation.id}"


# =============================================================================
# NEW CONSENT SYSTEM MODELS
# =============================================================================

class PractitionerDataRequest(models.Model):
    """
    Defines the set of data fields a practitioner requests from their clients
    and the consent text they present. Each practitioner has one.
    """
    practitioner = models.OneToOneField(
        Practitioner, 
        on_delete=models.CASCADE, 
        related_name='data_request_settings'
    )
    requested_fields = models.JSONField(
        default=list,
        help_text="List of client model field names the practitioner requests access to."
    )
    consent_form_text = models.TextField(
        blank=True,
        help_text="The default text shown to clients when requesting data access."
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Data Request Settings for {self.practitioner.business_name}"


class ClientConsent(models.Model):
    """
    Records the specific, field-level consent a Client has given to a
    Practitioner. This is the source of truth for data access.
    """
    client = models.ForeignKey(
        'clients.Client',
        on_delete=models.CASCADE, 
        related_name='consent_records'
    )
    practitioner = models.ForeignKey(
        Practitioner, 
        on_delete=models.CASCADE, 
        related_name='client_consents'
    )
    authorized_fields = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    consent_given_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('client', 'practitioner')

    def __str__(self):
        status = "Active" if self.is_active else "Revoked"
        return f"Consent from {self.client.get_full_name()} to {self.practitioner.business_name} ({status})"


class EmailLog(models.Model):
    """
    Logs incoming email events from Postmark webhooks.
    """
    received_at = models.DateTimeField(default=timezone.now)
    raw_data = models.JSONField()
    message_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    recipient = models.EmailField(blank=True, null=True)
    event_type = models.CharField(max_length=50, blank=True, null=True, db_index=True) # e.g., 'Delivery', 'Bounce', 'Open'
    details = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.event_type} for {self.recipient} at {self.received_at.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        ordering = ['-received_at']
        verbose_name = "Email Log"
        verbose_name_plural = "Email Logs"


class TelnyxLog(models.Model):
    """
    Logs incoming events from Telnyx webhooks (SMS, Calls, etc.).
    """
    received_at = models.DateTimeField(default=timezone.now)
    raw_data = models.JSONField()
    event_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    event_type = models.CharField(max_length=100, blank=True, null=True, db_index=True) # e.g., 'message.received', 'call.initiated'
    phone_number_from = models.CharField(max_length=50, blank=True, null=True)
    phone_number_to = models.CharField(max_length=50, blank=True, null=True)
    details = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.event_type} from {self.phone_number_from} to {self.phone_number_to}"

    class Meta:
        ordering = ['-received_at']
        verbose_name = "Telnyx Log"
        verbose_name_plural = "Telnyx Logs"
