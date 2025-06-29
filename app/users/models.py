from django.db import models
from django.conf import settings
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)


class CustomUserManager(BaseUserManager):
    """Manager for users."""

    def create_user(self, email, username, phone_number, first_name, last_name,
                    password=None, **extra_fields):
        """Create, save and return a new user"""
        if not email:
            raise ValueError("User must have an email address.")
        if not username:
            raise ValueError("User must have a username.")
        if not phone_number:
            raise ValueError("User must have a phone number.")
        if not first_name:
            raise ValueError("User must have a first name")
        if not last_name:
            raise ValueError("User must have a last name")
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            username=username,
            phone_number=phone_number,
            first_name=first_name,
            last_name=last_name,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, username, phone_number, first_name,
                         last_name, password=None, **extra_fields):
        """Create, save and return a new superuser"""
        user = self.create_user(
            email=email,
            username=username,
            phone_number=phone_number,
            first_name=first_name,
            last_name=last_name,
            password=password,
            **extra_fields
        )
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)

        return user


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """User in the system."""
    username = models.CharField(max_length=150, unique=True, null=False,
                                blank=False)
    email = models.EmailField(max_length=255, unique=True, null=False,
                              blank=False)
    first_name = models.CharField(max_length=100, null=False, blank=False)
    last_name = models.CharField(max_length=100, null=False, blank=False)
    phone_number = models.CharField(max_length=15, unique=True, null=False,
                                    blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'phone_number', 'first_name', 'last_name']

    def __str__(self):
        return self.email


class Address(models.Model):
    """Address for users and orders"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             related_name='addresses')
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.city}, {self.street}, {self.zip_code}"
