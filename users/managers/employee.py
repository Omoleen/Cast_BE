from django.contrib.auth.models import BaseUserManager

from Castellum.enums import Roles


class EmployeeManager(BaseUserManager):
    role = Roles.EMPLOYEE

    def get_queryset(self, *args, **kwargs):
        results = super().get_queryset(*args, **kwargs)
        return results.filter(role=self.role)

    def create_emp(self, email, password=None, *args, **kwargs):

        if not email:
            raise ValueError("User must have an email address")

        user = self.model(
            email=self.normalize_email(email),
            role=self.role,
            is_active=True,
            is_email_verified=kwargs.get("is_email_verified", False),
        )
        user.set_password(password)
        user.save(using=self._db)
        employee_attributes = ["email", "role", "is_active", "is_email_verified"]

        for attr in employee_attributes:
            if attr in kwargs:
                kwargs.pop(attr)

        self.create_employee_profile(employee=user, **kwargs)
        return user

    def create_employee_profile(self, employee, *args, **kwargs):
        from ..models import EmployeeProfile

        return EmployeeProfile.objects.create(employee=employee, *args, **kwargs)
