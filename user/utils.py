from rest_framework.exceptions import ValidationError
from uuid import UUID, uuid4
import re
from django.conf import settings
from django.core import signing, mail
from django.db.transaction import atomic
from django.utils import timezone
from pyotp import TOTP, random_base32
import smtplib
from .choices import OTPTypeChoices


class GenerateUUID:
    """
    Generates a random UUID and replaces the first group of characters
    with '036157e40'[in place of '0whisper0', because UUIDs 😀],
    or '0acce550'[in place of '0access0'],
    or 'c6a3be40'[in place of 'chamber0'].

    NB: '0acce550-...' IS A PLACEHOLDER AND CANNOT BE USED FOR AUTHENTICATION.
    """

    def __init__(self) -> None:
        self.uuid_string = uuid4()
        self.apheretic_uuid_string = re.search(
            r"(?<=-)\S+", str(self.uuid_string)
        ).group()

    def random_username(self) -> UUID:
        return UUID(f"03ea7e40-{self.apheretic_uuid_string}")

    def random_access_token(self) -> UUID:
        return UUID(f"0acce550-{self.apheretic_uuid_string}")

    def random_chambertag(self) -> UUID:
        return UUID(f"c6a3be40-{self.apheretic_uuid_string}")


class ValidateEmail:
    def __init__(self, email, check_db=False) -> None:
        self.email = email
        self.user = None
        if check_db:
            from .models import User

            user = User.objects.filter(email=self.email).first()
            if user:
                self.user = user

    def check_existence(self) -> None | Exception:
        if self.user:
            raise ValidationError({"email": "A user with this email already exists."})

    def check_non_existence(self) -> None | Exception:
        if not self.user:
            raise ValidationError(
                {"email": "No registered user exists with this email."}
            )

    def check_email_verified(self) -> None | Exception:
        if all([self.user, not self.user.is_email_verified]):
            raise ValidationError(
                {
                    "email": "Click the link sent to your email to verify your account, or request a new one to proceed."
                }
            )


class ValidatePassword:
    def __init__(self, password1, password2) -> None:
        self.password1 = password1
        self.password2 = password2

    def check_format(self) -> None | Exception:
        if len(self.password1) < 8:
            raise ValidationError({"password": "Password is too short."})
        elif not re.search(r"[A-Z]", self.password1):
            raise ValidationError(
                {"password": "Password must contain at least one uppercase letter."}
            )
        elif not re.search(r"[a-z]", self.password1):
            raise ValidationError(
                {"password": "Password must contain at least one lowercase letter."}
            )
        elif not re.search(r"[0-9]", self.password1):
            raise ValidationError(
                {"password": "Password must contain at least one digit."}
            )
        elif not re.search(r"[!@#$%^&*|]", self.password1):
            raise ValidationError(
                {"password": "Password must contain at least one valid symbol."}
            )
        elif self.password1 != self.password2:
            raise ValidationError({"password": "Passwords do not match."})


class ValidateUsername:
    def __init__(self, username, check_db=False) -> None:
        self.username = username
        self.user = None
        if check_db:
            from .models import User

            user = User.objects.filter(username=self.username).first()
            if user:
                self.user = user

    def check_existence(self) -> None:
        if self.user:
            raise ValidationError(
                {"username": "A user with this username already exists."}
            )


class EmailOTP:
    def __init__(
        self, email=None, otp_type=OTPTypeChoices.EMAIL, token=None, check_db=False
    ) -> None:
        from .models import User

        self.email = email
        self.otp_type = otp_type
        self.token = token
        self.check_db = check_db
        self.otp_code = None
        self.user = None
        self.user_id = None
        self.is_email_sent = False

        if self.check_db:
            user = User.objects.filter(email=self.email).first()
            if user:
                self.user = user
        elif self.token:
            self.decode_signed_token()
            self.user = User.objects.filter(id=self.user_id).first()

    def generate_otp_code(self) -> None:
        from .models import UserOTP

        if self.user:
            otp_code = TOTP(random_base32(), digits=6).now()
            UserOTP.objects.create(
                otp_code=otp_code, otp_type=self.otp_type, user=self.user
            )
            self.otp_code = otp_code

    def generate_signed_token(self) -> None:
        self.token = signing.dumps((self.otp_code, str(self.user.id)))

    def send_otp_email(self) -> None:
        current_host = settings.CURRENT_HOST
        sender_email = settings.SENDER_EMAIL
        if self.otp_type == OTPTypeChoices.EMAIL:
            url_path = "verify-email"
            operation_message = "verify your email"
            subject = "Email Verification"
        elif self.otp_type == OTPTypeChoices.PASSWORD:
            url_path = "change-password"
            operation_message = "change your password"
            subject = "Password Change"

        html_message = f"""
            <html>
                <body>
                    <p>
                        Click this link to {operation_message}:<br>
                        <a href='https://{current_host}/api/v1/weaver/{url_path}/complete/{self.token}/'>{url_path.replace('-', ' ').capitalize()}</a>
                    </p>
                </body>
            </html>
        """

        mail.send_mail(
            subject=subject,
            message=html_message,
            from_email=sender_email,
            recipient_list=[self.email],
            html_message=html_message,
            fail_silently=False,
        )
        if len(mail.outbox) == 1:
            self.is_email_sent = True

    def send_check_all(self) -> None | Exception:
        try:
            with atomic():
                self.generate_otp_code()
                self.generate_signed_token()
                self.send_otp_email()
        except smtplib.SMTPException:
            raise ValidationError(
                {
                    "smtp": "An SMTPException occurred. Verification email failed to send."
                }
            )

    def decode_signed_token(self) -> None | Exception:
        try:
            self.otp_code, self.user_id = signing.loads(self.token)
        except signing.BadSignature:
            raise ValidationError({"OTP": "Invalid OTP token detected."})

    def check_used_or_invalid_or_expired(self) -> None | Exception:
        if self.user.is_email_verified:
            raise ValidationError(
                {"OTP": "This user's email has already been verified."}
            )
        user_otp = self.user.otp
        if any(
            [user_otp.otp_code != str(self.otp_code), timezone.now() > user_otp.expiry]
        ):
            user_otp.delete()
            raise ValidationError(
                {
                    "OTP": "OTP code is invalid or expired, request a new verification link."
                }
            )

    def check_unused(self) -> None | Exception:
        if all([self.user, not self.user.is_email_verified, hasattr(self.user, "otp")]):
            raise ValidationError(
                {"OTP": "Check your email for an already existing verification link."}
            )

    def retrieve_user_data(self) -> tuple:
        with atomic():
            self.user.otp.delete()
            self.user.is_email_verified = True
            self.user.save(update_fields=["is_email_verified"])
        return (
            self.user.id,
            self.user.email,
            self.user.username,
            self.user.is_email_verified,
        )
