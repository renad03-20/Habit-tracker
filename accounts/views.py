import logging
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from .emails import (
    send_password_reset_email,
    send_verification_email,
    send_password_changed_notification,
)
from .forms import (
    ChangePasswordForm,
    LoginForm,
    PasswordResetConfirmForm,
    PasswordResetRequestForm,
    SignUpForm,
)
from .models import (
    EmailVerificationToken,
    LoginSession,
    PasswordResetToken,
    User,
)

logger = logging.getLogger(__name__)


def _get_client_ip(request):
    x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded:
        return x_forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def _record_login_session(request, user):
    if request.session.session_key is None:
        request.session.create()
    LoginSession.objects.update_or_create(
        session_key=request.session.session_key,
        defaults={
            "user": user,
            "ip_address": _get_client_ip(request),
            "user_agent": request.META.get("HTTP_USER_AGENT", "")[:500],
        },
    )


# ──────────────────────────────────────────────
# Sign Up
# ──────────────────────────────────────────────

@never_cache
@require_http_methods(["GET", "POST"])
def signup_view(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        token = EmailVerificationToken.objects.create(user=user)
        send_verification_email(request, user, token)
        messages.success(
            request,
            _("Account created! Please check your email to verify your address before logging in."),
        )
        logger.info("New user registered: %s", user.email)
        return redirect("accounts:login")

    return render(request, "auth/signup.html", {"form": form})


# ──────────────────────────────────────────────
# Email Verification
# ──────────────────────────────────────────────

@never_cache
def verify_email_view(request, token):
    verification = get_object_or_404(EmailVerificationToken, token=token)

    if verification.is_expired:
        verification.delete()
        messages.error(
            request,
            _("This verification link has expired. Please request a new one."),
        )
        return redirect("accounts:resend_verification")

    user = verification.user
    user.is_active = True
    user.email_verified = True
    user.save(update_fields=["is_active", "email_verified"])
    verification.delete()

    messages.success(request, _("Email verified! You can now log in."))
    logger.info("Email verified for user: %s", user.email)
    return redirect("accounts:login")


@never_cache
@require_http_methods(["GET", "POST"])
def resend_verification_view(request):
    if request.method == "POST":
        email = request.POST.get("email", "").lower().strip()
        try:
            user = User.objects.get(email=email, email_verified=False)
            token, _ = EmailVerificationToken.objects.get_or_create(user=user)
            if not token.is_expired:
                # Recreate the token to extend expiry
                token.delete()
                token = EmailVerificationToken.objects.create(user=user)
            send_verification_email(request, user, token)
        except User.DoesNotExist:
            pass  # Don't reveal whether the email exists
        messages.success(
            request,
            _("If that email belongs to an unverified account, we've sent a new link."),
        )
        return redirect("accounts:login")

    return render(request, "auth/resend_verification.html")


# ──────────────────────────────────────────────
# Login / Logout
# ──────────────────────────────────────────────

@never_cache
@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"]
        password = form.cleaned_data["password"]
        remember_me = form.cleaned_data.get("remember_me", False)

        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, _("Invalid email or password."))
            return render(request, "auth/login.html", {"form": form})

        # Account lock check
        if user_obj.is_locked:
            remaining = (user_obj.locked_until - timezone.now()).seconds // 60 + 1
            messages.error(
                request,
                _(f"Account temporarily locked. Try again in {remaining} minute(s)."),
            )
            return render(request, "auth/login.html", {"form": form})

        # Email verification check
        if not user_obj.email_verified:
            messages.warning(
                request,
                _("Please verify your email address first. Check your inbox or request a new link."),
            )
            return render(request, "auth/login.html", {"form": form})

        user = authenticate(request, username=email, password=password)
        if user is None:
            user_obj.record_failed_login()
            messages.error(request, _("Invalid email or password."))
            logger.warning("Failed login attempt for: %s from %s", email, _get_client_ip(request))
            return render(request, "auth/login.html", {"form": form})

        # Successful login
        user.clear_failed_logins()
        user.last_login_ip = _get_client_ip(request)
        user.save(update_fields=["last_login_ip"])

        login(request, user)

        if not remember_me:
            # Session expires when browser closes
            request.session.set_expiry(0)
        else:
            # 30 days
            request.session.set_expiry(60 * 60 * 24 * 30)

        _record_login_session(request, user)

        logger.info("Successful login: %s from %s", user.email, _get_client_ip(request))

        next_url = request.GET.get("next") or "accounts:dashboard"
        # Validate next URL is safe (relative only)
        if next_url.startswith("http") or next_url.startswith("//"):
            next_url = "accounts:dashboard"
        return redirect(next_url)

    return render(request, "auth/login.html", {"form": form})


@require_http_methods(["POST"])
def logout_view(request):
    if request.user.is_authenticated:
        # Delete session record
        if request.session.session_key:
            LoginSession.objects.filter(session_key=request.session.session_key).delete()
        logger.info("User logged out: %s", request.user.email)
    logout(request)
    messages.success(request, _("You have been signed out."))
    return redirect("accounts:login")


# ──────────────────────────────────────────────
# Password Reset
# ──────────────────────────────────────────────

@never_cache
@require_http_methods(["GET", "POST"])
def password_reset_request_view(request):
    form = PasswordResetRequestForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"]
        try:
            user = User.objects.get(email=email, is_active=True)
            # Invalidate old tokens
            PasswordResetToken.objects.filter(user=user, used=False).update(used=True)
            token = PasswordResetToken.objects.create(user=user)
            send_password_reset_email(request, user, token)
            logger.info("Password reset requested for: %s", email)
        except User.DoesNotExist:
            pass  # Don't reveal if email exists
        messages.success(
            request,
            _("If that email is registered, you'll receive a password reset link shortly."),
        )
        return redirect("accounts:login")

    return render(request, "auth/password_reset_request.html", {"form": form})


@never_cache
@require_http_methods(["GET", "POST"])
def password_reset_confirm_view(request, token):
    reset_token = get_object_or_404(PasswordResetToken, token=token, used=False)

    if reset_token.is_expired:
        reset_token.used = True
        reset_token.save()
        messages.error(request, _("This password reset link has expired. Please request a new one."))
        return redirect("accounts:password_reset_request")

    form = PasswordResetConfirmForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = reset_token.user
        user.set_password(form.cleaned_data["password1"])
        user.save(update_fields=["password"])
        reset_token.used = True
        reset_token.save()
        # Invalidate all sessions
        LoginSession.objects.filter(user=user).delete()
        send_password_changed_notification(user)
        messages.success(request, _("Password changed successfully. Please log in."))
        logger.info("Password reset completed for: %s", user.email)
        return redirect("accounts:login")

    return render(request, "auth/password_reset_confirm.html", {"form": form, "token": token})


# ──────────────────────────────────────────────
# Authenticated views
# ──────────────────────────────────────────────

@login_required
def dashboard_view(request):
    sessions = LoginSession.objects.filter(user=request.user).order_by("-last_activity")[:10]
    return render(request, "auth/dashboard.html", {"sessions": sessions})


@login_required
@require_http_methods(["GET", "POST"])
def change_password_view(request):
    form = ChangePasswordForm(user=request.user, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        # Keep user logged in after password change
        update_session_auth_hash(request, request.user)
        send_password_changed_notification(request.user)
        messages.success(request, _("Password changed successfully."))
        return redirect("accounts:dashboard")

    return render(request, "auth/change_password.html", {"form": form})
