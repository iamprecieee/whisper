from django.db.transaction import atomic
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.parsers import MultiPartParser, JSONParser
from rest_framework.exceptions import NotFound
from .serializers import (
    RegisterSerializer,
    VerifyEmailCompleteSerializer,
    VerifyEmailBeginSerializer,
    LoginSerializer,
    RefreshTokenSerializer,
    UserSerializer,
    UserProfileSerializer,
)
from .refresh import SessionRefreshToken
from .models import User, UserProfile
from portal.permissions import isCurrentUserOrReadOnly


class RegisterView(APIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            with atomic():
                user_data = serializer.save()
                response_data = self.serializer_class(user_data).data
                return Response(response_data, status=status.HTTP_201_CREATED)


class VerifyEmailCompleteView(APIView):
    permission_classes = [AllowAny]
    serializer_class = VerifyEmailCompleteSerializer

    def post(self, request, token):
        serializer = self.serializer_class(data={"token": token})
        if serializer.is_valid(raise_exception=True):
            with atomic():
                user_data = serializer.save()
                response_data = self.serializer_class(user_data).data
                return Response(
                    response_data,
                    status=status.HTTP_200_OK,
                )


class VerifyEmailBeginView(APIView):
    permission_classes = [AllowAny]
    serializer_class = VerifyEmailBeginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            with atomic():
                response_data = serializer.save()
                return Response(
                    response_data,
                    status=status.HTTP_200_OK,
                )


class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    alt_serializer_class = (
        LoginSerializer  # Will be used to serialize login data (including id, email)
    )

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            login_data = serializer.validated_data
            login_data["email"] = request.data["email"]
            alt_serializer = self.alt_serializer_class(
                data=login_data, context={"request": request}
            )
            if alt_serializer.is_valid(raise_exception=True):
                with atomic():
                    jwt_data = alt_serializer.save()
                    response_data = self.alt_serializer_class(jwt_data).data
                    return Response(response_data, status=status.HTTP_200_OK)


class RefreshView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = RefreshTokenSerializer

    def post(self, request):
        serializer = self.serializer_class(context={"request": request})
        with atomic():
            data = serializer.save()
            response_data = self.serializer_class(data).data
            return Response(response_data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        refresh_session_instance = SessionRefreshToken(request)
        refresh_session_instance.remove_token()
        return Response("Logout successful.", status=status.HTTP_200_OK)


class UserListView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    serializer_class = UserSerializer

    def get(self, request):
        users = User.objects.all()
        users_data = self.serializer_class(users, many=True).data
        return Response(users_data, status=status.HTTP_200_OK)


class UserDetailView(APIView):
    permission_classes = [IsAuthenticated, isCurrentUserOrReadOnly]
    authentication_classes = [JWTAuthentication]
    serializer_class = UserSerializer

    def get(self, request, user_id):
        user = User.objects.filter(id=user_id).first()
        if user:
            user_data = self.serializer_class(user).data
            return Response(user_data, status=status.HTTP_200_OK)
        else:
            raise NotFound("User with this id does not exist.")

    def put(self, request, user_id):
        user = User.objects.filter(id=user_id).first()
        if user:
            serializer = self.serializer_class(user, data=request.data, partial=True)
            if serializer.is_valid(raise_exception=True):
                with atomic():
                    weaver_data = serializer.save()
                    response_data = self.serializer_class(weaver_data).data
                    return Response(response_data, status=status.HTTP_202_ACCEPTED)
        else:
            raise NotFound("User with this id does not exist.")


class UserProfileListView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    serializer_class = UserProfileSerializer

    def get(self, request):
        user_profiles = UserProfile.objects.all()
        user_profiles_data = self.serializer_class(user_profiles, many=True).data
        return Response(user_profiles_data, status=status.HTTP_200_OK)


class UserProfileDetailView(APIView):
    permission_classes = [IsAuthenticated, isCurrentUserOrReadOnly]
    authentication_classes = [JWTAuthentication]
    serializer_class = UserProfileSerializer
    parser_classes = [MultiPartParser, JSONParser]

    def get(self, request, user_id):
        user = User.objects.select_related("profile").filter(id=user_id).first()
        if user:
            user_profile = user.profile
            user_profile_data = self.serializer_class(user_profile).data
            return Response(user_profile_data, status=status.HTTP_200_OK)
        else:
            raise NotFound("User with this id does not exist.")

    def put(self, request, user_id):
        user = User.objects.select_related("profile").filter(id=user_id).first()
        if user:
            user_profile = user.profile
            if user_profile:
                serializer = self.serializer_class(
                    user_profile, data=request.data, partial=True
                )
                if serializer.is_valid(raise_exception=True):
                    with atomic():
                        user_profile_data = serializer.save()
                        response_data = self.serializer_class(user_profile_data).data
                        return Response(response_data, status=status.HTTP_202_ACCEPTED)
            else:
                raise NotFound("User does not have existing profile.")
        else:
            raise NotFound("User with this id does not exist.")
