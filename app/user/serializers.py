"""
Serializers for the user and address API View.
"""
from django.contrib.auth import get_user_model

from rest_framework import serializers
from rest_framework.validators import UniqueValidator

import re


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""

    username = serializers.CharField(
        required=True,
        validators=[UniqueValidator(
            queryset=get_user_model().objects.all(),
            message="An account with this username already exists."
        )]
    )
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(
            queryset=get_user_model().objects.all(),
            message="An account with this email already exists."
        )]
    )
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    phone_number = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = get_user_model()
        fields = ['username', 'email', 'first_name', 'last_name',
                  'phone_number', 'password', 'password2']

    def create(self, validated_data):
        """Create and return a user with encrypted password."""
        validated_data.pop('password2')
        return get_user_model().objects.create_user(**validated_data)

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({
                "password": "Passwords do not match."
                })
        return attrs

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 \
                                              characters long")
        return value

    def validate_email(self, value):
        return value.lower()

    def validate_phone_number(self, value):
        if not re.fullmatch(r'^\+?\d{9,15}$', value):
            raise serializers.ValidationError(
                "Phone number must start with optional \
                '+' and contain 9-15 digits.")

        User = get_user_model()
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError(
                "An account with this phone number already exists")

        return value


class CurrentUserSerializer(serializers.ModelSerializer):
    """Serializer for basic current user data."""

    class Meta:
        model = get_user_model()
        fields = ['username', 'email', 'first_name', 'last_name']


class CurrentUserDetailSerializer(serializers.ModelSerializer):
    """Serializer for detail current user data"""

    class Meta:
        model = get_user_model()
        fields = ['username', 'email', 'first_name', 'last_name',
                  'phone_number']
