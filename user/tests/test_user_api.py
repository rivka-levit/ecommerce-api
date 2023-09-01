"""
Tests for user profile APIs.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

CREATE_USER_URL = reverse('user:create')


def create_user(**params):
    """Create and return a new user."""

    defaults = {
        'email': 'test@example.com',
        'name': 'Sample Name',
        'password': 'test_pass12345'
    }
    defaults.update(params)

    return get_user_model().objects.create_user(**defaults)


class PublicUserApiTests(TestCase):
    """Test requests from unauthorized users."""

    def setUp(self) -> None:
        self.client = APIClient()

    def test_create_user_success(self):
        """Test creating a new user successfully."""

        payload = {
            'email': 'test@example.com',
            'name': 'Sample Name',
            'password': 'test_pass123'
        }

        r = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r.data['email'], payload['email'])
        user = get_user_model().objects.get(email=payload['email'])
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', r.data)

    def test_create_user_generate_name(self):
        """
        Test creating a new user with a name generated from email,
        when the name hasn't been provided.
        """

        payload = {
            'email': 'sample_one@example.com',
            'password': 'test_pass654'
        }

        r = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=payload['email'])
        self.assertEqual(user.name, 'sample_one')

    def test_create_user_email_not_unique_fails(self):
        """Test creating a user with email that already exists, fails."""

        payload = {
            'email': 'abc@example.com',
            'name': 'Sample Name',
            'password': 'test_pass123'
        }

        create_user(**payload)

        r = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_user_password_too_short_fails(self):
        """
        Test creating a new user fails when the password provided is
        shorter, then 8 characters.
        """

        payload = {
            'email': 'test_test@example.com',
            'password': '123a'
        }

        r = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        exists = get_user_model().objects.filter(
            email=payload['email']
        ).exists()
        self.assertFalse(exists)
