from rest_framework import generics
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from user.serializers import UserSerializer
from user.permissions import AccessOwnProfile


class CreateUserView(generics.CreateAPIView):
    """Create a new user in the system."""

    serializer_class = UserSerializer


class UserProfileView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update and delete user in the system."""

    serializer_class = UserSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, AccessOwnProfile,)

    def get_object(self):
        """Retrieve and return the user"""

        return self.request.user
