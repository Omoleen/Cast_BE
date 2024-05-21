import factory
from faker import Faker

from Castellum.enums import Roles


class OrganizationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "users.Organization"

    email = factory.Faker("email")
    password = "testpassword123"

    is_active = True
    is_email_verified = True

    role = Roles.ORGANIZATION

    @classmethod
    def _create(self, model_class, *args, **kwargs):
        manager = self._get_manager(model_class)
        fake = Faker()

        kwargs["name"] = kwargs.get("name", fake.company())
        kwargs["url"] = kwargs.get("url", fake.url())

        user = manager.create_org(*args, **kwargs)
        user.is_active = True
        user.save()

        return user


class DepartmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "users.Department"

    name = factory.Faker("name")
    organization = factory.SubFactory("users.factory.OrganizationFactory")

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        manager = cls._get_manager(model_class)
        return manager.create(*args, **kwargs)


class EmployeeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "users.Employee"

    email = factory.Faker("email")
    password = "testpassword123"

    is_active = True
    is_email_verified = True

    role = Roles.EMPLOYEE

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        manager = cls._get_manager(model_class)
        org = OrganizationFactory.create()
        department = DepartmentFactory.create(organization=org)
        fake = Faker()
        first_name = fake.first_name()
        last_name = fake.last_name()
        user = manager.create_emp(
            organization=org,
            department=department,
            first_name=first_name,
            last_name=last_name,
            *args,
            **kwargs
        )

        return user
