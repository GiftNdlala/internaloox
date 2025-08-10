from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import User
from .serializers import UserSerializer, UserListSerializer
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
    Hierarchical system: Users can access their role or lower levels
    """
    if not user or not requested_role:
        return False
        
    user_role = user.role.lower()
    requested_role = requested_role.lower()
    
    # Owner can access everything
    if user_role == 'owner':
        return True
    
    # Users can access their own role or lower in hierarchy
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
    """Get user's role permissions and accessible dashboards - Hierarchical access system"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        available_roles = []
        
        # Check which roles the user can access based on hierarchy
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
            },
            'access_system': 'hierarchical',
            'message': 'Users can access their role level and below in hierarchy'
        })

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return UserListSerializer
        return UserSerializer
    
    def get_queryset(self):
        # Order by date_joined for consistent pagination
        queryset = User.objects.all().order_by('-date_joined')
        
        # Filter based on user role permissions
        if self.request.user.is_owner:
            return queryset  # Owners can see all users
        elif self.request.user.is_admin:
            return queryset.exclude(role='owner')  # Admins can see all except owners
        else:
            return queryset.filter(id=self.request.user.id)  # Others can only see themselves

    def create(self, request, *args, **kwargs):
        if not request.user.is_owner:
            return Response({
                'error': 'Only users with Owner role can create new users',
                'required_role': 'owner',
                'your_role': request.user.role
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Return detailed response
        response_serializer = UserSerializer(user)
        return Response({
            'success': True,
            'message': f'User "{user.username}" created successfully',
            'user': response_serializer.data
        }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        if not request.user.is_owner:
            return Response({
                'error': 'Only users with Owner role can update users',
                'required_role': 'owner',
                'your_role': request.user.role
            }, status=status.HTTP_403_FORBIDDEN)
        
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        return Response({
            'success': True,
            'message': f'User "{user.username}" updated successfully',
            'user': serializer.data
        })

    def destroy(self, request, *args, **kwargs):
        if not request.user.is_owner:
            return Response({
                'error': 'Only users with Owner role can delete users',
                'required_role': 'owner',
                'your_role': request.user.role
            }, status=status.HTTP_403_FORBIDDEN)
        
        instance = self.get_object()
        
        # Prevent deleting yourself
        if instance.id == request.user.id:
            return Response({
                'error': 'You cannot delete your own account',
                'suggestion': 'Ask another owner to delete your account if needed'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        username = instance.username
        instance.delete()
        
        return Response({
            'success': True,
            'message': f'User "{username}" deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'user': serializer.data
        })
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_response = self.get_paginated_response(serializer.data)
            # Enhance the paginated response with additional info
            paginated_response.data.update({
                'success': True,
                'total_users': queryset.count(),
                'user_role': request.user.role
            })
            return paginated_response
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'users': serializer.data,
            'total_users': queryset.count(),
            'user_role': request.user.role
        }) 

class CreateUserView(APIView):
    """
    Secure endpoint to create new users with role assignment
    Only authenticated users with proper permissions can create users
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # Check if user has permission to create users
            if not request.user.is_owner:
                return Response({
                    'error': 'Only users with Owner role can create new users',
                    'required_role': 'owner',
                    'your_role': request.user.role
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Get data from request
            username = request.data.get('username')
            email = request.data.get('email')
            password = request.data.get('password')
            role = request.data.get('role', 'delivery')  # Default to lowest role
            first_name = request.data.get('first_name', '')
            last_name = request.data.get('last_name', '')
            phone = request.data.get('phone', '')
            
            # Validate required fields
            if not username or not password:
                return Response({
                    'error': 'Username and password are required',
                    'required_fields': ['username', 'password'],
                    'optional_fields': ['email', 'first_name', 'last_name', 'phone', 'role']
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate role
            valid_roles = [choice[0] for choice in User.ROLE_CHOICES]
            if role not in valid_roles:
                return Response({
                    'error': f'Invalid role: {role}',
                    'valid_roles': valid_roles
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if user already exists
            if User.objects.filter(username=username).exists():
                return Response({
                    'error': f'User with username "{username}" already exists',
                    'suggestion': 'Try a different username'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if email already exists (if provided)
            if email and User.objects.filter(email=email).exists():
                return Response({
                    'error': f'User with email "{email}" already exists',
                    'suggestion': 'Try a different email address'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create user with proper password hashing
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                role=role,
                first_name=first_name,
                last_name=last_name,
                phone=phone
            )
            
            # Set additional permissions for owner role
            if role.lower() == 'owner':
                user.is_staff = True
                user.is_superuser = True
                user.save()
            
            # Prepare response with user data
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone': user.phone,
                'role': user.role,
                'role_display': user.get_role_display(),
                'is_active': user.is_active,
                'date_joined': user.date_joined,
                'permissions': {
                    'can_access_owner': user_has_role_permission(user, 'owner'),
                    'can_access_admin': user_has_role_permission(user, 'admin'),
                    'can_access_warehouse': user_has_role_permission(user, 'warehouse'),
                    'can_access_delivery': user_has_role_permission(user, 'delivery'),
                }
            }
            
            logger.info(f"User created successfully: {username} (role: {role}) by {request.user.username}")
            
            return Response({
                'success': True,
                'message': f'User "{username}" created successfully with role "{role}"',
                'user': user_data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"User creation error: {str(e)}")
            return Response({
                'error': f'Failed to create user: {str(e)}',
                'type': type(e).__name__
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def create_admin_user(request):
    """DEPRECATED - Use CreateUserView instead. Kept for backward compatibility."""
    try:
        data = json.loads(request.body)
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'delivery')
        
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
        
        if role.lower() == 'owner':
            user.is_staff = True
            user.is_superuser = True
            user.save()
        
        return JsonResponse({
            'success': True,
            'message': f'User {username} created successfully',
            'user_id': user.id,
            'note': 'This endpoint is deprecated. Use POST /api/users/create/ instead.'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def warehouse_workers(request):
    """Get list of warehouse workers for task assignment dropdown"""
    try:
        # Get all warehouse workers (both new and legacy roles)
        workers = User.objects.filter(
            Q(role='warehouse_worker') | Q(role='warehouse') | Q(role='warehouse_manager'),
            is_active=True
        ).order_by('first_name', 'last_name')
        
        workers_data = []
        for worker in workers:
            workers_data.append({
                'id': worker.id,
                'username': worker.username,
                'first_name': worker.first_name,
                'last_name': worker.last_name,
                'full_name': worker.get_full_name() or worker.username,
                'email': worker.email,
                'role': worker.role,
                'employee_id': getattr(worker, 'employee_id', None),
                'can_manage_tasks': worker.can_manage_tasks,
                'is_active': worker.is_active
            })
        
        return Response(workers_data)
        
    except Exception as e:
        return Response({'error': str(e)}, status=500) 