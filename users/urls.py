from django.urls import path

from .views import (
    AddEmployeeView,
    AllowlistingSettingsView,
    AuthorizedDomainView,
    AzureADCallbackAPIView,
    AzureADSignInAPIView,
    ChangePasswordView,
    CreateListDeliverabilityTestView,
    DeactivateEmployeesView,
    DeleteDepartmentsView,
    DepartmentView,
    DetailDepartmentView,
    DetailedAuthorizedDomainView,
    DetailedDeliverabilityTestView,
    EmployeesListView,
    EmployeesPaginatedListView,
    EmployeeUpdateView,
    EnrollmentAndNotificationsSettingsView,
    ForgotPasswordTriggerView,
    ImportOktaUsers,
    LoginView,
    OrganizationDashboardView,
    OrganizationProfileView,
    PhishingPermissionCheckView,
    PhishingReportEmailView,
    ResendActivationLinkOrgView,
    ResendAuthorizedDomainVerificationEmailView,
    ResetPasswordView,
    SetCutOffScoreView,
    Step1RegisterOrgView,
    Step2RegisterOrgView,
    UserFileImportView,
    VerifyAuthorizedDomainView,
    VerifyDeliverabilityTestView,
    VerifyRegisterTokenOrgView,
)

app_name = "users"

urlpatterns = [
    path("profile/", OrganizationProfileView.as_view(), name="organization-profile"),
    path("register/", Step1RegisterOrgView.as_view(), name="register-org-1"),
    path("register-2/", Step2RegisterOrgView.as_view(), name="register-org-2"),
    path("verify-token/", VerifyRegisterTokenOrgView.as_view(), name="verify-token"),
    path(
        "phishing-permission-check/",
        PhishingPermissionCheckView.as_view(),
        name="phishing-permission-check",
    ),
    path(
        "resend-activation-link/",
        ResendActivationLinkOrgView.as_view(),
        name="resend-activation-link",
    ),
    path("login/", LoginView.as_view(), name="login"),
    path("user-file-import/", UserFileImportView.as_view(), name="user-file-import"),
    path(
        "forgot-password/", ForgotPasswordTriggerView.as_view(), name="forgot-password"
    ),
    path("employees/", EmployeesListView.as_view(), name="employees"),
    path(
        "employees-paginated/",
        EmployeesPaginatedListView.as_view(),
        name="employees-paginated",
    ),
    path("add-employee/", AddEmployeeView.as_view(), name="add-employee"),
    path(
        "employees/deactivate/",
        DeactivateEmployeesView.as_view(),
        name="deactivate-employee",
    ),
    path(
        "employees/<uuid:id>/",
        EmployeeUpdateView.as_view(),
        name="update-user",
    ),
    path("azure-ad-sign-in/", AzureADSignInAPIView.as_view(), name="azure_ad_sign_in"),
    path(
        "azure-ad-callback/", AzureADCallbackAPIView.as_view(), name="azure_ad_callback"
    ),
    path("import-okta-users/", ImportOktaUsers.as_view(), name="import-okta-users"),
    path("departments/", DepartmentView.as_view(), name="departments"),
    path(
        "departments/delete/",
        DeleteDepartmentsView.as_view(),
        name="delete-departments",
    ),
    path("departments/<str:id>/", DetailDepartmentView.as_view(), name="department"),
    path("settings/cut-off-score/", SetCutOffScoreView.as_view(), name="cut-off-score"),
    path(
        "settings/enrollment-notifications/",
        EnrollmentAndNotificationsSettingsView.as_view(),
        name="enrollment-notifications",
    ),
    path(
        "settings/allowlisting/",
        AllowlistingSettingsView.as_view(),
        name="allowlisting-settings",
    ),
    path(
        "settings/phishing-report-email/",
        PhishingReportEmailView.as_view(),
        name="phishing-report-email",
    ),
    path(
        "settings/authorized-domains/",
        AuthorizedDomainView.as_view(),
        name="authorized-domains",
    ),
    path(
        "settings/authorized-domains/<str:id>/",
        DetailedAuthorizedDomainView.as_view(),
        name="authorized-domain",
    ),
    path(
        "settings/authorized-domains/<str:id>/verify/",
        VerifyAuthorizedDomainView.as_view(),
        name="verify-authorized-domain",
    ),
    path(
        "settings/authorized-domains/<str:id>/resend-verification/",
        ResendAuthorizedDomainVerificationEmailView.as_view(),
        name="resend-authorized-domain-verification",
    ),
    path(
        "settings/deliverability-test/",
        CreateListDeliverabilityTestView.as_view(),
        name="deliverability-test",
    ),
    path(
        "settings/deliverability-test/<str:id>/",
        DetailedDeliverabilityTestView.as_view(),
        name="detailed-deliverability-test",
    ),
    path(
        "settings/deliverability-test/<str:id>/verify/",
        VerifyDeliverabilityTestView.as_view(),
        name="verify-deliverability-test",
    ),
    path(
        "reset-password/<str:token>/",
        ResetPasswordView.as_view(),
        name="reset-password",
    ),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
    path(
        "dashboard/", OrganizationDashboardView.as_view(), name="organization-dashboard"
    ),
]
