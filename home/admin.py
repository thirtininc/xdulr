from django.contrib import admin
from .models import (
    User, Practitioner, Client, Appointment, AppointmentType, 
    Staff, StaffAvailability, Payment, Notification
)

# Register your models here to make them accessible in the Django admin interface.
# This helps in managing the data directly from a web interface.

class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type', 'is_staff')
    list_filter = ('user_type', 'is_staff', 'is_superuser')
    search_fields = ('username', 'first_name', 'last_name', 'email')

class PractitionerAdmin(admin.ModelAdmin):
    list_display = ('user', 'business_name', 'stripe_account_id', 'stripe_onboarded')
    search_fields = ('user__username', 'business_name')

class ClientAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at')
    search_fields = ('user__username',)

class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'practitioner', 'client', 'date', 'start_time', 'status')
    list_filter = ('status', 'date', 'practitioner')
    search_fields = ('client__user__username', 'practitioner__user__username')
    date_hierarchy = 'date'

class StaffAdmin(admin.ModelAdmin):
    list_display = ('name', 'practitioner', 'email', 'is_active')
    list_filter = ('practitioner', 'is_active')

admin.site.register(User, UserAdmin)
admin.site.register(Practitioner, PractitionerAdmin)
admin.site.register(Client, ClientAdmin)
admin.site.register(Appointment, AppointmentAdmin)
admin.site.register(AppointmentType)
admin.site.register(Staff, StaffAdmin)
admin.site.register(StaffAvailability)
admin.site.register(Payment)
admin.site.register(Notification)
