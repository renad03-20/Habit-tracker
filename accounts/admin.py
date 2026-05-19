from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import EmailVerificationToken, LoginSession, PasswordResetToken, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("email", "first_name", "last_name", "is_active", "email_verified", "date_joined", "last_login")
    list_filter = ("is_active", "email_verified", "is_staff", "is_superuser")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("-date_joined",)
    readonly_fields = ("id", "date_joined", "last_login", "last_login_ip", "failed_login_attempts", "locked_until")

    fieldsets = (
        (None, {"fields": ("id", "email", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name")}),
        (_("Status"), {"fields": ("is_active", "email_verified", "is_staff", "is_superuser")}),
        (_("Security"), {"fields": ("last_login_ip", "failed_login_attempts", "locked_until")}),
        (_("Permissions"), {"fields": ("groups", "user_permissions")}),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "first_name", "last_name", "password1", "password2"),
        }),
    )


@admin.register(LoginSession)
class LoginSessionAdmin(admin.ModelAdmin):
    list_display = ("user", "ip_address", "created_at", "last_activity")
    list_filter = ("created_at",)
    search_fields = ("user__email", "ip_address")
    readonly_fields = ("user", "session_key", "ip_address", "user_agent", "created_at", "last_activity")


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "token", "created_at")
    readonly_fields = ("user", "token", "created_at")


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at", "used")
    list_filter = ("used",)
    readonly_fields = ("user", "token", "created_at", "used")
