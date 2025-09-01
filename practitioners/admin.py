# practitioners/admin.py

from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Practitioner, Appointment, Payment, Message, Notification, Task,
    Service, Staff, StaffAvailability, ClientSubscriptionPlan,
    PractitionerWallet, WalletTransaction, Subscription, SubscriptionPlan,
    PractitionerSubscription, Availability, SpecialAvailability,
    WebsitePlugin, Integration, BillingDetails, PaymentHistory,
    Conversation, AIAgent, KnowledgeBaseDocument, CallLog, TelnyxPhoneNumber
)

# --- Custom Admin Classes with Decorators ---

class StaffAvailabilityInline(admin.TabularInline):
    model = StaffAvailability
    extra = 0
    fields = ('day_of_week', 'start_time', 'end_time', 'is_available')

@admin.register(Practitioner)
class PractitionerAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'business_name', 'stripe_customer_id', "stripe_account_id", "stripe_onboarding_complete", 'get_email', 'created_at')
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'business_name')
    list_filter = ('created_at', 'stripe_onboarding_complete')

    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Name'
    
    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'

@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ('name', 'practitioner', 'specialization', 'email', 'phone', 'is_active', 'created_at')
    list_filter = ('is_active', 'practitioner', 'specialization', 'created_at')
    search_fields = ('name', 'email', 'phone', 'practitioner__business_name', 'specialization')
    list_editable = ('is_active',)
    filter_horizontal = ('services',)
    ordering = ('practitioner', 'name')
    inlines = [StaffAvailabilityInline]
    
    fieldsets = (
        ('Basic Information', {'fields': ('practitioner', 'name', 'email', 'phone')}),
        ('Professional Details', {'fields': ('specialization', 'bio', 'profile_picture')}),
        ('Services', {'fields': ('services',)}),
        ('Account', {'fields': ('user', 'is_active')}),
    )

@admin.register(StaffAvailability)
class StaffAvailabilityAdmin(admin.ModelAdmin):
    list_display = ('staff', 'get_practitioner', 'day_of_week', 'start_time', 'end_time', 'is_available')
    list_filter = ('day_of_week', 'is_available', 'staff__practitioner')
    search_fields = ('staff__name', 'staff__practitioner__business_name')
    list_editable = ('is_available',)
    ordering = ('staff', 'day_of_week', 'start_time')
    
    def get_practitioner(self, obj):
        return obj.staff.practitioner.business_name
    get_practitioner.short_description = 'Practitioner'
    get_practitioner.admin_order_field = 'staff__practitioner__business_name'

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'practitioner', 'duration', 'price', 'color_sample', 'is_active')
    list_filter = ('is_active', 'is_virtual', 'is_in_person', 'practitioner')
    search_fields = ('name', 'practitioner__business_name', 'practitioner__user__first_name')
    
    def color_sample(self, obj):
        return format_html('<div style="background-color:{}; width:30px; height:15px;"></div>', obj.color)
    color_sample.short_description = 'Color'

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'appointment_fee', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)

@admin.register(PractitionerSubscription)
class PractitionerSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('practitioner', 'plan', 'start_date', 'end_date', 'is_active')
    list_filter = ('plan', 'is_active', 'start_date')
    search_fields = ('practitioner__user__first_name', 'practitioner__user__last_name', 'practitioner__business_name')
    date_hierarchy = 'start_date'

@admin.register(Availability)
class AvailabilityAdmin(admin.ModelAdmin):
    list_display = ('practitioner', 'day_of_week', 'start_time', 'end_time', 'is_available')
    list_filter = ('day_of_week', 'is_available', 'practitioner')
    search_fields = ('practitioner__business_name', 'practitioner__user__first_name')

@admin.register(SpecialAvailability)
class SpecialAvailabilityAdmin(admin.ModelAdmin):
    list_display = ('practitioner', 'date', 'title', 'is_available')
    list_filter = ('is_available', 'date', 'practitioner')
    search_fields = ('practitioner__business_name', 'title')
    date_hierarchy = 'date'

@admin.register(WebsitePlugin)
class WebsitePluginAdmin(admin.ModelAdmin):
    list_display = ('practitioner', 'widget_id', 'button_text', 'color_sample')
    search_fields = ('practitioner__business_name', 'widget_id')
    
    def color_sample(self, obj):
        return format_html('<div style="background-color:{}; width:30px; height:15px;"></div>', obj.primary_color)
    color_sample.short_description = 'Color'

@admin.register(Integration)
class IntegrationAdmin(admin.ModelAdmin):
    list_display = ('practitioner', 'type', 'provider', 'status', 'last_synced')
    list_filter = ('type', 'provider', 'status', 'practitioner')
    search_fields = ('practitioner__business_name', 'provider')
    date_hierarchy = 'created_at'

@admin.register(BillingDetails)
class BillingDetailsAdmin(admin.ModelAdmin):
    list_display = ('practitioner', 'is_paid_plan',)
    search_fields = ('practitioner__business_name',)
    date_hierarchy = 'created_at'

@admin.register(PaymentHistory)
class PaymentHistoryAdmin(admin.ModelAdmin):
    list_display = ('practitioner', 'amount', 'status', 'date')
    list_filter = ('status', 'practitioner')
    search_fields = ('practitioner__business_name', 'invoice_name')
    date_hierarchy = 'date'


# --- Simple Registrations for Models Without Custom Admin Classes ---

admin.site.register(ClientSubscriptionPlan)
admin.site.register(PractitionerWallet)
admin.site.register(WalletTransaction)
admin.site.register(Subscription)
admin.site.register(Conversation)
admin.site.register(AIAgent)
admin.site.register(KnowledgeBaseDocument)
admin.site.register(CallLog)
admin.site.register(TelnyxPhoneNumber)
#admin.site.register(Client)
admin.site.register(Appointment)
admin.site.register(Payment)
admin.site.register(Message)
admin.site.register(Notification)
admin.site.register(Task)