from django.contrib.auth.models import (
    BaseUserManager,
    AbstractBaseUser,
    PermissionsMixin,
)
from django.db.models import (
    UUIDField,
    EmailField,
    CharField,
    BooleanField,
    DateTimeField,
    Model,
    TextField,
    ImageField,
    DateField,
    CASCADE,
    OneToOneField,
)
from django.utils import timezone
from .utils import GenerateUUID
from .choices import (
    GenderChoices,
    CountryChoices,
    OTPTypeChoices,
)
from uuid import uuid4
from datetime import timedelta


class WhisperUserManager(BaseUserManager):
    """
    Creates a custom object manager class for the `User` model.
    This handles user and superuser creation.
    """

    def _create_user(self, **kwargs):
        email = kwargs.pop("email")
        normalized_email = self.normalize_email(email)
        password = kwargs.pop("password", None)
        if not kwargs.get("username"):
            username = GenerateUUID().random_username()
            kwargs.setdefault("username", username)
        user = self.model(email=normalized_email, **kwargs)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_user(self, **kwargs):
        return self._create_user(**kwargs)

    def create_superuser(self, **kwargs):
        kwargs.setdefault("is_email_verified", True)
        kwargs.setdefault("is_superuser", True)
        kwargs.setdefault("is_staff", True)
        return self._create_user(**kwargs)


class User(AbstractBaseUser, PermissionsMixin):
    """
    This is the [custom] User model class for whisper.
    """

    id = UUIDField(primary_key=True, editable=False, unique=True, default=uuid4)
    email = EmailField(max_length=120, blank=False, unique=True, db_index=True)
    username = CharField(max_length=120, unique=True, db_index=True)
    password = CharField(max_length=200, editable=False, blank=False)
    is_email_verified = BooleanField(default=False, db_index=True)
    is_active = BooleanField(default=True)
    is_superuser = BooleanField(default=False)
    is_staff = BooleanField(default=False)
    is_online = BooleanField(default=False, db_index=True)
    created = DateTimeField(auto_now_add=True, db_index=True)
    updated = DateTimeField(auto_now=True)
    last_login = DateTimeField(auto_now=True)

    objects = WhisperUserManager()
    USERNAME_FIELD = "email"

    class Meta:
        db_table = "user"
        ordering = ["-created"]

    def __str__(self):
        return self.username


class UserProfile(Model):
    id = UUIDField(primary_key=True, editable=False, unique=True, default=uuid4)
    display_name = CharField(max_length=120, blank=True, db_index=True)
    bio = TextField(blank=True)
    avatar = ImageField(blank=True, upload_to="avatars/")
    gender = CharField(
        max_length=4,
        blank=True,
        choices=GenderChoices.choices,
        default=GenderChoices.CYBORG,
        db_index=True,
    )
    date_of_birth = DateField(blank=True, null=True)
    nationality = CharField(
        max_length=2,
        blank=True,
        choices=CountryChoices.choices,
        default=CountryChoices.UNITED_STATES_OF_AMERICA,
        db_index=True,
    )
    user = OneToOneField(User, related_name="profile", on_delete=CASCADE)
    created = DateTimeField(auto_now_add=True, db_index=True)
    updated = DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_profile"
        ordering = ["-created"]

    def __str__(self):
        return f"{self.user.username}'s profile"


class UserOTP(Model):
    otp_code = CharField(max_length=6, unique=True, editable=False, db_index=True)
    otp_type = CharField(
        max_length=3,
        blank=True,
        choices=OTPTypeChoices.choices,
        default=OTPTypeChoices.EMAIL,
        db_index=True,
    )
    user = OneToOneField(User, related_name="otp", on_delete=CASCADE)
    expiry = DateTimeField(
        editable=False, db_index=True, default=timezone.now() + timedelta(minutes=5)
    )

    class Meta:
        db_table = "user_otp"
        ordering = ["-expiry"]

    def __str__(self):
        return f"{self.user.username}'s OTP code"


class JWTAccessToken(Model):
    access_token = CharField(
        max_length=1024,
        unique=True,
        db_index=True,
    )
    user = OneToOneField(User, related_name="access_token", on_delete=CASCADE)
    created = DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "user_jwt_access_token"
        ordering = ["-created"]

    def __str__(self):
        return f"{self.user.username}'s JWT access token"

    def save(self, *args, **kwargs) -> None:
        if not self.access_token:
            self.access_token = GenerateUUID().random_access_token()
        return super().save(*args, **kwargs)
