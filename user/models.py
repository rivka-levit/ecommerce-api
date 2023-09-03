from django.db import models

from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager
)


class UserManager(BaseUserManager):
    """Manager for using custom user model."""

    def create_user(self, email, name=None, password=None):
        """Creates and return a new user."""

        if not email:
            raise ValueError('Users must have an email address.')

        if not name:
            name = email.split('@')[0]

        email = self.normalize_email(email)
        user = self.model(email=email, name=name)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password, name=None):
        """Creates and return a new superuser."""

        if not name:
            name = email.split('@')[0]

        user = self.create_user(email, name, password)

        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)

        return user


class User(AbstractBaseUser, PermissionsMixin):
    """
    Represents a user in the system. Stores all user account
    related data, such as 'email address' and 'name'.
    """

    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'

    def get_full_name(self):
        """Is used by Django when it needs to get the full name of a user."""

        return self.name

    def get_short_name(self):
        """Is used by Django when it needs to get the short name of a user."""

        return self.name

    def __str__(self):
        """
        Is used by Django when it needs to convert a user object to string.
        """

        return f'{self.email} -- {self.name}'
