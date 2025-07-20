from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render
from django.http import JsonResponse
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import User
from .serializers import UserSerializer
from rest_framework.exceptions import PermissionDenied
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import logging
logger = logging.getLogger(__name__)
from rest_framework_simplejwt.tokens import RefreshToken
import json

@method_decorator(csrf_exempt, name='dispatch')
class LoginView(APIView):
    authentication_classes = []  # Disable SessionAuthentication (and thus CSRF) for this endpoint
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            username = request.data.get('username')
            password = request.data.get('password')
            
            if not username or not password:
                logger.warning("Missing username or password")
                return Response({
                    'error': 'Username and password are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            user = authenticate(username=username, password=password)
            
            if user is None:
                logger.warning(f"Invalid credentials for username: {username}")
                return Response({
                    'error': 'Invalid credentials'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            if not user.is_active:
                logger.warning(f"Inactive user tried to login: {username}")
                return Response({
                    'error': 'Account is disabled'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            serializer = UserSerializer(user)
            logger.info(f"User logged in: {username}")
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': serializer.data
            })
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return Response({'error': f'Login failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        logout(request)
        return Response({'message': 'Logged out successfully'})

class CurrentUserView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_admin or self.request.user.is_owner:
            return User.objects.all()
        return User.objects.filter(role=self.request.user.role)

    def create(self, request, *args, **kwargs):
        if not request.user.is_owner:
            raise PermissionDenied('Only owners can create users.')
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if not request.user.is_owner:
            raise PermissionDenied('Only owners can update users.')
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if not request.user.is_owner:
            raise PermissionDenied('Only owners can delete users.')
        return super().destroy(request, *args, **kwargs) 

@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def create_admin_user(request):
    """Temporary endpoint to create admin users - REMOVE IN PRODUCTION"""
    try:
        data = json.loads(request.body)
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'customer')
        
        # Check if user already exists
        if User.objects.filter(username=username).exists():
            return JsonResponse({'error': 'User already exists'}, status=400)
        
        # Create user with proper password hashing
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            role=role
        )
        
        if role == 'Owner':
            user.is_staff = True
            user.is_superuser = True
            user.save()
        
        return JsonResponse({
            'success': True,
            'message': f'User {username} created successfully',
            'user_id': user.id
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500) 