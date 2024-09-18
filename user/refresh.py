from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.sessions.exceptions import SessionInterrupted


class SessionRefreshToken:
    """
    For storing refresh tokens directly in session, and not having to manually input it in request data.
    """

    def __init__(self, request):
        self.session = request.session

        refresh = self.session.get(settings.REFRESH_SESSION_ID)
        if not refresh:
            refresh = self.session[settings.REFRESH_SESSION_ID] = {}

        self.refresh = refresh

    def check_token(self):
        return self.refresh.get("refresh")

    def add_token(self, refresh_token):
        self.refresh["refresh"] = refresh_token
        self.save()

    def remove_token(self):
        """
        Method for blacklisting refresh token to be removed from session.
        """
        if self.refresh.get("refresh"):
            existing_refresh_token = self.check_token()
            try:
                validated_refresh_token = RefreshToken(existing_refresh_token)
                if settings.SIMPLE_JWT["ROTATE_REFRESH_TOKENS"]:
                    if settings.SIMPLE_JWT["BLACKLIST_AFTER_ROTATION"]:
                        try:
                            validated_refresh_token.blacklist()
                        except AttributeError:
                            pass

                    validated_refresh_token.set_jti()
                    validated_refresh_token.set_exp()
                    validated_refresh_token.set_iat()

                del self.refresh["refresh"]
                self.save()
            except (TokenError, SessionInterrupted):
                # Deletes session data and regenerates a new session key
                self.session.flush()

    def save(self):
        self.session.modified = True
