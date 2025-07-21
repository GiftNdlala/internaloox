from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    last_login = serializers.DateTimeField(read_only=True)
    date_joined = serializers.DateTimeField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 
            'role', 'phone', 'is_active', 'last_login', 'date_joined'
        ]
        read_only_fields = ['id', 'is_active', 'last_login', 'date_joined'] 