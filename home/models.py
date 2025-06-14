from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import uuid
import json
from datetime import timedelta
import random

# Custom User Model
class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('practitioner', 'Practitioner'),
        ('client', 'Client'),
    )
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='client')
    phone = models.CharField(max_length=20, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    
    groups = models.ManyToManyField(
        'auth.Group', verbose_name=_('groups'), blank=True,
        help_text=_('The groups this user belongs to.'),
        related_name="customuser_groups", related_query_name="user"
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission', verbose_name=_('user permissions'), blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name="customuser_permissions", related_query_name="user"
    )

# Practitioner Model
class Practitioner(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='practitioner_profile')
    business_name = models.CharField(max_length=255)
    business_phone = models.CharField(max_length=20, blank=True, null=True)
    business_address = models.TextField(blank=True, null=True)
    website_url = models.URLField(blank=True, null=True)
    professional_bio = models.TextField(blank=True, null=True)
    
    # Stripe Fields
    stripe_account_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_onboarded = models.BooleanField(default=False)
    
    # Subscription Fields
    subscription_plan = models.CharField(max_length=20, default='pay_as_go')
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True)
    subscription_status = models.CharField(max_length=20, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username

# Client Model
class Client(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='client_profile')
    practitioners = models.ManyToManyField(Practitioner, related_name='clients')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username

# Appointment Type Model
class AppointmentType(models.Model):
    practitioner = models.ForeignKey(Practitioner, on_delete=models.CASCADE, related_name='appointment_types')
    name = models.CharField(max_length=100)
    duration = models.IntegerField(help_text="Duration in minutes")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    color = models.CharField(max_length=20, default="primary")
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

# Staff Model
class Staff(models.Model):
    practitioner = models.ForeignKey(Practitioner, on_delete=models.CASCADE, related_name='staff_members')
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    appointment_types = models.ManyToManyField(AppointmentType, related_name='staff_members', blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

# Staff Availability Model
class StaffAvailability(models.Model):
    DAY_CHOICES = [(i, timezone.datetime(2024, 1, 1 + i).strftime('%A')) for i in range(7)]
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='availabilities')
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)

# Appointment Model
class Appointment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'), ('confirmed', 'Confirmed'), ('cancelled', 'Cancelled'),
        ('completed', 'Completed'), ('no_show', 'No Show'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    practitioner = models.ForeignKey(Practitioner, on_delete=models.CASCADE, related_name='appointments')
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='appointments')
    appointment_type = models.ForeignKey(AppointmentType, on_delete=models.SET_NULL, null=True, blank=True)
    staff = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True, null=True)
    is_virtual = models.BooleanField(default=False)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

# Payment Model
class Payment(models.Model):
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='completed')
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    payment_date = models.DateTimeField(default=timezone.now)

# Notification Model
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
