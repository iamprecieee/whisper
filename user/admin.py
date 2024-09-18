from django.contrib.admin import register, ModelAdmin
from .models import User, UserProfile, UserOTP, JWTAccessToken


@register(User)
class UserAdmin(ModelAdmin):
    list_display = [
        "id",
        "email",
        "username",
        "password",
        "is_email_verified",
        "is_superuser",
        "is_staff",
        "is_active",
        "is_online",
        "created",
        "updated",
        "last_login",
    ]
    list_filter = [
        "id",
        "email",
        "is_superuser",
        "is_staff",
        "is_active",
        "is_online",
        "created",
    ]


@register(UserProfile)
class UserProfileAdmin(ModelAdmin):
    list_display = [
        "id",
        "display_name",
        "bio",
        "avatar",
        "gender",
        "date_of_birth",
        "nationality",
        "user",
        "created",
        "updated",
    ]
    list_filter = ["id", "user", "created"]


@register(UserOTP)
class UserOTPAdmin(ModelAdmin):
    list_display = ["otp_code", "otp_type", "user", "expiry"]
    list_filter = ["user", "otp_type", "expiry"]


@register(JWTAccessToken)
class JWTAccessTokenAdmin(ModelAdmin):
    list_display = ["access_token", "user", "created"]
    list_filter = ["user", "created"]
