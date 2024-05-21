from django.contrib.auth.base_user import BaseUserManager

from Castellum.enums import Roles


class UserManager(BaseUserManager):
    def create_superuser(self, email, password=None, **kwargs):
        if password is None:
            raise TypeError("Password should not be none")

        if not email:
            raise ValueError("User must have an email address")

        kwargs.update(
            {
                "is_superuser": True,
                "is_staff": True,
                "is_admin": True,
                "is_active": True,
                "role": Roles.ADMIN,
            }
        )

        user = self.model(email=self.normalize_email(email), **kwargs)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **kwargs):
        if password is None:
            raise TypeError("Password should not be none")

        if not email:
            raise ValueError("User must have an email address")

        kwargs.update({"role": Roles.EMPLOYEE})

        user = self.model(email=self.normalize_email(email), **kwargs)
        user.set_password(password)
        user.save(using=self._db)
        return user
