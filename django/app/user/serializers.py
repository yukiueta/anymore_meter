from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'permission', 'is_active', 'date_joined']
        read_only_fields = ['date_joined']