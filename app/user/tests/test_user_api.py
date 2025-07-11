"""
Tests for the user API
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from user.models import Address


REGISTER_USER_URL = reverse('user:register-user')
TOKEN_PAIR_URL = reverse('user:token_obtain_pair')
TOKEN_REFRESH = reverse('user:token_refresh')
CURRENT_USER_INFO = reverse('user:current-user')
CURRENT_USER_DETAIL_INFO = reverse('user:current-user-detail')
CREATE_ADDRESS = reverse('user:create-address')


def create_user(**params):
    """Create and return a new user"""
    defaults = {
        'username': 'janek123',
        'email': 'user@example.com',
        'first_name': 'Jan',
        'last_name': 'Kowalski',
        'phone_number': '123456789',
        'password': 'Test1234',
    }
    defaults.update(params)
    return get_user_model().objects.create_user(**defaults)


class PublicUserAPITests(TestCase):
    """Test the public features of the user API."""
    def setUp(self):
        self.client = APIClient()

    def get_tokens_for_valid_user(self, email, password):
        """
        Authenticate the user with given email and password,
        then return access and refresh tokens from the API.
        """
        payload = {
            'email': email,
            'password': password
        }
        res = self.client.post(TOKEN_PAIR_URL, payload)
        return res.data

    def test_registration_user_success(self):
        """Test registration a user is successful"""
        payload = {
            'username': 'MichaLeS',
            'email': 'tESt@example.com',
            'first_name': 'Michał',
            'last_name': 'Kowalski',
            'phone_number': '654654654',
            'password': 'test1234',
            'password2': 'test1234',
        }
        res = self.client.post(REGISTER_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=payload['email'].lower())
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)
        self.assertNotIn('password2', res.data)
        self.assertEqual(res.data['email'], payload['email'].lower())
        self.assertEqual(res.data['username'], payload['username'])

    def test_user_with_email_exists_error(self):
        """Test error returned if user with email exists."""
        user_data = {
            'username': 'MichaLeS',
            'email': 'test@example.com',
            'first_name': 'Michał',
            'last_name': 'Kowalski',
            'phone_number': '654654654',
            'password': 'test1234',
        }
        create_user(**user_data)

        res = self.client.post(REGISTER_USER_URL, {
            'username': 'MichaLee',
            'email': 'test@example.com',
            'first_name': 'Michał',
            'last_name': 'Kowalski',
            'phone_number': '654654653',
            'password': 'test1234',
            'password2': 'test1234',
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_with_phone_exists_error(self):
        """Test error returned if user with phone number exists."""
        user_data = {
            'username': 'MichaLeS',
            'email': 'test@example.com',
            'first_name': 'Michał',
            'last_name': 'Kowalski',
            'phone_number': '654654654',
            'password': 'test1234',
        }
        create_user(**user_data)

        res = self.client.post(REGISTER_USER_URL, {
            'username': 'MichaLee',
            'email': 'test2@example.com',
            'first_name': 'Michał',
            'last_name': 'Kowalski',
            'phone_number': '654654654',
            'password': 'test1234',
            'password2': 'test1234',
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_with_username_exists_error(self):
        """Test error returned if user with username exists."""
        user_data = {
            'username': 'MichaLeS',
            'email': 'test@example.com',
            'first_name': 'Michał',
            'last_name': 'Kowalski',
            'phone_number': '654654654',
            'password': 'test1234',
        }
        create_user(**user_data)

        res = self.client.post(REGISTER_USER_URL, {
            'username': 'MichaLeS',
            'email': 'test2@example.com',
            'first_name': 'Michał',
            'last_name': 'Kowalski',
            'phone_number': '654354654',
            'password': 'test1234',
            'password2': 'test1234',
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_with_valid_credentials(self):
        """
        Test generates access and refresh token for valid credentials
        """
        user_details = {
            'email': 'test@example.com',
            'password': 'Test1234'
        }
        create_user(**user_details)

        payload = {
            'email': user_details['email'],
            'password': user_details['password'],
        }
        res = self.client.post(TOKEN_PAIR_URL, payload)

        self.assertIn('access', res.data)
        self.assertIn('refresh', res.data)

    def test_refresh_token(self):
        """Test refresh tokens"""
        payload = {
            'email': 'test@example.com',
            'password': 'Test1234',
        }

        create_user(**payload)
        tokens = self.get_tokens_for_valid_user(**payload)

        res = self.client.post(TOKEN_REFRESH, {'refresh': tokens['refresh']})

        self.assertIn('access', res.data)
        self.assertNotIn('refresh', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_with_invalid_credentials(self):
        """Test returns error if credentials invalid."""
        payload = {
            'email': 'y8kjhk788@lkjoiy.com',
            'password': 'oiaudasod',
        }

        res = self.client.post(TOKEN_PAIR_URL, payload)

        self.assertNotIn('access', res.data)
        self.assertNotIn('refresh', res.data)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_current_user_data_error(self):
        """Test that unauthorized user cannot retrieve current user data"""

        res = self.client.get(CURRENT_USER_INFO)
        res_detail = self.client.get(CURRENT_USER_DETAIL_INFO)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(res_detail.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_address_error(self):
        """Test that unauthorized user cannot create an address"""
        res = self.client.post(CREATE_ADDRESS, {
            'street': '123 Main St',
            'city': 'Warsaw',
            'zip_code': '00-001',
            'country': 'Poland'
        })

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Address.objects.all().count(), 0)


class PrivateUserAPITests(TestCase):
    """Test API request that require authentication"""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_current_user_basic_data(self):
        """Test retrieving basic data of the current authenticated user."""
        res = self.client.get(CURRENT_USER_INFO, {})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {
            'username': self.user.username,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name
        })
        self.assertNotIn("phone_number", res.data)
        self.assertNotIn("password", res.data)

    def test_retrieve_current_user_detail_data(self):
        """Test retrieving detailed data of the current authenticated user."""
        res = self.client.get(CURRENT_USER_DETAIL_INFO, {})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['phone_number'], self.user.phone_number)
        self.assertNotIn("password", res.data)

    def test_create_address(self):
        """Test create address by current user"""

        res = self.client.post(CREATE_ADDRESS, {
            'street': '123 Main St',
            'city': 'Warsaw',
            'zip_code': '00-001',
            'country': 'Poland'
        })

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Address.objects.all().count(), 1)

    def test_create_existing_address(self):
        """
        Test that the API prevents duplicate addresses and returns the
        existing address
        """

        payload = {
            'street': '123 Main St',
            'city': 'Warsaw',
            'zip_code': '00-001',
            'country': 'Poland'
        }
        Address.objects.create(user=self.user, **payload)

        res = self.client.post(CREATE_ADDRESS, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(Address.objects.count(), 1)
        self.assertEqual(res.data["created"], False)
