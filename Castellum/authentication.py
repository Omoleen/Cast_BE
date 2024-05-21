from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import HTTP_HEADER_ENCODING, authentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import (
    AuthenticationFailed,
    InvalidToken,
    TokenError,
)
from rest_framework_simplejwt.settings import api_settings

# from django.conf import settings as api_settings
from Castellum.enums import Roles

User = get_user_model()


class CustomJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        header = self.get_header(request)
        if header is None:
            return None

        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)

        return self.get_user(validated_token), validated_token

    def get_user(self, validated_token):
        """
        Attempts to find and return a user using the given validated token.
        """
        try:
            user_id = validated_token[api_settings.USER_ID_CLAIM]
        except KeyError:
            raise InvalidToken(_("Token contained no recognizable user identification"))

        try:
            user = self.user_model.objects.prefetch_related(
                # "org_profile", "emp_profile",
                # "departments", "attempted_courses", "completed_contents", "answered_questions", "employee_profiles", "org_campaigns", "content", "courses",
                # "course_campaign", "course_campaign_records", "campaign_courses", "completed_campaign_contents", "phishing_campaigns","phishing_campaign_records",
                # "quiz_questions",
                # "phishing_templates"
            ).get(**{api_settings.USER_ID_FIELD: user_id})
            # match user.role:
            #     case Roles.ORGANIZATION:
            #         user = self.user_model.objects.prefetch_related(
            #             "org_profile", "departments", "attempted_courses"
            #             ).get(**{api_settings.USER_ID_FIELD: user_id})
            #     case Roles.EMPLOYEE:
            #         user = self.user_model.objects.prefetch_related(
            #             "emp_profile", "attempted_courses",
            #             ).get(**{api_settings.USER_ID_FIELD: user_id})
        except self.user_model.DoesNotExist:
            raise AuthenticationFailed(_("User not found"), code="user_not_found")

        if not user.is_active:
            raise AuthenticationFailed(_("User is inactive"), code="user_inactive")

        return user
