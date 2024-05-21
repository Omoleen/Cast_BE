from rest_framework.permissions import IsAuthenticated

from campaign.models import Campaign
from Castellum.enums import Roles
from content.models import Content
from phishing.models import PhishingTemplate
from quiz.models import Question
from users.models import Employee, Organization, User


class IsOrganization(IsAuthenticated):
    def has_permission(self, request, view):
        if super().has_permission(request, view):
            if request.user.role == Roles.ORGANIZATION:
                request.user.__class__ = Organization
                return True
        return False

    def has_object_permission(self, request, view, obj):
        if super().has_object_permission(request, view, obj):
            if isinstance(obj, Employee):
                if obj.emp_profile.organization == request.user:
                    return True
            if isinstance(obj, PhishingTemplate):
                if obj.is_public or obj.organization == request.user:
                    return True
            if obj.organization == request.user:
                return True

        return False


class IsEmployee(IsAuthenticated):
    def has_permission(self, request, view):
        if super().has_permission(request, view):
            if request.user.role == Roles.EMPLOYEE:
                request.user.__class__ = Employee
                return True
        return False

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Campaign):
            if (
                request.user.phishing_campaigns_queryset.filter(pk=obj.pk).exists()
                or request.user.course_campaigns_queryset.filter(pk=obj.pk).exists()
            ):
                return True
        if isinstance(obj, Question):
            return True
        if isinstance(obj, Content):
            return True
        else:
            if obj.emp_profile.employee == request.user:
                return True
        return False
