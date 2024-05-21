import os

import requests
from django.conf import settings
from django.contrib.sessions.models import Session
from django.db import models
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from ldap3 import ALL, SUBTREE, Connection, Server
from msal import ConfidentialClientApplication
from rest_framework import generics, status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from abstract.views import (
    SimpleCreateGenericView,
    SimpleDeleteOneGenericView,
    SimpleGetDetailGenericView,
    SimpleGetListGenericView,
    SimplePartialUpdateGenericView,
    SimplePostGenericView,
    SimpleUpdateGenericView,
)
from Castellum.permissions import IsOrganization
from users.models import AuthorizedDomain, Employee, Organization, User
from users.models.organization import DeliverabilityTest

from .arch.managers import (
    AddEmployeeManager,
    AllowlistingManager,
    AuthorizedDomainManager,
    ChangePasswordManager,
    DeactivateDepartmentsManager,
    DeactivateEmployeesManager,
    DepartmentManager,
    EmployeeUpdateManager,
    EnrollmentAndNotificationsSettingsManager,
    ForgotPasswordTriggerManager,
    OrganizationDashboardManager,
    PhishingPermissionCheckManager,
    PhishingReportEmailManager,
    ResendActivationLinkOrgManager,
    ResetPasswordManager,
    SetCutOffScoreManager,
    Step1RegisterOrgManager,
    Step2RegisterOrgManager,
    UserFileImportManager,
    VerifyRegisterTokenOrgManager,
)
from .models import Department, Employee, EmployeeProfile
from .serializers import (
    DeliverabilityTestSerializer,
    EmployeeSerializer,
    OrganizationSerializer,
    UserLoginSerializer,
)

load_dotenv()


@extend_schema_view(
    post=extend_schema(
        summary="Register Organization - Step 1",
        description="Register an organization - Step 1",
    ),
)
class Step1RegisterOrgView(SimpleCreateGenericView):
    serializer_class = Step1RegisterOrgManager


@extend_schema_view(
    post=extend_schema(
        summary="Verify Register Token - Organization",
        description="Verify the register token of an organization",
    ),
)
class VerifyRegisterTokenOrgView(SimpleCreateGenericView):
    serializer_class = VerifyRegisterTokenOrgManager


@extend_schema_view(
    post=extend_schema(
        summary="Register Organization - Step 2",
        description="Register an organization - Step 2",
    ),
)
class Step2RegisterOrgView(SimpleCreateGenericView):
    serializer_class = Step2RegisterOrgManager


@extend_schema_view(
    post=extend_schema(
        summary="Resend Activation Link - Organization",
        description="Resend the activation link of an organization",
    ),
)
class ResendActivationLinkOrgView(SimpleCreateGenericView):
    serializer_class = ResendActivationLinkOrgManager


@extend_schema_view(
    post=extend_schema(
        summary="Login",
        description="Login User",
    ),
)
class LoginView(generics.GenericAPIView):
    serializer_class = UserLoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema_view(
    get=extend_schema(
        summary="Organization Profile",
        description="Get the profile of the authenticated organization",
    )
)
class OrganizationProfileView(SimpleGetDetailGenericView):
    serializer_class = OrganizationSerializer
    permission_classes = [IsOrganization]
    queryset = Organization.objects.all()

    def get_object(self):
        return self.request.user


@extend_schema_view(
    post=extend_schema(
        summary="User File Import",
        description="Import users from a file",
    ),
)
class UserFileImportView(SimpleCreateGenericView):
    serializer_class = UserFileImportManager
    permission_classes = [IsOrganization]
    parser_classes = [MultiPartParser, FormParser]


@extend_schema_view(
    post=extend_schema(
        summary="Add Employee",
        description="Add an employee",
    ),
)
class AddEmployeeView(SimpleCreateGenericView):
    permission_classes = [IsOrganization]
    serializer_class = AddEmployeeManager


@extend_schema_view(
    get=extend_schema(
        summary="Employees List",
        description="Get a list of all employees",
        parameters=[
            OpenApiParameter(
                name="query",
                type=str,
                required=False,
                description="Search for employees by first name, last name, email or department name",
            )
        ],
    ),
)
class EmployeesListView(SimpleGetListGenericView):
    """
    Add "query" to query params to search for employees by first name, last name, email or department name
    """

    permission_classes = [IsOrganization]
    serializer_class = EmployeeSerializer
    queryset = Employee.objects.prefetch_related("emp_profile").all()

    def get_queryset(self):
        queryset = self.queryset.filter(emp_profile__organization=self.request.user)
        query = self.request.query_params.get("query")
        if query:
            queryset = queryset.filter(
                models.Q(emp_profile__first_name__icontains=query)
                | models.Q(emp_profile__last_name__icontains=query)
                | models.Q(email__icontains=query)
                | models.Q(emp_profile__department__name__icontains=query)
            )
        return queryset


@extend_schema_view(
    get=extend_schema(
        summary="Employees Paginated List",
        description="Get a paginated list of all employees",
        parameters=[
            OpenApiParameter(
                name="query",
                type=str,
                required=False,
                description="Search for employees by first name, last name, email or department name",
            )
        ],
    ),
)
class EmployeesPaginatedListView(generics.ListAPIView):
    """
    Add "query" to query params to search for employees by first name, last name, email or department name
    """

    permission_classes = [IsOrganization]
    serializer_class = EmployeeSerializer
    queryset = Employee.objects.prefetch_related("emp_profile").all()

    def get_queryset(self):
        return self.queryset.prefetch_related("emp_profile").filter(
            emp_profile__organization=self.request.user
        )

    def filter_queryset(self, queryset):
        query = self.request.query_params.get("query")
        if query:
            queryset = queryset.filter(
                models.Q(emp_profile__first_name__icontains=query)
                | models.Q(emp_profile__last_name__icontains=query)
                | models.Q(email__icontains=query)
                | models.Q(emp_profile__department__name__icontains=query)
            )
        return queryset


@extend_schema_view(
    post=extend_schema(
        summary="Deactivate Employees",
        description="Deactivate employees",
    ),
)
class DeactivateEmployeesView(SimpleCreateGenericView):
    permission_classes = [IsOrganization]
    serializer_class = DeactivateEmployeesManager
    queryset = Employee.objects.all()


@extend_schema_view(
    post=extend_schema(
        summary="Delete Departments",
        description="Delete departments",
    ),
)
class DeleteDepartmentsView(SimplePostGenericView):
    permission_classes = [IsOrganization]
    serializer_class = DeactivateDepartmentsManager
    queryset = Department.objects.all()

    def get_queryset(self):
        return self.queryset.filter(organization=self.request.user)


@extend_schema_view(
    get=extend_schema(
        summary="Department List",
        description="Get a list of all departments",
        parameters=[
            OpenApiParameter(
                name="name",
                type=str,
                required=False,
                description="Search for departments by name",
            )
        ],
    ),
    post=extend_schema(
        summary="Create Department",
        description="Create a department",
    ),
)
class DepartmentView(generics.ListCreateAPIView):
    """
    add "name" to query params to search for department
    """

    permission_classes = [IsOrganization]
    serializer_class = DepartmentManager
    queryset = Department.objects.all()

    def filter_queryset(self, queryset):
        name = self.request.query_params.get("name")
        if name:
            queryset = queryset.filter(name__icontains=name.lower())
        return queryset

    def get_queryset(self):
        return self.request.user.departments.all()


@extend_schema_view(
    get=extend_schema(
        summary="Department Detail",
        description="Get the details of a department",
    ),
    patch=extend_schema(
        summary="Update Department",
        description="Update a department",
    ),
    delete=extend_schema(
        summary="Delete Department",
        description="Delete a department",
    ),
)
class DetailDepartmentView(
    SimplePartialUpdateGenericView,
    SimpleDeleteOneGenericView,
    SimpleGetDetailGenericView,
):
    permission_classes = [IsOrganization]
    serializer_class = DepartmentManager
    queryset = Department.objects.all()

    def get_queryset(self):
        return self.queryset.filter(organization=self.request.user)


@extend_schema_view(
    patch=extend_schema(
        summary="Update Employee",
        description="Update an employee",
    ),
)
class EmployeeUpdateView(SimplePartialUpdateGenericView):
    permission_classes = [IsOrganization]
    serializer_class = EmployeeUpdateManager
    lookup_field = "id"
    queryset = Employee.objects.prefetch_related("emp_profile").all()

    def get_queryset(self):
        return self.queryset.filter(emp_profile__organization=self.request.user)


@extend_schema_view(
    post=extend_schema(
        summary="Forgot Password Trigger",
        description="Trigger a forgot password email",
    ),
)
class ForgotPasswordTriggerView(SimpleCreateGenericView):
    permission_classes = [AllowAny]
    serializer_class = ForgotPasswordTriggerManager


@extend_schema_view(
    patch=extend_schema(
        summary="Reset Password",
        description="Reset a password",
    ),
)
class ResetPasswordView(SimpleUpdateGenericView):
    permission_classes = [AllowAny]
    serializer_class = ResetPasswordManager
    queryset = User.objects.all()
    lookup_field = "token"
    lookup_url_kwarg = "token"


@extend_schema_view(
    patch=extend_schema(
        summary="Change Password",
        description="Change the password of the authenticated user",
    ),
)
class ChangePasswordView(SimpleUpdateGenericView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordManager

    def get_object(self):
        return self.request.user


@extend_schema_view(
    get=extend_schema(
        summary="Get Cut Off Score",
        description="Get the cut off score of the authenticated organization",
    ),
    patch=extend_schema(
        summary="Set Cut Off Score",
        description="Set the cut off score of the authenticated organization",
    ),
)
class SetCutOffScoreView(SimpleUpdateGenericView, SimpleGetDetailGenericView):
    permission_classes = [IsOrganization]
    serializer_class = SetCutOffScoreManager
    queryset = Organization.objects.all()
    lookup_field = None
    lookup_url_kwarg = None

    def get_object(self):
        return self.request.user.org_profile


@extend_schema_view(
    get=extend_schema(
        summary="Enrollment and Notifications Settings",
        description="Get the enrollment and notifications settings of the authenticated organization",
    ),
    patch=extend_schema(
        summary="Update Enrollment and Notifications Settings",
        description="Update the enrollment and notifications settings of the authenticated organization",
    ),
)
class EnrollmentAndNotificationsSettingsView(
    SimpleGetDetailGenericView, SimplePartialUpdateGenericView
):

    permission_classes = [IsOrganization]
    serializer_class = EnrollmentAndNotificationsSettingsManager
    queryset = Organization.objects.all()

    def get_object(self):
        return self.request.user.org_profile


@extend_schema_view(
    get=extend_schema(
        summary="Phishing Report Email",
        description="Get the phishing report email settings of the authenticated organization",
    ),
    patch=extend_schema(
        summary="Update Phishing Report Email",
        description="Update the phishing report email settings of the authenticated organization",
    ),
)
class PhishingReportEmailView(
    SimpleGetDetailGenericView, SimplePartialUpdateGenericView
):

    permission_classes = [IsOrganization]
    serializer_class = PhishingReportEmailManager
    queryset = Organization.objects.all()

    def get_object(self):
        return self.request.user.org_profile


@extend_schema_view(
    get=extend_schema(
        summary="Allowlisting Settings",
        description="Get the allowlisting settings of the authenticated organization",
    ),
)
class AllowlistingSettingsView(SimpleGetDetailGenericView):
    permission_classes = [IsOrganization]
    serializer_class = AllowlistingManager
    queryset = Organization.objects.all()
    lookup_field = None
    lookup_url_kwarg = None

    def get_object(self):
        return self.request.user


@extend_schema_view(
    post=extend_schema(
        summary="Add Authorized Domain",
        description="Add an authorized domain",
    ),
    get=extend_schema(
        summary="Authorized Domain List",
        description="Get a list of all authorized domains",
    ),
)
class AuthorizedDomainView(SimpleCreateGenericView, SimpleGetListGenericView):
    permission_classes = [IsOrganization]
    queryset = AuthorizedDomain.objects.all()
    serializer_class = AuthorizedDomainManager

    def get_queryset(self):
        return self.queryset.filter(organization=self.request.user)


@extend_schema_view(
    delete=extend_schema(
        summary="Delete Authorized Domain",
        description="Delete an authorized domain",
    ),
)
class DetailedAuthorizedDomainView(SimpleDeleteOneGenericView):
    permission_classes = [IsOrganization]
    queryset = AuthorizedDomain.objects.all()

    def get_queryset(self):
        return self.queryset.filter(organization=self.request.user)


@extend_schema_view(
    patch=extend_schema(
        summary="Verify Authorized Domain",
        description="Verify an authorized domain",
    ),
)
class VerifyAuthorizedDomainView(SimpleUpdateGenericView):
    permission_classes = [IsOrganization]
    queryset = AuthorizedDomain.objects.all()
    lookup_field = "verification_token"
    lookup_url_kwarg = "id"

    def get_queryset(self):
        return self.queryset.filter(organization=self.request.user)

    def patch(self, request, *args, **kwargs):
        instance: AuthorizedDomain = self.get_object()
        instance.verify_domain()
        return Response(
            {"message": "Domain verified successfully"},
            status=status.HTTP_200_OK,
        )


@extend_schema_view(
    patch=extend_schema(
        summary="Resend Authorized Domain Verification Email",
        description="Resend the authorized domain verification email",
    ),
)
class ResendAuthorizedDomainVerificationEmailView(SimpleUpdateGenericView):
    permission_classes = [IsOrganization]
    # serializer_class = ResendAuthorizedDomainVerificationEmailManager
    queryset = AuthorizedDomain.objects.all()
    lookup_field = "id"

    def get_queryset(self):
        return self.queryset.filter(organization=self.request.user)

    def patch(self, request, *args, **kwargs):
        instance: AuthorizedDomain = self.get_object()
        instance.send_domain_verification_email()
        return Response(
            {"message": "Verification email sent successfully"},
            status=status.HTTP_200_OK,
        )


@extend_schema_view(
    get=extend_schema(
        summary="Deliverability Test List",
        description="Get a list of all deliverability tests",
    ),
    post=extend_schema(
        summary="Create Deliverability Test",
        description="Create a deliverability test",
    ),
)
class CreateListDeliverabilityTestView(generics.ListCreateAPIView):
    permission_classes = [IsOrganization]
    queryset = DeliverabilityTest.objects.all()
    serializer_class = DeliverabilityTestSerializer

    def get_queryset(self):
        return self.request.user.deliverability_tests.all()


@extend_schema_view(
    delete=extend_schema(
        summary="Delete Deliverability Test",
        description="Delete a deliverability test",
    ),
)
class DetailedDeliverabilityTestView(generics.DestroyAPIView):
    permission_classes = [IsOrganization]
    queryset = DeliverabilityTest.objects.all()
    serializer_class = DeliverabilityTestSerializer

    def get_queryset(self):
        return self.request.user.deliverability_tests.all()


@extend_schema_view(
    patch=extend_schema(
        summary="Verify Deliverability Test",
        description="Verify a deliverability test",
    ),
)
class VerifyDeliverabilityTestView(SimpleUpdateGenericView):
    permission_classes = [IsOrganization]
    queryset = DeliverabilityTest.objects.all()
    lookup_field = "verification_token"
    lookup_url_kwarg = "id"

    def get_queryset(self):
        return self.request.user.deliverability_tests.all()

    def patch(self, request, *args, **kwargs):
        instance: DeliverabilityTest = self.get_object()
        instance.verify_domain()
        return Response(
            {"message": "Deliverability Tests verified successfully"},
            status=status.HTTP_200_OK,
        )


@extend_schema_view(
    get=extend_schema(
        summary="Organization Dashboard",
        description="Get the dashboard of the authenticated organization",
    ),
)
class OrganizationDashboardView(SimpleGetDetailGenericView):
    serializer_class = OrganizationDashboardManager
    permission_classes = [IsOrganization]
    queryset = Organization.objects.all()

    def get_object(self):
        return self.request.user


@extend_schema_view(
    get=extend_schema(
        summary="Get Phishing Permissions", description="Get Phishing Permissions"
    )
)
class PhishingPermissionCheckView(SimpleGetDetailGenericView):
    permission_classes = [IsOrganization]
    queryset = Organization.objects.all()
    serializer_class = PhishingPermissionCheckManager

    def get_object(self):
        return self.request.user


@method_decorator(csrf_exempt, name="dispatch")
class ImportADUsersView(APIView):
    def post(self, request, *args, **kwargs):
        server_address = "192.168.1.4"
        admin_bind_dn = "ethnosng.com"
        password = "th3nextLEVEL."
        search_base = "dc= ethnosng, dc= com"

        if not all([server_address, admin_bind_dn, password, search_base]):
            return JsonResponse(
                {"error": "Missing required AD server details"}, status=400
            )

        return self.import_users(server_address, admin_bind_dn, password, search_base)

    def get_ldap_connection(self, server_address, admin_bind_dn, password):
        server = Server(server_address, get_info=ALL)
        connection = Connection(server, admin_bind_dn, password, auto_bind=True)
        return connection

    def import_users(self, server_address, admin_bind_dn, password, search_base):
        connection = self.get_ldap_connection(server_address, admin_bind_dn, password)
        if not connection.bind():
            return JsonResponse({"error": "Failed to bind to AD server"}, status=400)

        search_filter = "(objectClass=user)"
        attributes = ["givenName", "sn", "mail"]

        connection.search(search_base, search_filter, SUBTREE, attributes=attributes)

        default_organization = "NIL"
        default_department = "NIL"

        for entry in connection.entries:
            email = entry.mail.value if entry.mail else None
            if email:
                employee, created = Employee.objects.update_or_create(
                    email=email,
                    defaults={
                        "first_name": entry.givenName.value if entry.givenName else "",
                        "last_name": entry.sn.value if entry.sn else "",
                        "is_active": True,
                    },
                )

                EmployeeProfile.objects.update_or_create(
                    employee=employee,
                    defaults={
                        "first_name": entry.givenName.value if entry.givenName else "",
                        "last_name": entry.sn.value if entry.sn else "",
                        "organization": default_organization,
                        "department": default_department,
                    },
                )

        return Response({"status": "completed", "imported": len(connection.entries)})


redirect_url = os.environ.get("REDIRECT_PATH")


class AzureADSignInAPIView(APIView):
    def get(self, request):
        app = ConfidentialClientApplication(
            settings.AZURE_AD["CLIENT_ID"],
            authority=settings.AZURE_AD["AUTHORITY"],
            client_credential=settings.AZURE_AD["CLIENT_SECRET"],
        )

        redirect_uri = redirect_url

        auth_url = app.get_authorization_request_url(
            settings.AZURE_AD["SCOPE"],
            redirect_uri=redirect_uri,
        )

        return Response({"auth_url": auth_url})


class AzureADCallbackAPIView(APIView):
    def get(self, request):
        code = request.query_params.get("code")
        if not code:
            raise AuthenticationFailed("Authorization code not provided")

        app = ConfidentialClientApplication(
            settings.AZURE_AD["CLIENT_ID"],
            authority=settings.AZURE_AD["AUTHORITY"],
            client_credential=settings.AZURE_AD["CLIENT_SECRET"],
        )

        redirect_uri = redirect_url

        token_response = app.acquire_token_by_authorization_code(
            code, scopes=settings.AZURE_AD["SCOPE"], redirect_uri=redirect_uri
        )

        if "error" in token_response:
            raise AuthenticationFailed(token_response.get("error_description"))

        token = token_response["access_token"]
        headers = {"Authorization": "Bearer " + token}
        user_profile_response = requests.get(
            "https://graph.microsoft.com/v1.0/me", headers=headers
        )
        user_profile_data = user_profile_response.json()

        if user_profile_data.get("jobTitle") == "Organization Admin":
            users_response = requests.get(
                "https://graph.microsoft.com/v1.0/users", headers=headers
            )
            users_data = users_response.json().get("value", [])

            for user in users_data:
                first_name, last_name = user.get("displayName").split(" ", 1)
                email = user.get("mail") or user.get("userPrincipalName")
                department = "Nil"
                user_data = {
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": email,
                    "department": department,
                }

                serializer = AddEmployeeManager(
                    data=user_data, context={"request": request}
                )
                if serializer.is_valid():
                    serializer.save()
                else:
                    print("Failed to add user:", serializer.errors)

            return Response({"message": "Users imported successfully"})
        else:
            return Response(
                {"message": "User authenticated successfully", "token": token_response}
            )


class ImportOktaUsers(APIView):
    permission_classes = [IsOrganization]

    def get_all_okta_users(self, url, headers):
        users = []
        while url:
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Ensure to handle HTTP errors appropriately
            page_users = response.json()
            users.extend(page_users)
            links = response.links
            url = links["next"]["url"] if "next" in links else None
        return users

    def get(self, request, *args, **kwargs):
        url = f"{settings.OKTA_DOMAIN}/api/v1/users"
        headers = {
            "Authorization": f"SSWS {settings.OKTA_API_TOKEN}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        try:
            users = self.get_all_okta_users(url, headers)
            simplified_users = [
                {
                    "email": user["profile"]["email"],
                    "first_name": user["profile"]["firstName"],
                    "last_name": user["profile"]["lastName"],
                }
                for user in users
            ]
            # Store in session for subsequent import
            request.session["okta_users"] = simplified_users
            return Response(simplified_users)
        except requests.exceptions.RequestException as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request, *args, **kwargs):
        users = request.session.get("okta_users", [])
        if not users:
            return Response(
                {"error": "No users to import. Please preview users first."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        imported_users = []
        errors = []
        for user_data in users:
            serializer = AddEmployeeManager(
                data=user_data, context={"request": request}
            )
            if serializer.is_valid():
                serializer.save()
                imported_users.append(serializer.validated_data)
            else:
                errors.append(serializer.errors)

        del request.session["okta_users"]

        if errors:
            return Response(
                {"imported_users": imported_users, "errors": errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "message": "Users imported successfully",
                "imported_users": imported_users,
            },
            status=status.HTTP_200_OK,
        )
