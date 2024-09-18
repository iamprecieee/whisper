from django.db.transaction import atomic
from rest_framework.serializers import (
    ModelSerializer,
    CharField,
    Serializer,
    EmailField,
    SerializerMethodField,
)
from .models import User, UserProfile, JWTAccessToken
from .utils import ValidateEmail, ValidatePassword, ValidateUsername, EmailOTP

from .refresh import SessionRefreshToken
from rest_framework_simplejwt.tokens import RefreshToken


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "is_online",
            "is_email_verified",
            "created",
        ]
        read_only_fields = ["id", "email", "is_online", "is_email_verified", "created"]


class UserProfileSerializer(ModelSerializer):
    username = SerializerMethodField()
    user = SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            "id",
            "username",
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
        read_only_fields = ["id", "created", "updated"]

    def get_username(self, obj):
        return obj.user.username

    def get_user(self, obj):
        return str(obj.user.id)


class RegisterSerializer(ModelSerializer):
    username = CharField(required=False)
    password = CharField(write_only=True)
    confirm_password = CharField(write_only=True)

    class Meta:
        model = User
        fields = ["email", "password", "confirm_password", "username"]

    def validate(self, data):
        password = data["password"]
        confirm_password = data["confirm_password"]
        username = data.get("username")
        validate_password_instance = ValidatePassword(password, confirm_password)
        validate_password_instance.check_format()
        if username:
            validate_username_instance = ValidateUsername(username, check_db=True)
            validate_username_instance.check_existence()
        return data

    def save(self, **kwargs):
        validated_data = self.validated_data
        validated_data.pop("confirm_password")
        with atomic():
            user = User.objects.create_user(**validated_data)
            UserProfile.objects.create(user=user)
            JWTAccessToken.objects.create(user=user)
            email_otp_instance = EmailOTP(validated_data["email"], check_db=True)
            email_otp_instance.send_check_all()
            return {
                "user": user,
                "message": "A verification link has been sent to your email.",
                "is_email_sent": email_otp_instance.is_email_sent,
            }

    def to_representation(self, instance):
        user_data = UserSerializer(instance["user"]).data
        user_data["message"] = instance["message"]
        user_data["is_email_sent"] = instance["is_email_sent"]
        return user_data


class VerifyEmailBeginSerializer(Serializer):
    email = EmailField(write_only=True)

    def validate(self, data):
        validate_email_instance = ValidateEmail(data["email"], check_db=True)
        validate_email_instance.check_non_existence()
        return data

    def save(self, **kwargs):
        validated_data = self.validated_data
        email_otp_instance = EmailOTP(validated_data["email"], check_db=True)
        email_otp_instance.check_unused()
        email_otp_instance.send_check_all()
        return {
            "message": "A verfication link has been sent to your email address.",
            "is_email_sent": email_otp_instance.is_email_sent,
        }


class VerifyEmailCompleteSerializer(Serializer):
    token = CharField(write_only=True)

    def validate(self, data):
        token = data["token"]
        email_otp_instance = EmailOTP(token=token)
        email_otp_instance.check_used_or_invalid_or_expired()
        data["id"], data["email"], data["username"], data["is_email_verified"] = (
            email_otp_instance.retrieve_user_data()
        )
        return data

    def save(self, **kwargs):
        validated_data = self.validated_data
        validated_data.pop("token")
        validated_data["id"] = str(validated_data["id"])
        return validated_data

    def to_representation(self, instance):
        return instance


class LoginSerializer(Serializer):
    email = CharField()
    access = CharField()
    refresh = CharField()

    def validate(self, data):
        validate_email_instance = ValidateEmail(data["email"], check_db=True)
        validate_email_instance.check_email_verified()
        return data

    def save(self, **kwargs):
        validated_data = self.validated_data
        session_refresh_instance = SessionRefreshToken(self.context["request"])
        with atomic():
            user = (
                User.objects.select_related("access_token")
                .select_for_update(of=["access_token_access_token"])
                .filter(email=validated_data["email"])
                .first()
            )
            user.access_token.access_token = validated_data["access"]
            user.access_token.save(update_fields=["access_token"])
            session_refresh_instance.add_token(validated_data["refresh"])
        validated_data["id"] = user.id
        validated_data["username"] = user.username
        return validated_data

    def to_representation(self, instance):
        return instance


class RefreshTokenSerializer(Serializer):
    """
    Serializer for generating new access tokens, and blacklisting refresh tokens.
    Previous refresh token is blacklisted and replaced by a new token.
    """

    def save(self, **kwargs):
        request = self.context["request"]
        new_refresh_token = RefreshToken()
        with atomic():
            session_refresh_instance = SessionRefreshToken(request)
            session_refresh_instance.remove_token()
            session_refresh_instance.add_token(str(new_refresh_token))
            request.user.access_token.access_token = new_refresh_token.access_token
            request.user.access_token.save(update_fields=["access_token"])

        jwt_data = {
            "access": str(new_refresh_token.access_token),
            "refresh": str(new_refresh_token),
            "id": str(request.user.id),
            "email": request.user.email,
            "username": request.user.username,
        }
        return jwt_data

    def to_representation(self, instance):
        return instance
