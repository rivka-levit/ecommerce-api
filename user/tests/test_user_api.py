"""
Tests for user profile APIs.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

CREATE_USER_URL = reverse('user:create')
PROFILE_URL = reverse('user:profile')
TOKEN_URL = reverse('user:token')


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
        self.assertEqual(r.data['name'], payload['name'])
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

    def test_retrieve_user_profile_unauthorized_fails(self):
        """Test authentication required to retrieve a user profile. """

        r = self.client.get(PROFILE_URL)

        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):
    """Test API requests that require authentication."""

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = create_user(email='test_user@example.com')
        self.client.force_authenticate(self.user)

    def test_retrieve_user_profile_success(self):
        """Test retrieving user's own profile successful."""

        r = self.client.get(PROFILE_URL)

        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data['name'], self.user.name)
        self.assertEqual(r.data['email'], self.user.email)

    def test_post_not_allowed_user_profile(self):
        """Test post request is not allowed for user profile."""

        r = self.client.post(PROFILE_URL, {})

        self.assertEqual(r.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile_success(self):
        """Test updating user's own profile successful."""

        payload = {
            'name': 'Another Name',
            'password': 'another_test_pass1234'
        }

        r = self.client.patch(PROFILE_URL, payload)

        self.user.refresh_from_db()
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))

    def test_delete_user_profile(self):
        """Test removing user's own profile."""

        r = self.client.delete(PROFILE_URL)

        self.assertEqual(r.status_code, status.HTTP_204_NO_CONTENT)
        exists = get_user_model().objects.filter(
            email=self.user.email
        ).exists()
        self.assertFalse(exists)

    def test_create_token_success(self):
        """Test generating a token for existing user."""

        user_credentials = {
            'email': 'user0987@example.com',
            'password': 'test_pass5566'
        }
        create_user(**user_credentials)

        r = self.client.post(TOKEN_URL, user_credentials)

        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIn('token', r.data)

    def test_create_token_invalid_password_fails(self):
        """Test generating token fails with invalid password."""

        create_user()
        payload = {
            'email': 'test@example.com',
            'password': 'bad_password'
        }

        r = self.client.post(TOKEN_URL, payload)

        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', r.data)

    def test_create_token_blank_password_fails(self):
        """Test generating token fails with blank password."""

        create_user()
        payload = {
            'email': 'test@example.com',
            'password': ''
        }

        r = self.client.post(TOKEN_URL, payload)

        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', r.data)
