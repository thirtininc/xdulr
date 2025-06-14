# This file is intended for helper functions that can be reused across different views.
# For example, functions for sending emails, processing payments, or interacting
# with external APIs would go here.

import stripe
from django.conf import settings
from django.core.mail import send_mail

# Set the Stripe API key from settings
stripe.api_key = settings.STRIPE_SECRET_KEY

def send_custom_email(subject, message, recipient_list):
    """
    A wrapper around Django's send_mail function for sending emails.
    """
    try:
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            recipient_list,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def create_stripe_connect_account(user):
    """
    Creates a Stripe Express connected account for a new practitioner.
    """
    try:
        account = stripe.Account.create(
            type='express',
            country='CA',  # Or get from user profile
            email=user.email,
            capabilities={
                'card_payments': {'requested': True},
                'transfers': {'requested': True},
            },
        )
        return account.id
    except Exception as e:
        print(f"Error creating Stripe connected account: {e}")
        return None

def create_stripe_onboarding_link(account_id, refresh_url, return_url):
    """
    Generates a one-time link for a practitioner to onboard with Stripe.
    """
    try:
        account_link = stripe.AccountLink.create(
            account=account_id,
            refresh_url=refresh_url,
            return_url=return_url,
            type='account_onboarding',
        )
        return account_link.url
    except Exception as e:
        print(f"Error creating Stripe onboarding link: {e}")
        return None
