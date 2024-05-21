from django.contrib.auth import get_user_model
from rest_framework import serializers

from abstract.managers import SimpleManager, SimpleModelManager
from users.models import (
    ActivityLog,
    AuthorizedDomain,
    DeliverabilityTest,
    Department,
    Employee,
    EmployeeProfile,
    Organization,
    OrganizationProfile,
)
from users.tasks import create_employee_records

from .services import UserImport
from .utils import UserCSVImport, UserFileImport, UserXLSXImport

User = get_user_model()


class TokensSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()


class OrganizationSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="org_profile.name")

    class Meta:
        model = Organization
        fields = ["email", "last_login", "name", "id"]


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ["name", "id"]


class EmployeeProfileSerializer(serializers.ModelSerializer):
    department = DepartmentSerializer(read_only=True)

    class Meta:
        model = EmployeeProfile
        fields = [
            "first_name",
            "last_name",
            "status",
            "department",
        ]


class EmployeeSerializer(serializers.ModelSerializer):
    emp_profile = EmployeeProfileSerializer()
    first_name = serializers.CharField(source="emp_profile.first_name")
    last_name = serializers.CharField(source="emp_profile.last_name")
    status = serializers.CharField(source="emp_profile.status")

    class Meta:
        model = Employee
        fields = [
            "id",
            "email",
            "last_login",
            "emp_profile",
            "first_name",
            "last_name",
            "status",
        ]

        extra_kwargs = {
            "id": {"read_only": True},
            "last_login": {"read_only": True},
            "email": {"read_only": True},
        }

    # def create(self, validated_data):
    #     emp_profile_data = validated_data.pop("emp_profile")
    #     employee = Employee.objects.create(**validated_data)
    #     EmployeeProfile.objects.create(employee=employee, **emp_profile_data)
    #     return employee

    def update(self, instance, validated_data):
        emp_profile_data = validated_data.pop("emp_profile", None)
        emp_profile = instance.emp_profile

        instance.email = validated_data.get("email", instance.email)
        instance.is_active = validated_data.get("is_active", instance.is_active)
        instance.save()

        if emp_profile_data is not None:
            for attr, value in emp_profile_data.items():
                setattr(emp_profile, attr, value)
            emp_profile.save()

        return instance


class EmployeeListSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source="emp_profile.first_name")
    last_name = serializers.CharField(source="emp_profile.last_name")
    # status = serializers.CharField(source="emp_profile.status")

    class Meta:
        model = Employee
        fields = [
            "id",
            "email",
            # "last_login",
            "first_name",
            "last_name",
            # "status",
        ]

        extra_kwargs = {
            "id": {"read_only": True},
            "last_login": {"read_only": True},
            "email": {"read_only": True},
        }


class DeliverabilityTestSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliverabilityTest
        fields = ["id", "email", "verified_on"]
        extra_kwargs = {"id": {"read_only": True}, "verified_on": {"read_only": True}}

    def validate(self, attrs):
        attrs = super().validate(attrs)
        email = attrs.get("email")
        domain = email.split("@")[1]
        if not AuthorizedDomain.objects.filter(domain=domain).exists():
            raise serializers.ValidationError("Unauthorized domain")
        return attrs

    def create(self, validated_data):
        deliverability_test: DeliverabilityTest = DeliverabilityTest.objects.create(
            **validated_data, organization=self.context["request"].user
        )
        deliverability_test.send_domain_verification_email()
        return deliverability_test


class ActivityLogSerializer(serializers.ModelSerializer):
    employee = EmployeeListSerializer(read_only=True)

    class Meta:
        model = ActivityLog
        fields = ["employee", "description", "created_at"]
        extra_kwargs = {"id": {"read_only": True}, "created_at": {"read_only": True}}


class UserLoginSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True)
    role = serializers.CharField(read_only=True)
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ["email", "password", "role", "access", "refresh"]

    def validate(self, data):
        user = User.objects.filter(email=data.get("email")).first()
        if user is None:
            raise serializers.ValidationError("User does not exist")
        if not user.check_password(data.get("password")):
            raise serializers.ValidationError("Invalid password")
        self.user = user
        return data

    def create(self, validated_data):
        return self.user

    def to_representation(self, instance):
        return {"role": instance.role, **instance.tokens}
