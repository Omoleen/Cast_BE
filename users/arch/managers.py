import pendulum
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

from abstract.managers import SimpleManager, SimpleModelManager
from campaign.enums import CampaignTypes
from phishing.models import PhishingTemplate
from users.models import (
    AuthorizedDomain,
    Department,
    Employee,
    EmployeeProfile,
    Organization,
    OrganizationProfile,
)
from users.tasks import create_employee_records

from ..serializers import (
    ActivityLogSerializer,
    DepartmentSerializer,
    EmployeeProfileSerializer,
    EmployeeSerializer,
    TokensSerializer,
)
from ..services import UserImport
from ..utils import UserCSVImport, UserFileImport, UserXLSXImport

User = get_user_model()


class Step1RegisterOrgManager(SimpleModelManager):
    name = serializers.CharField(write_only=True)
    url = serializers.CharField(write_only=True)

    class Meta:
        model = Organization
        fields = ["email", "name", "url"]

    def _create(self, validated_data):
        return self.Meta.model.objects.create_org(**validated_data)

    def _notify_user(self, data: dict):
        organization: Organization = data["obj"]
        organization.receive_email("organization-activation")

    def _validate_fields(self, attrs):
        attrs = super()._validate_fields(attrs)
        # TODO check if it's an official domain
        return attrs

    def _validate_db(self, attrs):
        model = self.Meta.model
        if model.objects.filter(email=attrs["email"]).exists():
            raise serializers.ValidationError("Email already exists")
        if OrganizationProfile.objects.filter(name=attrs["name"]).exists():
            raise serializers.ValidationError("Organization name already exists")
        # if OrganizationProfile.objects.filter(name=attrs["url"].lower()).exists():
        #     raise serializers.ValidationError("Organization url already exists")
        return attrs

    def _to_representation(self, instance):
        return "Account Verification Link sent"


class ResendActivationLinkOrgManager(SimpleManager):

    email = serializers.EmailField(required=True, write_only=True)

    class Meta:
        fields = ["email"]

    def _validate_db(self, attrs):
        organizations = Organization.objects.filter(
            email=attrs["email"], is_email_verified=False
        )
        if not organizations.exists():
            raise serializers.ValidationError(
                "Organization does not exist or organization has already been activated"
            )
        self.organization = organizations.first()
        return attrs

    def _create(self, validated_data):
        organization: Organization = self.organization
        organization.receive_email("organization-activation")
        return validated_data

    def _to_representation(self, instance):
        return "Account Verification Link sent"


class VerifyRegisterTokenOrgManager(SimpleManager):
    email = serializers.EmailField()
    token = serializers.CharField(write_only=True, required=True)

    class Meta:
        fields = ["email", "token"]

    def _validate_db(self, attrs):
        self.users = User.objects.filter(email=attrs["email"])
        if not self.users.exists():
            raise serializers.ValidationError("User does not exist")
        self.user = self.users[0]
        if self.user.token != attrs["token"]:
            raise serializers.ValidationError("Token is incorrect")
        return attrs

    def _to_representation(self, instance):
        return "Email Verified"

    def _create(self, validated_data):
        return validated_data


class Step2RegisterOrgManager(SimpleModelManager):
    password = serializers.CharField(min_length=8, required=True, write_only=True)
    confirmPassword = serializers.CharField(
        min_length=8, required=True, write_only=True
    )
    email = serializers.EmailField(required=True)
    token = serializers.CharField(write_only=True, required=True)
    tokens = TokensSerializer(read_only=True)

    class Meta:
        model = User
        fields = ["password", "confirmPassword", "email", "token", "tokens"]

    def _validate_fields(self, attrs):
        if attrs["password"] != attrs["confirmPassword"]:
            raise serializers.ValidationError("Passwords do not match")
        return attrs

    def _validate_db(self, attrs):
        self.users = User.objects.filter(email=attrs["email"])
        if not self.users.exists():
            raise serializers.ValidationError("User does not exist")
        self.user = self.users[0]
        if self.user.token != attrs["token"]:
            raise serializers.ValidationError("Token is incorrect")
        return attrs

    def _create(self, validated_data):
        user: Organization = self.user
        user.set_password(validated_data["password"])
        user.is_email_verified = True
        user.is_active = True
        user.save()
        return user


class UserFileImportManager(serializers.Serializer):
    file = serializers.FileField(required=True, write_only=True)
    employees = EmployeeSerializer(read_only=True, many=True)

    class Meta:
        fields = ["file", "employees"]

    def create(self, validated_data):
        file = validated_data["file"]
        file = UserFileImport(file)
        if file.is_valid():
            records = file.records
            self.new_employees = create_employee_records(
                records, self.context["request"].user.id
            )
            if not self.new_employees:
                raise serializers.ValidationError({"file": "No new employees added"})
            return records
        else:
            raise serializers.ValidationError(file.errors)

    def to_representation(self, instance):
        return {
            "data": {
                "employees": EmployeeSerializer(self.new_employees, many=True).data,
            },
            "message": "Users added Successfully",
        }


class AddEmployeeManager(SimpleModelManager):
    emp_profile = EmployeeProfileSerializer(read_only=True)
    first_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)
    department_id = serializers.CharField(write_only=True, required=False)
    email = serializers.EmailField()
    department = DepartmentSerializer(read_only=True)

    class Meta:
        model = Employee
        fields = [
            "id",
            "email",
            "emp_profile",
            "department_id",
            "department",
            "first_name",
            "last_name",
            "last_login",
        ]
        extra_kwargs = {
            "id": {"read_only": True},
            "last_login": {"read_only": True},
        }

    def _validate_db(self, attrs):
        if User.objects.filter(email=attrs["email"]).exists():
            raise serializers.ValidationError("User email already exists")
        if attrs.get("department_id"):
            departments = Department.objects.filter(
                id=attrs["department_id"], organization=self.context["request"].user
            )

            if not departments.exists():
                raise serializers.ValidationError("Department does not exist")
            self.department = departments.first()
        return attrs

    def _create(self, validated_data):
        organization: Organization = self.context["request"].user
        department = self.department if hasattr(self, "department") else None
        email = validated_data.pop("email")
        first_name = validated_data.pop("first_name")
        last_name = validated_data.pop("last_name")

        employee: Employee = Employee.objects.create_emp(
            organization=organization,
            email=email,
            first_name=first_name,
            last_name=last_name,
            department=department,
            **validated_data
        )
        employee.receive_email("employee-invite")
        return employee


class DepartmentManager(SimpleModelManager):
    class Meta:
        model = Department
        fields = ["name", "id", "num_employees"]
        extra_kwargs = {"id": {"read_only": True}, "num_employees": {"read_only": True}}

    def _validate_fields(self, attrs):
        attrs = super()._validate_fields(attrs)
        if Department.objects.filter(
            name=attrs["name"], organization=self.context["request"].user
        ).exists():
            raise serializers.ValidationError("Department already exists")
        return attrs

    def _create(self, validated_data):
        return Department.objects.create(
            organization=self.context["request"].user,
            name=validated_data["name"].lower(),
        )

    def _update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name).lower()
        instance.save()
        return instance

    def to_representation(self, instance):
        match self.context["request"].method:
            case "POST":
                return {
                    "data": {"id": instance.id, "name": instance.name},
                    "message": "Department Created Successfully",
                }

            case "GET":
                return {
                    "id": instance.id,
                    "name": instance.name,
                    "num_employees": instance.num_employees,
                }
            case "PATCH":
                return {
                    "data": {
                        "id": instance.id,
                        "name": instance.name,
                        "num_employees": instance.num_employees,
                    },
                    "message": "Department Updated Successfully",
                }


class DeactivateEmployeesManager(SimpleManager):
    ids = serializers.ListField(child=serializers.CharField(), write_only=True)

    class Meta:
        fields = ["ids"]

    def _validate_db(self, attrs):
        employees = Employee.objects.prefetch_related("emp_profile").filter(
            id__in=attrs["ids"], emp_profile__organization=self.context["request"].user
        )
        if not employees.exists():
            raise serializers.ValidationError("Employees do not exist")
        self.employees = employees
        return attrs

    def _create(self, validated_data):
        employees = self.employees
        for employee in employees:
            employee.deactivate_account()
        return validated_data

    def _to_representation(self, instance):
        return "Employees Deactivated Successfully"


class DeactivateDepartmentsManager(SimpleManager):
    ids = serializers.ListField(child=serializers.CharField(), write_only=True)

    class Meta:
        fields = ["ids"]

    def _validate_db(self, attrs):
        departments = Department.objects.filter(
            id__in=attrs["ids"], organization=self.context["request"].user
        )
        if not departments.exists():
            raise serializers.ValidationError("Departments do not exist")
        self.departments = departments
        return attrs

    def _create(self, validated_data):
        departments = self.departments
        departments.delete()
        return validated_data

    def _to_representation(self, instance):
        return "Departments Deactivated Successfully"


class EmployeeUpdateManager(SimpleModelManager):
    first_name = serializers.CharField(required=False, write_only=True)
    last_name = serializers.CharField(required=False, write_only=True)
    department_id = serializers.CharField(required=False, write_only=True)
    emp_profile = EmployeeProfileSerializer(read_only=True)

    class Meta:
        model = Employee
        fields = [
            "id",
            "email",
            "emp_profile",
            "department_id",
            "first_name",
            "last_name",
            "last_login",
        ]
        extra_kwargs = {
            "id": {"read_only": True},
            "last_login": {"read_only": True},
            "emp_profile": {"read_only": True},
            "email": {"read_only": True},
        }

    def _validate_db(self, attrs):
        attrs = super()._validate_db(attrs)
        if attrs.get("department_id"):
            departments = Department.objects.filter(
                id=attrs["department_id"], organization=self.context["request"].user
            )
            if not departments.exists():
                raise serializers.ValidationError("Department does not exist")
            self.department = departments.first()
        return attrs

    def _update(self, instance, validated_data):
        profile = instance.emp_profile
        profile.first_name = validated_data.get("first_name", profile.first_name)
        profile.last_name = validated_data.get("last_name", profile.last_name)
        if hasattr(self, "department"):
            profile.department = self.department
        profile.save()

        return instance


class ForgotPasswordTriggerManager(SimpleManager):
    email = serializers.EmailField(write_only=True, required=True)

    class Meta:
        fields = ["email"]

    def _validate_db(self, attrs):
        users = User.objects.filter(email=attrs["email"])
        if not users.exists():
            raise serializers.ValidationError("User does not exist")
        self.user = users.first()
        return attrs

    def _create(self, validated_data):
        user: User = self.user
        user.receive_email("password-reset")
        return validated_data

    def _to_representation(self, instance):
        return "Password Reset Link sent"


class ResetPasswordManager(SimpleModelManager):
    password = serializers.CharField(min_length=8, required=True, write_only=True)
    confirm_password = serializers.CharField(
        min_length=8, required=True, write_only=True
    )

    class Meta:
        model = User
        fields = ["password", "confirm_password"]

    def _validate_fields(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match")
        return super()._validate_fields(attrs)

    def _update(self, instance, validated_data):
        user = self.instance
        user.set_password(validated_data["password"])
        user.save()
        return instance

    def _to_representation(self, instance):
        return "Password Reset Successfully"


class ChangePasswordManager(SimpleModelManager):
    old_password = serializers.CharField(min_length=8, required=True, write_only=True)
    new_password = serializers.CharField(min_length=8, required=True, write_only=True)
    confirm_password = serializers.CharField(
        min_length=8, required=True, write_only=True
    )

    class Meta:
        model = User
        fields = ["old_password", "new_password", "confirm_password"]

    def _validate_fields(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match")
        if self.instance.check_password(attrs["new_password"]):
            raise serializers.ValidationError(
                "New Password cannot be the same as Old Password"
            )
        return super()._validate_fields(attrs)

    def _validate_db(self, attrs):
        user = self.context["request"].user
        if not user.check_password(attrs["old_password"]):
            raise serializers.ValidationError("Old Password is incorrect")
        return attrs

    def _update(self, instance, validated_data):
        user = self.context["request"].user
        user.set_password(validated_data["new_password"])
        user.save()
        user.receive_email("password-changed")
        return instance

    def _to_representation(self, instance):
        return "Password Changed Successfully"


class SetCutOffScoreManager(SimpleModelManager):
    cut_off_score = serializers.FloatField(
        required=True,
        min_value=0,
        max_value=100,
    )

    class Meta:
        model = OrganizationProfile
        fields = ["cut_off_score"]

    def _update(self, instance, validated_data):
        instance.cut_off_score = validated_data["cut_off_score"]
        instance.save()
        return instance


class EnrollmentAndNotificationsSettingsManager(SimpleModelManager):
    campaign_email_notification = serializers.BooleanField(
        required=False,
    )
    campaign_completion_notification = serializers.BooleanField(
        required=False,
    )
    reminder_notification = serializers.BooleanField(
        required=False,
    )

    class Meta:
        model = OrganizationProfile
        fields = [
            "campaign_email_notification",
            "campaign_completion_notification",
            "reminder_notification",
        ]

    def _update(self, instance, validated_data):
        instance.campaign_email_notification = validated_data.get(
            "campaign_email_notification", instance.campaign_email_notification
        )
        instance.campaign_completion_notification = validated_data.get(
            "campaign_completion_notification",
            instance.campaign_completion_notification,
        )
        instance.reminder_notification = validated_data.get(
            "reminder_notification", instance.reminder_notification
        )
        instance.save()
        return instance


class AllowlistingManager(SimpleManager):
    ip_addresses = serializers.ListField(child=serializers.IPAddressField())
    email_headers = serializers.ListField(child=serializers.CharField())
    domain_list = serializers.ListField(child=serializers.CharField())

    class Meta:
        fields = ["ip_addresses", "email_headers", "domain_list"]

    def _to_representation(self, instance):
        ip_addresses = settings.PHISHING_EMAIL_IP_ADDRESSES
        email_headers = settings.PHISHING_EMAIL_HEADERS
        domain_list = set(
            PhishingTemplate.objects.all().values_list("email_domain", flat=True)
        )
        return {
            "ip_addresses": ip_addresses,
            "email_headers": email_headers,
            "domain_list": domain_list,
        }


class PhishingReportEmailManager(SimpleModelManager):
    class Meta:
        model = OrganizationProfile
        fields = ["phishing_report_email"]

    def _update(self, instance, validated_data):
        instance.phishing_report_email = validated_data["phishing_report_email"]
        instance.save()
        return instance


class AuthorizedDomainManager(SimpleModelManager):
    class Meta:
        model = AuthorizedDomain
        fields = ["domain", "verified_on", "email", "id"]
        extra_kwargs = {
            "domain": {"read_only": True},
            "verified_on": {"read_only": True},
            "id": {"read_only": True},
        }

    def _create(self, validated_data):
        domain = validated_data["email"].split("@")[1]
        authorized_domain: AuthorizedDomain = AuthorizedDomain.objects.create(
            organization=self.context["request"].user,
            domain=domain,
            email=validated_data["email"],
        )
        authorized_domain.send_domain_verification_email()
        return authorized_domain


class OrganizationDashboardManager(SimpleModelManager):
    training_completion_rate = serializers.IntegerField(
        read_only=True, source="organization_training_completion_rate"
    )
    security_score = serializers.SerializerMethodField()
    activity_logs = ActivityLogSerializer(
        read_only=True, source="org_activity_logs", many=True
    )

    class Meta:
        model = Organization
        fields = [
            "security_score",
            "campaign_stats",
            "training_completion_rate",
            "activity_logs",
            "employees_security_stats",
            "departments_security_stats",
            "courses_phishing_campaign_stats",
        ]

    def get_security_score(self, obj):
        return obj.org_profile.security_score


class PhishingPermissionCheckManager(SimpleModelManager):
    authorized_domains = serializers.BooleanField(read_only=True)
    deliverability_tests = serializers.BooleanField(read_only=True)

    class Meta:
        model = Organization
        fields = ["authorized_domains", "deliverability_tests"]

    def get_authorized_domains(self, obj):
        return obj.authorized_domains.filter(verified_on__isnull=False).exists()

    def get_deliverability_tests(self, obj):
        return obj.deliverability_tests.filter(verified_on__isnull=False).exists()
