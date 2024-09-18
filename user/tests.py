from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase, APITransactionTestCase
from .models import User, UserProfile, JWTAccessToken
from django.utils import timezone
from time import sleep
from datetime import timedelta
from .utils import EmailOTP


class RegisterViewTestCase(APITransactionTestCase):
    def setUp(self):
        self.url = reverse("user:register")

    def test_register_success(self):
        response = self.client.post(
            self.url,
            data={
                "email": "admin@gmail.com",
                "password": "Adm@n1234",
                "confirm_password": "Adm@n1234",
            },
        )
        self.assertEqual(response.data["email"], "admin@gmail.com")
        self.assertEqual(response.data["is_email_sent"], True)
        email = response.data["email"]
        user = User.objects.filter(email=email).first()
        self.assertEqual(
            all(
                [
                    user.is_superuser,
                    UserProfile.objects.filter(user=user).exists(),
                    JWTAccessToken.objects.filter(user=user).exists(),
                ]
            ),
            False,
        )

    def run_test_register_failure_email(self):
        for i in range(2):
            response = self.client.post(
                self.url,
                data={
                    "email": "emmypresh777@gmail.com",
                    "password": "Adm@n1234",
                    "confirm_password": "Adm@n1234",
                },
            )
        self.assertEqual("User with this email already exists.", response.data)

        response2 = self.client.post(
            self.url,
            data={
                "email": "admingmail.com",
                "password": "Adm@n1234",
                "confirm_password": "Adm@n1234",
            },
        )
        self.assertEqual("Enter a valid email address.", response2.data)

    def test_register_failure_password(self):
        response = self.client.post(
            self.url, data={"email": "emmypresh777@gmail.com", "password": "Adm@n1234"}
        )
        self.assertEqual("Confirm_Password field is required.", response.data)

        response2 = self.client.post(
            self.url,
            data={
                "email": "admin@gmail.com",
                "password": "Admin134",
                "confirm_password": "Admin134",
            },
        )
        self.assertEqual(
            "Password must contain at least one valid symbol.", response2.data
        )

    def tearDown(self) -> None:
        sleep(1)


class VerifyEmailCompleteViewTestCase(APITransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="admin@gmail.com", password="Adm1!n123"
        )
        JWTAccessToken.objects.create(user=self.user)

        self.email_otp_instance = EmailOTP(self.user.email, check_db=True)
        self.email_otp_instance.generate_otp_code()
        self.email_otp_instance.generate_signed_token()

        self.url = reverse(
            "user:verify-email-complete",
            kwargs={"token": self.email_otp_instance.token},
        )
        self.url2 = reverse(
            "user:verify-email-complete",
            kwargs={
                "token": "WyI4Njk5MDAiLCI1NjRiZjBiOC0yZWVhLTRlY2ItOWU2MS1lNGMxNmIzZWRkODIiXQ:1siybP:cugzQP3k4oOoEQS0YoH8klsOeCUKLQkguUDOch_k6H8"
            },
        )

    def test_verify_email_complete_success(self):
        response = self.client.post(self.url)
        for string in ["id", "email", "username", "is_email_verified"]:
            self.assertIn(string, response.data)

    def test_verify_email_complete_failure_invalid_token(self):
        response = self.client.post(self.url2)
        self.assertEqual("Invalid otp token detected.", response.data)
        for i in range(2):
            response2 = self.client.post(self.url)
        self.assertEqual("This user's email has already been verified.", response2.data)

    def test_verify_email_complete_failure_expired_token(self):
        self.user.otp.expiry = timezone.now() + timedelta(seconds=5)
        self.user.otp.save(update_fields=["expiry"])
        sleep(10)
        response = self.client.post(self.url)
        self.assertEqual(
            "Otp code is invalid or expired, request a new verification link.",
            response.data,
        )

    def tearDown(self) -> None:
        sleep(1)


class VerifyEmailBeginViewTestCase(APITransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="emmypresh777@gmail.com", password="Adm1!n123"
        )
        JWTAccessToken.objects.create(user=self.user)
        self.url = reverse("user:verify-email-begin")

    def test_verify_email_begin_success(self):
        response = self.client.post(self.url, data={"email": self.user.email})
        self.assertEqual(
            "A verfication link has been sent to your email address.",
            response.data["message"],
        )
        self.assertEqual(response.data["is_email_sent"], True)
        self.assertTrue(self.user.otp)

    def test_verify_email_begin_failure(self):
        for i in range(2):
            response = self.client.post(self.url, data={"email": self.user.email})
        self.assertEqual(
            "Check your email for an already existing verification link.", response.data
        )


def tearDown(self) -> None:
    sleep(1)


class LoginViewTestCase(APITransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="admin@gmail.com", password="Adm1!n123"
        )
        JWTAccessToken.objects.create(user=self.user)
        self.user2 = User.objects.create_user(
            email="admin2@gmail.com", password="Adm1!n123", is_email_verified=True
        )
        JWTAccessToken.objects.create(user=self.user2)
        self.login_url = reverse("user:login")

    def test_login_success(self):
        response = self.client.post(
            self.login_url, data={"email": self.user2.email, "password": "Adm1!n123"}
        )
        for string in ["id", "email", "username", "access", "refresh"]:
            self.assertIn(string, response.data)

    def test_login_failure_unverified_email(self):
        response = self.client.post(
            self.login_url, data={"email": self.user.email, "password": "Adm1!n123"}
        )
        self.assertEqual(
            "Click the link sent to your email to verify your account, or request a new one to proceed.",
            response.data,
        )

    def test_login_failure_missing_credentials(self):
        response = self.client.post(
            self.login_url,
        )
        self.assertEqual(
            ["Email field is required.", "Password field is required."], response.data
        )

    def test_login_failure_invalid_credentials(self):
        response = self.client.post(
            self.login_url, data={"email": "admin1@gmail.com", "password": "Adm1!n123"}
        )
        self.assertEqual(
            "No active account found with the given credentials.", response.data
        )

    def tearDown(self) -> None:
        sleep(1)


class RefreshViewTestCase(APITransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="admin@gmail.com", password="Adm1!n123", is_email_verified=True
        )
        JWTAccessToken.objects.create(user=self.user)
        self.register_url = reverse("user:register")
        self.token = self.client.post(
            reverse("user:login"),
            data={"email": self.user.email, "password": "Adm1!n123"},
        ).data["access"]
        self.refresh_url = reverse("user:refresh")

    def test_refresh_success(self):
        response = self.client.post(
            self.refresh_url, headers={"Authorization": f"Bearer {self.token}"}
        )
        for string in ["id", "email", "username", "access", "refresh"]:
            self.assertIn(string, response.data)

    def tearDown(self) -> None:
        sleep(1)


class LogoutViewTestCase(APITransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="admin@gmail.com", password="Adm1!n123", is_email_verified=True
        )
        JWTAccessToken.objects.create(user=self.user)
        self.register_url = reverse("user:register")
        self.token = self.client.post(
            reverse("user:login"),
            data={"email": self.user.email, "password": "Adm1!n123"},
        ).data["access"]
        self.logout_url = reverse("user:logout")

    def test_logout_success(self):
        response = self.client.post(
            self.logout_url, headers={"Authorization": f"Bearer {self.token}"}
        )
        self.assertEqual("Logout successful.", response.data)

    def test_logout_failure_invalid_token(self):
        response = self.client.post(
            self.logout_url, headers={"Authorization": "Bearer invalid_token"}
        )
        self.assertEqual("Token is invalid or expired.", response.data)

    def tearDown(self) -> None:
        sleep(1)


class LogoutViewTestCase(APITransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="admin@gmail.com", password="Adm1!n123", is_email_verified=True
        )
        JWTAccessToken.objects.create(user=self.user)
        self.register_url = reverse("user:register")
        self.token = self.client.post(
            reverse("user:login"),
            data={"email": self.user.email, "password": "Adm1!n123"},
        ).data["access"]
        self.logout_url = reverse("user:logout")

    def test_logout_success(self):
        response = self.client.post(
            self.logout_url, headers={"Authorization": f"Bearer {self.token}"}
        )
        self.assertEqual("Logout successful.", response.data)

    def test_logout_failure_invalid_token(self):
        response = self.client.post(
            self.logout_url, headers={"Authorization": "Bearer invalid_token"}
        )
        self.assertEqual("Token is invalid or expired.", response.data)

    def tearDown(self) -> None:
        sleep(1)


class UserListViewTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="admin@gmail.com", password="Adm1!n123", is_email_verified=True
        )
        JWTAccessToken.objects.create(user=self.user)
        self.token = self.client.post(
            reverse("user:login"),
            data={"email": self.user.email, "password": "Adm1!n123"},
        ).data["access"]
        self.url = reverse("user:user-list")

    def test_retrieve_user_list_success(self):
        response = self.client.get(
            self.url, headers={"Authorization": f"Bearer {self.token}"}
        )
        self.assertTrue(list, type(response.data))
        for string in ["id", "email", "username"]:
            self.assertIn(string, response.data[0])

    def test_retrieve_user_list_failure(self):
        response = self.client.get(self.url)
        self.assertEqual(
            "Authentication credentials were not provided..", response.data
        )

    def tearDown(self) -> None:
        sleep(1)


class UserDetailViewTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="admin@gmail.com", password="Adm1!n123", is_email_verified=True
        )
        self.user2 = User.objects.create_user(
            email="admin2@gmail.com", password="Adm1!n123", is_email_verified=True
        )
        JWTAccessToken.objects.create(user=self.user)
        self.token = self.client.post(
            reverse("user:login"),
            data={"email": self.user.email, "password": "Adm1!n123"},
        ).data["access"]
        self.url = reverse("user:user-detail", kwargs={"user_id": self.user.id})

    def test_retrieve_user_detail_success(self):
        response = self.client.get(
            self.url, headers={"Authorization": f"Bearer {self.token}"}
        )
        for string in ["id", "email", "username"]:
            self.assertIn(string, response.data)

    def test_retrieve_user_detail_failure_nonexistent(self):
        response = self.client.get(
            reverse(
                "user:user-detail",
                kwargs={"user_id": "4ac07c02-bf7b-4789-aa38-42a434e7312e"},
            ),
            headers={"Authorization": f"Bearer {self.token}"},
        )
        self.assertEqual("User with this id does not exist.", response.data)

    def test_retrieve_user_detail_failure_invalid(self):
        response = self.client.get(
            reverse(
                "user:user-detail",
                kwargs={"user_id": "invalid-bf7b-4789-aa38-id"},
            ),
            headers={"Authorization": f"Bearer {self.token}"},
        )
        self.assertEqual(
            "“invalid-bf7b-4789-aa38-id” is not a valid UUID.", response.data
        )

    def test_update_user_detail_success(self):
        response = self.client.put(
            self.url,
            data={"username": "admin"},
            headers={"Authorization": f"Bearer {self.token}"},
        )
        self.assertEqual("admin", response.data["username"])

    def test_update_userr_profile_detail_failure_permission_denied(self):
        UserProfile.objects.create(user=self.user2)
        response = self.client.put(
            reverse("user:user-profile-detail", kwargs={"user_id": self.user2.id}),
            data={"username": "admin"},
            headers={"Authorization": f"Bearer {self.token}"},
        )
        self.assertEqual(
            "You do not have permission to perform this action.", response.data
        )

    def tearDown(self) -> None:
        sleep(1)


class UserProfileListViewTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="admin@gmail.com", password="Adm1!n123", is_email_verified=True
        )
        UserProfile.objects.create(user=self.user)
        JWTAccessToken.objects.create(user=self.user)
        self.token = self.client.post(
            reverse("user:login"),
            data={"email": self.user.email, "password": "Adm1!n123"},
        ).data["access"]
        self.url = reverse("user:user-profile-list")

    def test_retrieve_user_profile_list_success(self):
        response = self.client.get(
            self.url, headers={"Authorization": f"Bearer {self.token}"}
        )
        self.assertTrue(list, type(response.data))
        for string in ["id", "username", "gender", "user"]:
            self.assertIn(string, response.data[0])

    def test_retrieve_user_profile_list_failure(self):
        response = self.client.get(self.url)
        self.assertEqual(
            "Authentication credentials were not provided..", response.data
        )

    def tearDown(self) -> None:
        sleep(1)


class UserProfileDetailViewTestCase(APITransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="admin@gmail.com", password="Adm1!n123", is_email_verified=True
        )
        self.user2 = User.objects.create_user(
            email="admin2@gmail.com", password="Adm1!n123", is_email_verified=True
        )
        JWTAccessToken.objects.create(user=self.user)
        self.token = self.client.post(
            reverse("user:login"),
            data={"email": self.user.email, "password": "Adm1!n123"},
        ).data["access"]
        self.url = reverse("user:user-profile-detail", kwargs={"user_id": self.user.id})

    def test_retrieve_user_profile_detail_success(self):
        UserProfile.objects.create(user=self.user)
        response = self.client.get(
            self.url, headers={"Authorization": f"Bearer {self.token}"}
        )
        for string in ["id", "username", "gender", "user"]:
            self.assertIn(string, response.data)

    def test_retrieve_user_profile_detail_failure_nonexistent(self):
        response = self.client.get(
            reverse(
                "user:user-profile-detail",
                kwargs={"user_id": "4ac07c02-bf7b-4789-aa38-42a434e7312e"},
            ),
            headers={"Authorization": f"Bearer {self.token}"},
        )
        self.assertEqual("User with this id does not exist.", response.data)

        response2 = self.client.get(
            self.url, headers={"Authorization": f"Bearer {self.token}"}
        )
        self.assertEqual("User has no profile.", response2.data)

    def test_retrieve_user_profile_detail_failure_invalid(self):
        response = self.client.get(
            reverse(
                "user:user-profile-detail",
                kwargs={"user_id": "invalid-bf7b-4789-aa38-id"},
            ),
            headers={"Authorization": f"Bearer {self.token}"},
        )
        self.assertEqual(
            "“invalid-bf7b-4789-aa38-id” is not a valid UUID.", response.data
        )

    def test_update_user_profile_detail_success(self):
        UserProfile.objects.create(user=self.user)
        image_file = settings.BASE_DIR / "test-image/whisper.png"
        with open(image_file, "rb") as image:
            image_file_data = SimpleUploadedFile(
                "whisper.png", image.read(), content_type="image/png"
            )
            data = {
                "display_name": "John Doe",
                "bio": "Not a robot",
                "avatar": image_file_data,
                "gender": "MALE",
                "nationality": "UK",
            }
            response = self.client.put(
                self.url, data=data, headers={"Authorization": f"Bearer {self.token}"}
            )
        self.assertEqual(
            all(
                [
                    response.data["display_name"] == "John Doe",
                    response.data["bio"] == "Not a robot",
                    response.data["avatar"] != "",
                    response.data["gender"] == "MALE",
                    response.data["nationality"] == "UK",
                ]
            ),
            True,
        )

    def test_update_user_profile_detail_failure_invalid_data(self):
        UserProfile.objects.create(user=self.user)
        response = self.client.put(
            reverse("user:user-profile-detail", kwargs={"user_id": self.user.id}),
            data={"nationality": "MARS"},
            headers={"Authorization": f"Bearer {self.token}"},
        )
        self.assertEqual('"MARS" is not a valid choice.', response.data)

    def test_update_user_profile_detail_failure_permission_denied(self):
        UserProfile.objects.create(user=self.user2)
        response = self.client.put(
            reverse("user:user-profile-detail", kwargs={"user_id": self.user2.id}),
            data={"nationality": "MARS"},
            headers={"Authorization": f"Bearer {self.token}"},
        )
        self.assertEqual(
            "You do not have permission to perform this action.", response.data
        )

    def tearDown(self) -> None:
        sleep(1)
