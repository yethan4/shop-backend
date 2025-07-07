from django.core.exceptions import ValidationError
from django.test import TestCase
from django.contrib.auth import get_user_model

from user import models


def create_user(
    email='user@example.com',
    password='testpass123',
    username='testuser',
    phone_number='123456789',
    first_name='Test',
    last_name='User'
):
    """Create and return a new user."""
    return get_user_model().objects.create_user(
        email=email,
        password=password,
        username=username,
        phone_number=phone_number,
        first_name=first_name,
        last_name=last_name
    )


class CustomUserModelTests(TestCase):
    """Test CustomUser model."""

    def test_create_user_with_email_successful(self):
        """Test creating a user with an email is successful"""
        email = 'test@example.com'
        user = create_user(email=email)
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password('testpass123'))

    def test_new_user_email_normalized(self):
        """Test the email for a new user is normalized"""
        email = 'test@EXAMPLE.COM'
        user = create_user(email=email)
        self.assertEqual(user.email, email.lower())

    def test_create_user_without_email_raises_error(self):
        """Test creating user without email raises ValueError"""
        with self.assertRaises(ValueError):
            create_user(email='')

    def test_create_user_with_invalid_phone_raises_error(self):
        """Test creating user without phone number raises ValueError"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(
                email='test2@example.com',
                password='testpass123',
                username='user2',
                phone_number='',
                first_name='Test2',
                last_name='User2'
            )

    def test_create_superuser(self):
        """Test creating a superuser"""
        user = get_user_model().objects.create_superuser(
            email='super@example.com',
            password='superpass123',
            username='superuser',
            phone_number='987654321',
            first_name='Super',
            last_name='User'
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)


class AddressModelTests(TestCase):
    """Test Address Model."""

    def setUp(self):
        self.user = create_user()
        self.client.force_login(self.user)

    def test_create_address_successful(self):
        """Test successful creation of an Address instance."""
        address = models.Address.objects.create(
            user=self.user,
            street="Drzymaly 3",
            city="Poznan",
            zip_code="60-613",
            country="Poland",
        )

        self.assertEqual(
            models.Address.objects.filter(user=self.user).count(), 1)
        self.assertTrue(models.Address.objects.filter(id=address.id).exists())
        self.assertEqual(address.user, self.user)
        self.assertEqual(address.street, "Drzymaly 3")
        self.assertEqual(address.city, "Poznan")
        self.assertEqual(address.zip_code, "60-613")
        self.assertEqual(address.country, "Poland")

    def test_address_requires_street(self):
        """
        Test that creating an Address without a street raises a ValidationError
        """
        address = models.Address(
            user=self.user,
            city="Poznan",
            zip_code="60-613",
            country="Poland",
        )

        with self.assertRaises(ValidationError):
            address.full_clean()
