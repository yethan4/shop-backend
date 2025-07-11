"""
Views for the user and adress API
"""
from rest_framework.response import Response
from rest_framework import (
    generics,
    status,
)
from rest_framework.permissions import AllowAny, IsAuthenticated


from .serializers import (
    UserRegistrationSerializer,
    CurrentUserSerializer,
    CurrentUserDetailSerializer,
    AddressSerializer
)

from .models import Address


class UserRegistrationAPIView(generics.GenericAPIView):
    """API view for user registration."""
    permission_classes = (AllowAny,)
    serializer_class = UserRegistrationSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response(self.get_serializer(user).data,
                        status=status.HTTP_201_CREATED)


class CurrentUserAPIView(generics.RetrieveAPIView):
    """API view for basic current user data"""

    permission_classes = [IsAuthenticated]
    serializer_class = CurrentUserSerializer

    def get_object(self):
        return self.request.user


class CurrentUserDetailAPIView(generics.RetrieveAPIView):
    """API view for detail current user data"""

    permission_classes = [IsAuthenticated]
    serializer_class = CurrentUserDetailSerializer

    def get_object(self):
        return self.request.user


class AddressCreateAPIView(generics.CreateAPIView):
    """
    Create a new address for the current user, or return an existing one
    if the same address already exists.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = AddressSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        address, created = Address.objects.get_or_create(
            user=request.user,
            **serializer.validated_data
        )

        serializer.instance = address

        headers = self.get_success_headers(serializer.data)
        return Response(
            {
                "created": created,
                "address": serializer.data
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
            headers=headers
        )
