# practitioners/urls.py
from django.urls import path
from . import views
from home.views import *

app_name = 'practitioners'

urlpatterns = [
    # =============================================================================
    # CORE PRACTITIONER DASHBOARD & VIEWS
    # =============================================================================
    path('dashboard/', views.Dashboard, name='dashboard'),
    path('settings/', views.Settings.as_view(), name='settings'),
    path('notifications/', views.Notifications.as_view(), name='notifications'),
    path('reports/', views.Reports.as_view(), name='reports'),
    path('api/notifications/mark-as-read/', views.MarkNotificationsAsReadView.as_view(), name='mark_notifications_as_read'),

    # =============================================================================
    # TWO-FACTOR AUTHENTICATION SETUP (MOVED FROM HOME APP)
    # =============================================================================
    path('settings/2fa/authenticator/setup/', views.setup_authenticator_view, name='setup_authenticator'),
    path('settings/2fa/authenticator/verify/', views.verify_authenticator_view, name='verify_authenticator'),
    path('settings/2fa/authenticator/disable/', views.disable_authenticator_view, name='disable_authenticator'),
    path('settings/2fa/recovery-codes/', views.ShowRecoveryCodesView.as_view(), name='show_recovery_codes'),
    path('settings/2fa/regenerate-codes/', views.regenerate_recovery_codes_view, name='regenerate_recovery_codes'),


    # =============================================================================
    # CLIENT MANAGEMENT (from Practitioner's perspective)
    # =============================================================================
    path('clients/', views.Clients.as_view(), name='clients'),
    path('clients/create/', views.CreateClient.as_view(), name='create_client'),
    path('clients/<int:client_id>/', views.ClientDetail.as_view(), name='client_detail'),
    path('p/<str:username>/', views.UserPublicPageView.as_view(), name='public_booking_page'),
    path('clients/<int:client_id>/send-consent-request/', views.SendConsentRequestView.as_view(), name='send_consent_request'),
    path('clients/<int:client_id>/remove/', views.remove_client_connection, name='remove_client_connection'),
    path('api/client-search/', views.client_search_api, name='client_search_api'),
    path('api/connect-client/', views.connect_client_api, name='connect_client_api'),
    path('api/send-connection-otp/', views.send_connection_otp, name='send_connection_otp'),

   
    # =============================================================================
    # APPOINTMENTS, SERVICES & STAFF
    # =============================================================================
    path('appointments/', views.Appointments.as_view(), name='appointments'),
    path('appointments/create/', views.CreateAppointment.as_view(), name='create_appointment'),
    path('appointments/<int:appointment_id>/', views.AppointmentDetail.as_view(), name='appointment_detail'),
    path('appointments/<int:appointment_id>/edit/', views.EditAppointment.as_view(), name='edit_appointment'),
    path('appointments/<int:appointment_id>/confirm/', views.confirm_appointment, name='confirm_appointment'),
    path('appointments/<int:appointment_id>/complete/', views.complete_appointment, name='complete_appointment'),
    path('appointments/<int:appointment_id>/cancel/', views.cancel_appointment, name='cancel_appointment'),
    path('calendar/', views.Calendar.as_view(), name='calendar'),
    path('web-services/', views.web_services, name='web_services'),
    path('web-services/<str:tab>/', views.web_services, name='web_services_tab'), 
    path('api/appointment-client-search/', views.appointment_client_search_api, name='appointment_client_search_api'),
    path('api/appointments/<int:appointment_id>/update-time/', views.update_appointment_time_api, name='update_appointment_time_api'),

    # Staff and Services Management
    path('staff-services/', views.StaffAndServicesView.as_view(), name='staff_and_services'),
    path('api/staff/add/', views.add_or_edit_staff, name='api_add_staff'),
    path('api/staff/edit/<int:staff_id>/', views.add_or_edit_staff, name='api_edit_staff'),
    path('api/staff/delete/<int:staff_id>/', views.delete_staff_api, name='api_delete_staff'),
    path('api/staff/<int:staff_id>/paystub/create/', views.create_pay_stub_api, name='api_create_pay_stub'), 
    path('api/staff/<int:staff_id>/paystub/create/', views.create_pay_stub_api, name='api_create_pay_stub'),
    path('api/staff/<int:staff_id>/calculate-gross-pay/', views.calculate_gross_pay_api, name='api_calculate_gross_pay'), 
    path('api/paystub/<int:stub_id>/update/', views.update_pay_stub_api, name='api_update_pay_stub'), 
    path('api/paystub/<int:stub_id>/delete/', views.delete_pay_stub_api, name='api_delete_pay_stub'), 

    path('api/service/add/', views.add_or_edit_service, name='api_add_service'),
    path('api/service/edit/<int:service_id>/', views.add_or_edit_service, name='api_edit_service'),
    path('api/service/delete/<int:service_id>/', views.delete_service_api, name='api_delete_service'),


    # =============================================================================
    # CALENDAR INTEGRATIONS (FIX)
    # =============================================================================
    path('calendar/google/init/', views.GoogleCalendarInitView.as_view(), name='google_calendar_init'),
    path('calendar/google/redirect/', views.GoogleCalendarRedirectView.as_view(), name='google_calendar_redirect'),
    path('calendar/microsoft/init/', views.MicrosoftCalendarInitView.as_view(), name='microsoft_calendar_init'),
    path('calendar/microsoft/redirect/', views.MicrosoftCalendarRedirectView.as_view(), name='microsoft_calendar_redirect'),
    path('api/calendar-events/', views.get_calendar_events_api, name='calendar_events_api'),


    # =============================================================================
    # COMMUNICATIONS & MESSAGING
    # =============================================================================
    path('communications/', views.CommunicationsView.as_view(), name='communications'),
    path('api/conversation/<int:conversation_id>/', views.conversation_detail_api, name='conversation_detail_api'),
    path('api/send-message/<int:conversation_id>/', views.send_message_api, name='send_message_api'),
    path('api/send-video-link/', views.send_video_link_api, name='send_video_link_api'),
    path('api/video/create/<int:conversation_id>/', views.create_video_call_api, name='create_video_call_api'),
    path('video-call/<str:room_name>/', views.video_call_view, name='video_call_view'),

    # =============================================================================
    # FINANCIAL, WALLET & SUBSCRIPTIONS
    # =============================================================================
    path('my-finances/', views.MyFinancesView.as_view(), name='my_finances'),
    path('my-finances/salary/', views.SalaryManagementView.as_view(), name='salary_management'),
    path('subscriptions/', views.ManageSubscriptionsView.as_view(), name='subscriptions'),
    path('subscription-plans/', views.SubscriptionPlansView.as_view(), name='subscription_plans'),
    path('client-plans/manage/', views.ClientSubscriptionPlanManageView.as_view(), name='manage_client_plan'),
    path('wallet/', views.WalletView.as_view(), name='wallet'),
    path('wallet/create-checkout-session/', views.CreateCheckoutSessionView.as_view(), name='create_checkout_session'),
    path('wallet/recharge-success/', views.WalletRechargeSuccessView.as_view(), name='wallet_recharge_success'),
    path('wallet/recharge-cancel/', views.WalletRechargeCancelView.as_view(), name='wallet_recharge_cancel'),
    path('wallet/attach-payment-method/', views.AttachPaymentMethodView.as_view(), name='attach_payment_method'),
    path('api/get_wallet_balance/', views.get_wallet_balance, name='get_wallet_balance'),
    path('my-finances/create-payment-link/', views.create_payment_link, name='create_payment_link'), 
    path('my-finances/stripe-choice/', views.ChooseAccountTypeView.as_view(), name='stripe_connect_choice'),
    path('my-finances/stripe/dashboard-link/', views.stripe_dashboard_link, name='stripe_dashboard_link'),
    path('api/stripe/create-account-session/', views.create_stripe_account_session, name='create_stripe_account_session'),
   
    # Stripe Onboarding URLs <-- ADD THIS ENTIRE BLOCK
    path('stripe/authorize/', views.stripe_authorize, name='stripe_authorize'),
    path('stripe/callback/', views.stripe_callback, name='stripe_callback'),
    path('stripe/create-express/', views.stripe_create_express_account, name='stripe_create_express'),
    path('stripe/express-return/', views.stripe_express_return, name='stripe_express_return'),

    # =============================================================================
    # AI FEATURES, FORMS & OTHER TOOLS
    # =============================================================================
    path('account/toggle-2fa/', views.toggle_2fa, name='toggle_2fa'), 

    path('ai-command/', views.process_ai_command, name='process_ai_command'),
    path('ai-voice-assistant/', views.AIVoiceAssistantView.as_view(), name='ai_voice_assistant'),
    path('api/search_available_numbers/', views.search_available_numbers, name='search_available_numbers'),
    path('api/get_call_transcript/<int:log_id>/', views.get_call_transcript_api, name='get_call_transcript_api'),
    path('demand-forecasting/', views.DemandForecastingView.as_view(), name='demand_forecasting'),
    path('settings/forms/new/', views.custom_form_builder_view, name='custom_form_builder_new'),
    path('settings/forms/<int:form_id>/', views.custom_form_builder_view, name='custom_form_builder'),
    path('forms/send/<int:form_id>/', views.send_form_to_client, name='send_form_to_client'),
    path('api-documentation/', views.api_documentation, name='api_documentation'),


# WEBHOOKS

    path('webhooks/postmark/', views.PostmarkWebhookView.as_view(), name='postmark_webhook'),
    path('webhooks/telnyx/', views.TelnyxWebhookView.as_view(), name='telnyx_webhook'),



]
