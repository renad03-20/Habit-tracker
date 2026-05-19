from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    # Registration & Email verification
    path("signup/", views.signup_view, name="signup"),
    path("verify-email/<uuid:token>/", views.verify_email_view, name="verify_email"),
    path("resend-verification/", views.resend_verification_view, name="resend_verification"),

    # Login / Logout
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    # Password reset flow
    path("password-reset/", views.password_reset_request_view, name="password_reset_request"),
    path("password-reset/<uuid:token>/", views.password_reset_confirm_view, name="password_reset_confirm"),

    # Authenticated
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("change-password/", views.change_password_view, name="change_password"),
]
