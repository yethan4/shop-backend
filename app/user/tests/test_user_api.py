"""
Tests for the user API
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status


REGISTER_USER_URL = reverse('user:register-user')


def create_user(**params):
    """Create and return a new user"""
    return get_user_model().objects.create_user(**params)


class PublicUserAPITests(TestCase):
    """Test the public features of the user API."""
    def setUp(self):
        self.client = APIClient()

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
