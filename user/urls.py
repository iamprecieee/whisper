from django.urls import path
from .views import (
    RegisterView,
    VerifyEmailCompleteView,
    VerifyEmailBeginView,
    LoginView,
    RefreshView,
    LogoutView,
    UserListView,
    UserDetailView,
    UserProfileListView,
    UserProfileDetailView,
)


app_name = "user"
urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path(
        "verify-email/complete/<str:token>/",
        VerifyEmailCompleteView.as_view(),
        name="verify-email-complete",
    ),
    path(
        "verify-email/begin/", VerifyEmailBeginView.as_view(), name="verify-email-begin"
    ),
    path("login/", LoginView.as_view(), name="login"),
    path("refresh/", RefreshView.as_view(), name="refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("user-list/", UserListView.as_view(), name="user-list"),
    path("user-detail/<str:user_id>/", UserDetailView.as_view(), name="user-detail"),
    path("user-profile-list/", UserProfileListView.as_view(), name="user-profile-list"),
    path(
        "user-profile-detail/<str:user_id>/",
        UserProfileDetailView.as_view(),
        name="user-profile-detail",
    ),
]
