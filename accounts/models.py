import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_("Email address is required."))
        email = self.normalize_email(email)
        extra_fields.setdefault("is_active", False)  # inactive until email verified
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("email_verified", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model using email as the unique identifier.
    Supports email verification, account locking, and login tracking.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_("email address"), unique=True, db_index=True)
    first_name = models.CharField(_("first name"), max_length=150, blank=True)
    last_name = models.CharField(_("last name"), max_length=150, blank=True)

    # Status flags
    is_staff = models.BooleanField(_("staff status"), default=False)
    is_active = models.BooleanField(_("active"), default=False)
    email_verified = models.BooleanField(_("email verified"), default=False)

    # Security tracking
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    failed_login_attempts = models.PositiveSmallIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")

    def __str__(self):
        return self.email

    def get_full_name(self):
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name or self.email

    def get_short_name(self):
        return self.first_name or self.email.split("@")[0]

    @property
    def is_locked(self):
        if self.locked_until and timezone.now() < self.locked_until:
            return True
        return False

    def record_failed_login(self):
        from datetime import timedelta
        self.failed_login_attempts += 1
        # Lock after 5 failed attempts; lock duration increases with each lockout
        if self.failed_login_attempts >= 5:
            lock_minutes = min(2 ** (self.failed_login_attempts - 5), 60)
            self.locked_until = timezone.now() + timedelta(minutes=lock_minutes)
        self.save(update_fields=["failed_login_attempts", "locked_until"])

    def clear_failed_logins(self):
        if self.failed_login_attempts > 0 or self.locked_until:
            self.failed_login_attempts = 0
            self.locked_until = None
            self.save(update_fields=["failed_login_attempts", "locked_until"])


class EmailVerificationToken(models.Model):
    """One-time token for email verification."""
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="email_verification_token"
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("email verification token")

    def __str__(self):
        return f"Verification token for {self.user.email}"

    @property
    def is_expired(self):
        from datetime import timedelta
        return timezone.now() > self.created_at + timedelta(hours=24)


class PasswordResetToken(models.Model):
    """One-time token for password reset (separate from Django's built-in)."""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="password_reset_tokens"
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("password reset token")

    def __str__(self):
        return f"Reset token for {self.user.email}"

    @property
    def is_expired(self):
        from datetime import timedelta
        return timezone.now() > self.created_at + timedelta(hours=1)


class LoginSession(models.Model):
    """Track active sessions per user for security awareness."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="login_sessions")
    session_key = models.CharField(max_length=40, unique=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("login session")
        ordering = ["-last_activity"]

    def __str__(self):
        return f"{self.user.email} — {self.ip_address}"
