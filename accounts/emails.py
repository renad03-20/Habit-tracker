from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import strip_tags


def _build_absolute_url(request, url):
    return request.build_absolute_uri(url)


def send_verification_email(request, user, token):
    """Send email address verification link."""
    url = _build_absolute_url(
        request,
        reverse("accounts:verify_email", kwargs={"token": str(token.token)}),
    )
    context = {"user": user, "verification_url": url, "site_name": settings.SITE_NAME}
    html_message = render_to_string("auth/emails/verify_email.html", context)
    plain_message = strip_tags(html_message)
    send_mail(
        subject=f"Verify your email — {settings.SITE_NAME}",
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_password_reset_email(request, user, token):
    """Send password reset link."""
    url = _build_absolute_url(
        request,
        reverse("accounts:password_reset_confirm", kwargs={"token": str(token.token)}),
    )
    context = {"user": user, "reset_url": url, "site_name": settings.SITE_NAME}
    html_message = render_to_string("auth/emails/password_reset.html", context)
    plain_message = strip_tags(html_message)
    send_mail(
        subject=f"Reset your password — {settings.SITE_NAME}",
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_password_changed_notification(user):
    """Notify user that their password was changed."""
    context = {"user": user, "site_name": settings.SITE_NAME}
    html_message = render_to_string("auth/emails/password_changed.html", context)
    plain_message = strip_tags(html_message)
    send_mail(
        subject=f"Your password was changed — {settings.SITE_NAME}",
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=True,  # Don't crash if notification fails
    )
