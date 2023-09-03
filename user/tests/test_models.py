from django.test import TestCase
from django.contrib.auth import get_user_model

from user.models import User


class ModelTests(TestCase):
    """Tests for User model."""

    def test_create_user_successful(self):
        """Test creating an ordinary user successfully."""

        email = 'test@example.com'
        name = 'Sample Name'
        password = 'test_pass123'

        new_user = get_user_model().objects.create_user(
            email=email,
            name=name,
            password=password
        )

        self.assertEqual(new_user.email, email)
        self.assertTrue(new_user.check_password(password))

    def test_create_without_email_raises_error(self):
        """Test raises an error when trying to create a user without email."""

        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(
                email='',
                name='Name',
                password='test_p54678'
            )

    def test_new_user_email_normalized(self):
        """Test that the email provided by new user has been normalized."""

        sample_emails = [
            ['test1@EXAMPLE.com', 'test1@example.com'],
            ['Test2@Example.com', 'Test2@example.com'],
            ['TEST3@EXAMPLE.COM', 'TEST3@example.com'],
            ['test4@example.COM', 'test4@example.com']
        ]
        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(
                email=email,
                name='Name',
                password='test_12345'
            )
            self.assertEqual(user.email, expected)

    def test_create_superuser(self):
        """Test creating a superuser."""

        user = get_user_model().objects.create_superuser(
            email='test@example.com',
            name='Superuser Name',
            password='test_pass987'
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

