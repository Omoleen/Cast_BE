from django.contrib.auth.models import BaseUserManager

from Castellum.enums import Roles


class OrganizationManager(BaseUserManager):
    role = Roles.ORGANIZATION

    def get_queryset(self, *args, **kwargs):
        results = super().get_queryset(*args, **kwargs)
        return results.filter(role=self.role)

    def create_org(self, email, name, url, password=None, **kwargs):

        if not email:
            raise ValueError("Organization must have an email address")
        if not name:
            raise ValueError("Organization must have a name")
        if not url:
            raise ValueError("Organization must have a url")

        user = self.model(
            email=self.normalize_email(email),
            role=self.role,
        )
        user.set_password(password)
        user.save(using=self._db)

        self.create_organization_profile(organization=user, name=name, url=url)

        return user

    def create_organization_profile(self, organization, name, url):

        from ..models import OrganizationProfile

        return OrganizationProfile.objects.create(
            organization=organization, name=name, url=url
        )
