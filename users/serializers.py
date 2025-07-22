from rest_framework import serializers
from .models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, required=False, style={'input_type': 'password'})
    last_login = serializers.DateTimeField(read_only=True)
    date_joined = serializers.DateTimeField(read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 
            'role', 'role_display', 'phone', 'is_active', 'is_staff', 
            'is_superuser', 'last_login', 'date_joined', 'password', 'password_confirm'
        ]
        read_only_fields = ['id', 'last_login', 'date_joined', 'role_display']
    
    def validate(self, attrs):
        # Password validation for creation
        if self.instance is None:  # Creating new user
            password = attrs.get('password')
            password_confirm = attrs.get('password_confirm')
            
            if not password:
                raise serializers.ValidationError({'password': 'Password is required for new users.'})
            
            if password != password_confirm:
                raise serializers.ValidationError({'password_confirm': 'Passwords do not match.'})
            
            try:
                validate_password(password)
            except ValidationError as e:
                raise serializers.ValidationError({'password': e.messages})
        
        # Password validation for updates (optional)
        else:
            password = attrs.get('password')
            password_confirm = attrs.get('password_confirm')
            
            if password and password != password_confirm:
                raise serializers.ValidationError({'password_confirm': 'Passwords do not match.'})
            
            if password:
                try:
                    validate_password(password)
                except ValidationError as e:
                    raise serializers.ValidationError({'password': e.messages})
        
        return attrs
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        validated_data.pop('password_confirm', None)
        
        # Set owner permissions if role is owner
        if validated_data.get('role') == 'owner':
            validated_data['is_staff'] = True
            validated_data['is_superuser'] = True
        
        user = User.objects.create_user(password=password, **validated_data)
        return user
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        validated_data.pop('password_confirm', None)
        
        # Set owner permissions if role is owner
        if validated_data.get('role') == 'owner':
            validated_data['is_staff'] = True
            validated_data['is_superuser'] = True
        elif validated_data.get('role') and validated_data.get('role') != 'owner':
            # Remove superuser/staff if changing from owner to another role
            if instance.role == 'owner':
                validated_data['is_staff'] = False
                validated_data['is_superuser'] = False
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance

class UserListSerializer(serializers.ModelSerializer):
    """Simplified serializer for list views"""
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 
            'role', 'role_display', 'phone', 'is_active', 'last_login', 'date_joined'
        ] 