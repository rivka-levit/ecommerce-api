"""
Serializers for user APIs.
"""
from django.contrib.auth import get_user_model

from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user object."""

    class Meta:
        model = get_user_model()
        fields = ['email', 'password']
        extra_kwargs = {
            'password': {
                'write_only': True,
                'min_length': 8
            }
        }

    def create(self, validated_data):
        """Create and return a user."""

        name = validated_data.pop('name', None)

        # Generate a name for the user it has not been provided
        if not name:
            email = validated_data['email']
            name = email.split('@')[0]

        validated_data['name'] = name

        return get_user_model().objects.create_user(**validated_data)
