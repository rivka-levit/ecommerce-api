"""
Tests for Django admin modifications.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from rest_framework import status


class AdminTests(TestCase):
    """Tests for admin modifications."""

    def setUp(self) -> None:
        self.client = Client()
        self.admin_user = get_user_model().objects.create_superuser(
            email='admin@example.com',
            name='Super Name',
            password='test_pass1234'
        )
        self.client.force_login(self.admin_user)
        self.user = get_user_model().objects.create_user(
            email='user@example.com',
            name='Name',
            password='test_pass32567'
        )

    def test_users_listed(self):
        """Test users are listed on the page"""

        url = reverse('admin:user_user_changelist')
        r = self.client.get(url)

        self.assertContains(r, self.user.email)
        self.assertContains(r, self.user.name)

    def test_create_user_page(self):
        """Test the create user page works."""

        url = reverse('admin:user_user_add')
        r = self.client.get(url, args=[self.user.id])

        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_edit_user_page(self):
        """Test the edit user page works."""

        url = reverse('admin:user_user_change', args=[self.user.id])

        r = self.client.get(url)

        self.assertEqual(r.status_code, status.HTTP_200_OK)
