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

def user_has_role_permission(user, requested_role):
    """
    Check if user has permission to access the requested role dashboard
    """
    if not user or not requested_role:
        return False
        
    user_role = user.role.lower()
    requested_role = requested_role.lower()
    
    # Owner can access everything
    if user_role == 'owner':
        return True
    
    # Users can only access their own role or lower in hierarchy
    role_hierarchy = ['delivery', 'warehouse', 'admin', 'owner']
    
    try:
        user_level = role_hierarchy.index(user_role)
        requested_level = role_hierarchy.index(requested_role)
        return user_level >= requested_level
    except ValueError:
        # Invalid role
        return False

@method_decorator(csrf_exempt, name='dispatch')
class LoginView(APIView):
    authentication_classes = []  # Disable SessionAuthentication (and thus CSRF) for this endpoint
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            username = request.data.get('username')
            password = request.data.get('password')
            selected_role = request.data.get('role')  # NEW: Role selection from frontend
            
            if not username or not password:
                logger.warning("Missing username or password")
                return Response({
                    'error': 'Username and password are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Authenticate user credentials
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
            
            # NEW: Validate role permission if role is specified
            if selected_role:
                if not user_has_role_permission(user, selected_role):
                    logger.warning(f"User {username} (role: {user.role}) attempted to access {selected_role} dashboard without permission")
                    return Response({
                        'error': f'Access denied: You do not have {selected_role} permissions',
                        'user_role': user.role,
                        'requested_role': selected_role
                    }, status=status.HTTP_403_FORBIDDEN)
                
                # Log successful role-based login
                logger.info(f"User {username} (role: {user.role}) logged in to {selected_role} dashboard")
            else:
                # Default login without role specification
                logger.info(f"User {username} (role: {user.role}) logged in")
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            serializer = UserSerializer(user)
            
            response_data = {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': serializer.data,
                'permissions': {
                    'can_access_owner': user_has_role_permission(user, 'owner'),
                    'can_access_admin': user_has_role_permission(user, 'admin'),
                    'can_access_warehouse': user_has_role_permission(user, 'warehouse'),
                    'can_access_delivery': user_has_role_permission(user, 'delivery'),
                }
            }
            
            # Include selected role in response if provided
            if selected_role:
                response_data['selected_role'] = selected_role
            
            return Response(response_data)
            
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

class UserPermissionsView(APIView):
    """Get user's role permissions and accessible dashboards"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        available_roles = []
        
        # Check which roles the user can access
        roles_to_check = ['delivery', 'warehouse', 'admin', 'owner']
        for role in roles_to_check:
            if user_has_role_permission(user, role):
                available_roles.append({
                    'value': role,
                    'label': role.title(),
                    'can_access': True
                })
        
        return Response({
            'user_role': user.role,
            'available_roles': available_roles,
            'permissions': {
                'can_access_owner': user_has_role_permission(user, 'owner'),
                'can_access_admin': user_has_role_permission(user, 'admin'),
                'can_access_warehouse': user_has_role_permission(user, 'warehouse'),
                'can_access_delivery': user_has_role_permission(user, 'delivery'),
            }
        })

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