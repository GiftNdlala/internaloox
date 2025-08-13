from django.shortcuts import render
import sys
import traceback
from django.http import JsonResponse
from rest_framework import status, viewsets, filters
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from datetime import timedelta
from .models import Order, Customer, PaymentProof, OrderHistory, Product, Color, Fabric, OrderItem, ColorReference, FabricReference
from .serializers import (
    OrderSerializer, OrderListSerializer, OrderStatusUpdateSerializer,
    CustomerSerializer, PaymentProofSerializer, OrderHistorySerializer,
    ProductSerializer, ColorSerializer, FabricSerializer, OrderItemSerializer,
    ColorReferenceSerializer, FabricReferenceSerializer
)
from .permissions import CanCreateProducts
from django.db import models

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]  # Change from AllowAny
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'phone', 'email']
    ordering_fields = ['created_at', 'name']
    ordering = ['-created_at']

    def list(self, request, *args, **kwargs):
        if not Customer.objects.exists():
            # Return mock data for frontend testing
            mock_data = [
                {
                    'id': 1,
                    'name': 'John Doe',
                    'phone': '08012345678',
                    'email': 'john@example.com',
                    'address': '123 Main St',
                    'created_at': '2024-07-01T10:00:00Z',
                    'updated_at': '2024-07-01T10:00:00Z',
                },
                {
                    'id': 2,
                    'name': 'Jane Smith',
                    'phone': '08087654321',
                    'email': 'jane@example.com',
                    'address': '456 Side Ave',
                    'created_at': '2024-07-02T11:00:00Z',
                    'updated_at': '2024-07-02T11:00:00Z',
                }
            ]
            return Response(mock_data)
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """Create customer with role-based permissions"""
        user = request.user
        
        # Check if user can create customers
        if user.role not in ['owner', 'admin']:
            return Response({
                'error': 'Permission denied: Only Owner and Admin can create customers',
                'your_role': user.role
            }, status=status.HTTP_403_FORBIDDEN)
        
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """Update customer with role-based permissions"""
        user = request.user
        
        if user.role not in ['owner', 'admin']:
            return Response({
                'error': 'Permission denied: Only Owner and Admin can edit customers'
            }, status=status.HTTP_403_FORBIDDEN)
        
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Delete customer with role-based permissions"""
        user = request.user
        
        if user.role not in ['owner', 'admin']:
            return Response({
                'error': 'Permission denied: Only Owner and Admin can delete customers'
            }, status=status.HTTP_403_FORBIDDEN)
        
        return super().destroy(request, *args, **kwargs)

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    permission_classes = [IsAuthenticated]  # Change from AllowAny to IsAuthenticated
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['payment_status', 'order_status', 'production_status', 'created_by', 'assigned_to_warehouse', 'assigned_to_delivery']
    search_fields = ['order_number', 'customer__name', 'customer_name']
    ordering_fields = ['created_at', 'expected_delivery_date', 'total_amount']
    ordering = ['-created_at']

    def get_serializer_class(self):
        # Always use OrderSerializer for retrieve, update, partial_update, and create
        if self.action in ['list']:
            return OrderListSerializer
        return OrderSerializer

    def get_queryset(self):
        """Filter orders based on user role"""
        user = self.request.user
        queryset = Order.objects.all()
        
        # Owner and Admin can see all orders
        if user.role in ['owner', 'admin']:
            return queryset
        
        # Warehouse Manager can see orders assigned to warehouse or ready for production
        elif user.role == 'warehouse':
            return queryset.filter(
                models.Q(assigned_to_warehouse=user) |
                models.Q(order_status__in=['deposit_paid', 'order_ready']) |
                models.Q(production_status__in=['cutting', 'sewing', 'finishing', 'quality_check'])
            )
        
        # Warehouse Worker can see orders assigned to them or general warehouse orders
        elif user.role in ['warehouse_worker', 'warehouse']:
            return queryset.filter(
                models.Q(assigned_to_warehouse=user) |
                models.Q(order_status__in=['deposit_paid', 'order_ready'])
            )
        
        # Delivery can see orders ready for delivery or assigned to them
        elif user.role == 'delivery':
            return queryset.filter(
                models.Q(assigned_to_delivery=user) |
                models.Q(order_status__in=['order_ready', 'out_for_delivery'])
            )
        
        # Other roles can only see orders they created
        else:
            return queryset.filter(created_by=user)

    def create(self, request, *args, **kwargs):
        """Create order with role-based permissions"""
        user = request.user
        
        # Check if user can create orders
        if user.role not in ['owner', 'admin']:
            return Response({
                'error': 'Permission denied: Only Owner and Admin can create orders',
                'your_role': user.role,
                'required_roles': ['owner', 'admin']
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Proceed with creation
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """Update order with role-based permissions"""
        user = request.user
        instance = self.get_object()
        
        # Check if user can update orders
        if user.role not in ['owner', 'admin']:
            return Response({
                'error': 'Permission denied: Only Owner and Admin can edit orders',
                'your_role': user.role,
                'required_roles': ['owner', 'admin']
            }, status=status.HTTP_403_FORBIDDEN)
        
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Delete order with role-based permissions"""
        user = request.user
        instance = self.get_object()
        
        # Check if user can delete orders
        if user.role not in ['owner', 'admin']:
            return Response({
                'error': 'Permission denied: Only Owner and Admin can delete orders',
                'your_role': user.role,
                'required_roles': ['owner', 'admin']
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Prevent deletion of orders that are in production
        if instance.production_status not in ['not_started']:
            return Response({
                'error': 'Cannot delete order: Order is already in production',
                'production_status': instance.production_status,
                'suggestion': 'Cancel the order instead of deleting it'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Update order status with role-based permissions"""
        try:
            order = self.get_object()
            user = request.user
            
            # Define what statuses each role can change
            role_permissions = {
                'owner': ['all'],  # Owner can change to any status
                'admin': ['all'],  # Admin can change to any status
                'warehouse': ['production_status', 'order_status_limited'],
                'warehouse_worker': ['production_status_limited'],
                'delivery': ['order_status_delivery']
            }
            
            new_order_status = request.data.get('order_status')
            new_production_status = request.data.get('production_status')
            
            # Check permissions based on what's being updated
            if new_order_status:
                if not self._can_update_order_status(user, order, new_order_status):
                    return Response({
                        'error': f'Permission denied: {user.role} cannot change order status to {new_order_status}',
                        'your_role': user.role,
                        'current_status': order.order_status,
                        'requested_status': new_order_status
                    }, status=status.HTTP_403_FORBIDDEN)
            
            if new_production_status:
                if not self._can_update_production_status(user, order, new_production_status):
                    return Response({
                        'error': f'Permission denied: {user.role} cannot change production status to {new_production_status}',
                        'your_role': user.role,
                        'current_status': order.production_status,
                        'requested_status': new_production_status
                    }, status=status.HTTP_403_FORBIDDEN)
            
            # Update the order with validation
            serializer = OrderStatusUpdateSerializer(order, data=request.data, partial=True, context={'request': request})
            
            if serializer.is_valid():
                # Log the status change
                old_order_status = order.order_status
                old_production_status = order.production_status
                
                serializer.save()
                
                # Create history entry
                changes = []
                if new_order_status and new_order_status != old_order_status:
                    changes.append(f"Order status: {old_order_status} → {new_order_status}")
                if new_production_status and new_production_status != old_production_status:
                    changes.append(f"Production status: {old_production_status} → {new_production_status}")
                
                if changes:
                    OrderHistory.objects.create(
                        order=order,
                        user=user,
                        action="Status updated",
                        details="; ".join(changes)
                    )
                
                return Response({
                    'message': 'Order status updated successfully',
                    'order_status': order.order_status,
                    'production_status': order.production_status,
                    'updated_by': user.get_full_name() or user.username,
                    'changes': changes
                })
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            import traceback
            print(f"Status update error: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            return Response({
                'error': f'Status update failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def update_production_status(self, request, pk=None):
        """Update production status specifically for warehouse operations"""
        try:
            order = self.get_object()
            user = request.user
            
            # Check if user has permission to update production status
            if user.role not in ['owner', 'admin', 'warehouse', 'warehouse_worker']:
                return Response({
                    'error': 'Permission denied: Only warehouse staff can update production status'
                }, status=status.HTTP_403_FORBIDDEN)
            
            new_production_status = request.data.get('production_status')
            if not new_production_status:
                return Response({
                    'error': 'Production status is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate production status
            valid_statuses = [choice[0] for choice in Order.PRODUCTION_STATUS_CHOICES]
            if new_production_status not in valid_statuses:
                return Response({
                    'error': f'Invalid production status: {new_production_status}. Valid statuses: {", ".join(valid_statuses)}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Store old value for logging
            old_production_status = order.production_status
            
            # Update production status
            order.production_status = new_production_status
            
            # Special handling for completed status
            if new_production_status == 'completed':
                order.order_status = 'order_ready'
                # Set expected delivery date if not already set
                if not order.expected_delivery_date:
                    from datetime import date, timedelta
                    order.expected_delivery_date = date.today() + timedelta(days=3)
            
            # Special handling for ready_for_delivery status
            elif new_production_status == 'ready_for_delivery':
                order.order_status = 'order_ready'
            
            order.save()
            
            # Create history entry
            changes = [f"Production status: {old_production_status} → {new_production_status}"]
            if order.order_status != old_production_status:
                changes.append(f"Order status: {order.order_status}")
            
            OrderHistory.objects.create(
                order=order,
                user=user,
                action="Production status updated",
                details="; ".join(changes)
            )
            
            return Response({
                'message': 'Production status updated successfully',
                'order_number': order.order_number,
                'production_status': order.production_status,
                'order_status': order.order_status,
                'updated_by': user.get_full_name() or user.username,
                'changes': changes
            })
            
        except Exception as e:
            import traceback
            print(f"Production status update error: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            return Response({
                'error': f'Production status update failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _can_update_order_status(self, user, order, new_status):
        """Check if user can update order status"""
        # Owner and admin can change to any status
        if user.role in ['owner', 'admin']:
            return True
        
        # Warehouse roles: allow controlled transitions
        if user.role in ['warehouse_worker', 'warehouse']:
            current_status = order.order_status
            # Workers can only mark deposit_paid -> order_ready
            if user.role == 'warehouse_worker':
                return current_status == 'deposit_paid' and new_status == 'order_ready'
            # Warehouse (manager) can also move order_ready -> out_for_delivery
            if user.role == 'warehouse':
                allowed_transitions = {
                    'deposit_paid': ['order_ready'],
                    'order_ready': ['out_for_delivery'],
                }
                return new_status in allowed_transitions.get(current_status, [])
        
        # Delivery can update delivery-related statuses
        if user.role == 'delivery':
            current_status = order.order_status
            allowed_transitions = {
                'order_ready': ['out_for_delivery'],
                'out_for_delivery': ['delivered']
            }
            return new_status in allowed_transitions.get(current_status, [])
        
        return False

    def _can_update_production_status(self, user, order, new_status):
        """Check if user can update production status"""
        # Owner and admin can change to any production status
        if user.role in ['owner', 'admin']:
            return True
        
        # Warehouse roles can update production stages
        if user.role in ['warehouse_worker', 'warehouse']:
            # Define allowed production status transitions
            production_flow = [
                'not_started', 'cutting', 'sewing', 'finishing', 'quality_check', 'completed'
            ]
            current_index = production_flow.index(order.production_status) if order.production_status in production_flow else 0
            new_index = production_flow.index(new_status) if new_status in production_flow else -1
            
            # Can only move forward in production flow or stay at same stage
            return new_index >= current_index and new_index != -1
        
        return False

    def retrieve(self, request, *args, **kwargs):
        """Override retrieve to add debugging"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        print(f"RETRIEVING ORDER {instance.id}:")
        print(f"Order items count: {len(data.get('items', []))}")
        print(f"Order items data: {data.get('items', [])}")
        return Response(data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def escalate_priority(self, request, pk=None):
        """Escalate order to priority (owner only)"""
        order = self.get_object()
        user = request.user
        
        if order.escalate_to_priority(user):
            order.save()
            return Response({
                'message': 'Order escalated to priority successfully',
                'queue_position': order.queue_position,
                'is_priority_order': order.is_priority_order
            })
        else:
            return Response({
                'error': 'You do not have permission to escalate this order or order is not eligible'
            }, status=status.HTTP_403_FORBIDDEN)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def create_task(self, request, pk=None):
        """Create a task within a specific order"""
        from tasks.models import Task, TaskType, create_notification
        from tasks.serializers import TaskSerializer
        from users.models import User
        
        order = self.get_object()
        user = request.user
        
        # Check if user can create tasks
        if not user.can_manage_tasks:
            return Response({
                'error': 'You do not have permission to create tasks'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Validate input data
        required_fields = ['title', 'assigned_to_id']
        for field in required_fields:
            if field not in request.data:
                return Response({
                    'error': f'Missing required field: {field}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get task type by id or name
            task_type = None
            task_type_id = request.data.get('task_type_id')
            task_type_name = request.data.get('task_type_name')
            if task_type_id is not None:
                task_type = TaskType.objects.get(id=task_type_id)
            elif task_type_name:
                task_type = TaskType.objects.get(name=task_type_name)
            else:
                return Response({'error': 'Missing required field: task_type_id or task_type_name'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Get assigned worker
            assigned_worker = User.objects.get(id=request.data['assigned_to_id'])
            if not assigned_worker.is_warehouse_worker:
                return Response({
                    'error': 'Can only assign tasks to warehouse workers'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create the task
            task_data = {
                'title': request.data['title'],
                'description': request.data.get('description', ''),
                'task_type': task_type,
                'order': order,
                'assigned_to': assigned_worker,
                'assigned_by': user,
                'priority': request.data.get('priority', 'normal'),
                'instructions': request.data.get('instructions', ''),
                'materials_needed': request.data.get('materials_needed', ''),
                'estimated_duration': timedelta(minutes=request.data.get('estimated_duration', 60)),
                'order_item_id': request.data.get('order_item_id'),
            }
            
            # Set deadline if provided
            if 'deadline' in request.data:
                from django.utils.dateparse import parse_datetime
                deadline = parse_datetime(request.data['deadline'])
                if deadline:
                    task_data['deadline'] = deadline
                    task_data['due_date'] = deadline
            
            task = Task.objects.create(**task_data)
            
            # Send notification to assigned worker
            create_notification(
                user=assigned_worker,
                message=f"New task assigned: {task.title} for Order {order.order_number}",
                notification_type='task_assigned',
                priority='normal',
                task=task,
                order=order
            )
            
            # Return exact structure expected by frontend
            return Response({
                'message': 'Task created successfully',
                'task': {
                    'id': task.id,
                    'title': task.title,
                    'task_type': task.task_type.name,
                    'assigned_to': assigned_worker.get_full_name() or assigned_worker.username,
                    'status': task.status,
                    'priority': task.priority,
                    'order': order.id,
                    'order_number': order.order_number,
                    'deadline': (task.deadline or task.due_date).isoformat() if (task.deadline or task.due_date) else None,
                    'created_at': task.created_at.isoformat(),
                }
            }, status=status.HTTP_201_CREATED)
            
        except TaskType.DoesNotExist:
            return Response({
                'error': 'Task type not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except User.DoesNotExist:
            return Response({
                'error': 'Assigned user not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': f'Failed to create task: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def queue_status(self, request):
        """Get current production queue status"""
        queue_orders = Order.objects.filter(
            order_status='deposit_paid',
            queue_position__isnull=False
        ).order_by('queue_position')
        
        queue_data = []
        for order in queue_orders:
            queue_data.append({
                'id': order.id,
                'order_number': order.order_number,
                'customer_name': order.customer.name if order.customer else order.customer_name,
                'queue_position': order.queue_position,
                'deposit_paid_date': order.deposit_paid_date,
                'days_in_queue': order.days_in_queue(),
                'estimated_completion_date': order.estimated_completion_date,
                'is_priority_order': order.is_priority_order,
                'is_queue_expired': order.is_queue_expired()
            })
        
        return Response({
            'total_orders_in_queue': len(queue_data),
            'queue': queue_data
        })
    
    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated])
    def set_delivery_date(self, request, pk=None):
        """Set delivery date (only when order is ready)"""
        order = self.get_object()
        
        if not order.can_set_delivery_date():
            return Response({
                'error': 'Delivery date can only be set when order status is "order_ready"'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        delivery_date = request.data.get('delivery_date')
        if not delivery_date:
            return Response({
                'error': 'delivery_date is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        order.expected_delivery_date = delivery_date
        order.save()
        
        return Response({
            'message': 'Delivery date set successfully',
            'expected_delivery_date': order.expected_delivery_date
        })

    def list(self, request, *args, **kwargs):
        if not Order.objects.exists():
            # Return mock data for frontend testing
            mock_data = [
                {
                    'id': 1,
                    'order_number': 'OOX000101',
                    'customer': {
                        'id': 1,
                        'name': 'John Doe',
                        'phone': '08012345678',
                        'email': 'john@example.com',
                        'address': '123 Main St',
                        'created_at': '2024-07-01T10:00:00Z',
                        'updated_at': '2024-07-01T10:00:00Z',
                    },
                    'product_name': 'Custom Sofa',
                    'product_description': 'Blue, 3-seater',
                    'quantity': 2,
                    'unit_price': 'R50000.00',
                    'total_amount': 'R100000.00',
                    'deposit_amount': 'R50000.00',
                    'balance_amount': 'R50000.00',
                    'payment_status': 'deposit_only',
                    'order_status': 'pending',
                    'order_date': '2024-07-01T10:00:00Z',
                    'expected_delivery_date': '2024-07-10',
                    'actual_delivery_date': None,
                    'created_by': None,
                    'assigned_to_warehouse': None,
                    'assigned_to_delivery': None,
                    'admin_notes': '',
                    'warehouse_notes': '',
                    'delivery_notes': '',
                    'created_at': '2024-07-01T10:00:00Z',
                    'updated_at': '2024-07-01T10:00:00Z',
                }
            ]
            return Response(mock_data)
        return super().list(request, *args, **kwargs)

    def perform_create(self, serializer):
        try:
            items_data = self.request.data.get('items', [])
            serializer.save(
                created_by=self.request.user,
                items_data=items_data
            )
        except Exception as e:
            print("ORDER CREATE ERROR:", e)
            traceback.print_exc(file=sys.stdout)
            # Optionally, you can raise or return a more informative error
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'detail': f'Order creation failed: {str(e)}'})

    def perform_update(self, serializer):
        try:
            items_data = self.request.data.get('items', [])
            serializer.save(items_data=items_data)
        except Exception as e:
            print("ORDER UPDATE ERROR:", e)
            import sys, traceback
            traceback.print_exc(file=sys.stdout)
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'detail': f'Order update failed: {str(e)}'})

    @action(detail=True, methods=['post'])
    def assign_warehouse(self, request, pk=None):
        order = self.get_object()
        warehouse_user_id = request.data.get('warehouse_user_id')
        
        if warehouse_user_id:
            try:
                from users.models import User
                warehouse_user = User.objects.get(id=warehouse_user_id, role='warehouse')
                order.assigned_to_warehouse = warehouse_user
                order.save()
                
                OrderHistory.objects.create(
                    order=order,
                    user=request.user,
                    action="Assigned to warehouse",
                    details=f"Assigned to {warehouse_user.username}"
                )
                
                return Response({'message': 'Order assigned to warehouse successfully'})
            except User.DoesNotExist:
                return Response({'error': 'Invalid warehouse user'}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({'error': 'warehouse_user_id is required'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def assign_delivery(self, request, pk=None):
        order = self.get_object()
        delivery_user_id = request.data.get('delivery_user_id')
        
        if delivery_user_id:
            try:
                from users.models import User
                delivery_user = User.objects.get(id=delivery_user_id, role='delivery')
                order.assigned_to_delivery = delivery_user
                order.save()
                
                OrderHistory.objects.create(
                    order=order,
                    user=request.user,
                    action="Assigned to delivery",
                    details=f"Assigned to {delivery_user.username}"
                )
                
                return Response({'message': 'Order assigned to delivery successfully'})
            except User.DoesNotExist:
                return Response({'error': 'Invalid delivery user'}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({'error': 'delivery_user_id is required'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def warehouse_orders(self, request):
        """Get orders ready for warehouse processing"""
        # Orders that are paid and ready for production
        warehouse_orders = self.get_queryset().filter(
            order_status__in=['deposit_paid', 'order_ready'],
            production_status__in=['not_started', 'cutting', 'sewing', 'finishing', 'quality_check']
        ).select_related('customer').prefetch_related('items__product', 'tasks')
        
        # Organize by priority/urgency
        today = timezone.now().date()
        
        orders_data = []
        for order in warehouse_orders:
            # Calculate estimated completion date based on tasks
            total_estimated_time = timedelta(0)
            assigned_tasks = order.tasks.all()
            
            for task in assigned_tasks:
                total_estimated_time += task.estimated_duration
            
            # Determine urgency
            days_until_deadline = (order.delivery_deadline - today).days if order.delivery_deadline else 999
            urgency = 'low'
            if days_until_deadline <= 2:
                urgency = 'critical'
            elif days_until_deadline <= 5:
                urgency = 'high'
            elif days_until_deadline <= 10:
                urgency = 'medium'
            
            # Count tasks by status
            task_counts = {
                'total': assigned_tasks.count(),
                'not_started': assigned_tasks.filter(status='assigned').count(),
                'in_progress': assigned_tasks.filter(status='started').count(),
                'completed': assigned_tasks.filter(status__in=['completed', 'approved']).count(),
            }
            
            orders_data.append({
                'id': order.id,
                'order_number': order.order_number,
                'customer_name': order.customer.name if order.customer else order.customer_name,
                'order_status': order.order_status,
                'production_status': order.production_status,
                'delivery_deadline': order.delivery_deadline,
                'days_until_deadline': days_until_deadline,
                'urgency': urgency,
                'total_amount': float(order.total_amount),
                'estimated_completion_time': str(total_estimated_time),
                'task_counts': task_counts,
                'items_count': order.items.count(),
                'created_at': order.created_at,
                'is_priority_order': order.is_priority_order,
                'can_create_tasks': True  # Frontend expects this field
            })
        
        # Sort by urgency and deadline
        urgency_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        orders_data.sort(key=lambda x: (urgency_order[x['urgency']], x['days_until_deadline']))
        
        return Response({
            'orders': orders_data,
            'summary': {
                'total_orders': len(orders_data),
                'critical': len([o for o in orders_data if o['urgency'] == 'critical']),
                'high': len([o for o in orders_data if o['urgency'] == 'high']),
                'medium': len([o for o in orders_data if o['urgency'] == 'medium']),
                'low': len([o for o in orders_data if o['urgency'] == 'low']),
            }
        })
    
    @action(detail=True, methods=['get'])
    def order_details_for_tasks(self, request, pk=None):
        """Get detailed order information for task assignment"""
        order = self.get_object()
        
        # Get order items with product details
        items_data = []
        for item in order.items.all():
            # Get required materials for this product
            required_materials = []
            if hasattr(item.product, 'required_materials'):
                for pm in item.product.required_materials.all():
                    required_materials.append({
                        'material_id': pm.material.id,
                        'material_name': pm.material.name,
                        'quantity_required': float(pm.quantity_required),
                        'unit': pm.material.get_unit_display(),
                        'total_needed': float(pm.quantity_required * item.quantity)
                    })
            
            items_data.append({
                'id': item.id,
                'product_name': item.product.product_name,
                'quantity': item.quantity,
                'unit_price': float(item.unit_price),
                'fabric_letter': item.assigned_fabric_letter,
                'color_code': item.assigned_color_code,
                'fabric_name': item.fabric_name,
                'color_name': item.color_name,
                'required_materials': required_materials
            })
        
        # Get existing tasks for this order
        existing_tasks = order.tasks.select_related('assigned_to', 'task_type').all()
        tasks_data = []
        for task in existing_tasks:
            tasks_data.append({
                'id': task.id,
                'title': task.title,
                'task_type': task.task_type.name,
                'assigned_to': task.assigned_to.get_full_name() or task.assigned_to.username,
                'assigned_to_id': task.assigned_to.id,
                'status': task.status,
                'priority': task.priority,
                'estimated_duration': str(task.estimated_duration),
                'created_at': task.created_at
            })
        
        return Response({
            'order': {
                'id': order.id,
                'order_number': order.order_number,
                'customer_name': order.customer.name if order.customer else order.customer_name,
                'order_status': order.order_status,
                'production_status': order.production_status,
                'delivery_deadline': order.delivery_deadline,
                'total_amount': float(order.total_amount),
                'created_at': order.created_at,
                'admin_notes': order.admin_notes,
                'warehouse_notes': order.warehouse_notes,
            },
            'items': items_data,
            'existing_tasks': tasks_data,
            'task_summary': {
                'total_tasks': len(tasks_data),
                'completed': len([t for t in tasks_data if t['status'] in ['completed', 'approved']]),
                'in_progress': len([t for t in tasks_data if t['status'] == 'started']),
                'pending': len([t for t in tasks_data if t['status'] == 'assigned'])
            }
        })
    
    @action(detail=True, methods=['post'])
    def assign_tasks_to_order(self, request, pk=None):
        """Assign multiple tasks to an order"""
        order = self.get_object()
        tasks_data = request.data.get('tasks', [])
        
        if not tasks_data:
            return Response({'error': 'No tasks provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        created_tasks = []
        errors = []
        
        for task_data in tasks_data:
            try:
                from users.models import User
                from tasks.models import TaskType, Task
                
                # Get required data
                assigned_to = User.objects.get(id=task_data['assigned_to_id'])
                if not assigned_to.is_warehouse_worker:
                    raise User.DoesNotExist('Assigned user is not a warehouse worker')
                task_type = None
                if 'task_type_id' in task_data and task_data['task_type_id'] is not None:
                    task_type = TaskType.objects.get(id=task_data['task_type_id'])
                elif 'task_type_name' in task_data and task_data['task_type_name']:
                    task_type = TaskType.objects.get(name=task_data['task_type_name'])
                else:
                    raise TaskType.DoesNotExist('task_type_id or task_type_name required')
                
                # Create the task
                task = Task.objects.create(
                    title=task_data.get('title', f"{task_type.name} - {order.order_number}"),
                    description=task_data.get('description', f"{task_type.name} for order {order.order_number}"),
                    task_type=task_type,
                    assigned_to=assigned_to,
                    assigned_by=request.user,
                    order=order,
                    order_item_id=task_data.get('order_item_id'),  # Optional: specific item
                    priority=task_data.get('priority', 'normal'),
                    due_date=task_data.get('due_date'),
                    estimated_duration=timedelta(minutes=task_type.estimated_duration_minutes)
                )
                
                # If materials are specified, create task materials
                if 'required_materials' in task_data:
                    from tasks.models import TaskMaterial
                    from inventory.models import Material
                    
                    for material_data in task_data['required_materials']:
                        material = Material.objects.get(id=material_data['material_id'])
                        TaskMaterial.objects.create(
                            task=task,
                            material=material,
                            quantity_needed=material_data['quantity_needed']
                        )
                
                created_tasks.append({
                    'task_id': task.id,
                    'title': task.title,
                    'assigned_to': assigned_to.get_full_name() or assigned_to.username,
                    'task_type': task_type.name,
                    'status': 'created'
                })
                
            except (User.DoesNotExist, TaskType.DoesNotExist) as e:
                errors.append({
                    'task_data': task_data,
                    'error': str(e)
                })
            except Exception as e:
                errors.append({
                    'task_data': task_data,
                    'error': f'Unexpected error: {str(e)}'
                })
        
        # Update order production status if tasks were created
        if created_tasks and order.production_status == 'not_started':
            order.production_status = 'cutting'  # or appropriate first stage
            order.save()
        
        return Response({
            'message': f'{len(created_tasks)} tasks created successfully',
            'created_tasks': created_tasks,
            'errors': errors,
            'order_id': order.id,
            'order_number': order.order_number
        })
    
    @action(detail=False, methods=['get'])
    def owner_dashboard_orders(self, request):
        """Owner dashboard: Complete order overview with all controls"""
        user = request.user
        
        if user.role != 'owner':
            return Response({'error': 'Access denied: Owner access required'}, status=status.HTTP_403_FORBIDDEN)
        
        # Get all orders with comprehensive statistics
        all_orders = self.get_queryset()
        
        # Order status breakdown
        status_breakdown = {}
        for status_choice in Order.ORDER_STATUS_CHOICES:
            status_code = status_choice[0]
            status_breakdown[status_code] = all_orders.filter(order_status=status_code).count()
        
        # Production status breakdown
        production_breakdown = {}
        for prod_choice in Order.PRODUCTION_STATUS_CHOICES:
            prod_code = prod_choice[0]
            production_breakdown[prod_code] = all_orders.filter(production_status=prod_code).count()
        
        # Financial overview
        from django.db.models import Sum
        financial_stats = all_orders.aggregate(
            total_revenue=Sum('total_amount'),
            total_deposits=Sum('deposit_amount'),
            total_balance=Sum('balance_amount')
        )
        
        # Recent orders
        recent_orders = all_orders.order_by('-created_at')[:10]
        
        # Overdue orders
        from django.utils import timezone
        overdue_orders = all_orders.filter(
            delivery_deadline__lt=timezone.now().date(),
            order_status__in=['deposit_pending', 'deposit_paid', 'order_ready', 'out_for_delivery']
        )
        
        # Priority orders
        priority_orders = all_orders.filter(is_priority_order=True)
        
        return Response({
            'dashboard_type': 'owner',
            'permissions': {
                'can_create': True,
                'can_edit': True,
                'can_delete': True,
                'can_change_status': True,
                'can_assign_users': True,
                'can_escalate_priority': True
            },
            'statistics': {
                'total_orders': all_orders.count(),
                'status_breakdown': status_breakdown,
                'production_breakdown': production_breakdown,
                'financial_stats': {
                    'total_revenue': float(financial_stats['total_revenue'] or 0),
                    'total_deposits': float(financial_stats['total_deposits'] or 0),
                    'total_balance': float(financial_stats['total_balance'] or 0)
                },
                'overdue_count': overdue_orders.count(),
                'priority_count': priority_orders.count()
            },
            'recent_orders': OrderListSerializer(recent_orders, many=True).data,
            'overdue_orders': OrderListSerializer(overdue_orders, many=True).data,
            'priority_orders': OrderListSerializer(priority_orders, many=True).data
        })
    
    @action(detail=False, methods=['get'])
    def admin_dashboard_orders(self, request):
        """Admin dashboard: Order management with limited controls"""
        user = request.user
        
        if user.role != 'admin':
            return Response({'error': 'Access denied: Admin access required'}, status=status.HTTP_403_FORBIDDEN)
        
        # Get all orders (admin can see all)
        all_orders = self.get_queryset()
        
        # Orders needing attention
        pending_orders = all_orders.filter(order_status='deposit_pending')
        in_production = all_orders.filter(production_status__in=['cutting', 'sewing', 'finishing'])
        ready_for_delivery = all_orders.filter(order_status='order_ready')
        
        # Recent activity
        recent_orders = all_orders.order_by('-updated_at')[:15]
        
        return Response({
            'dashboard_type': 'admin',
            'permissions': {
                'can_create': True,
                'can_edit': True,
                'can_delete': True,
                'can_change_status': True,
                'can_assign_users': True,
                'can_escalate_priority': False
            },
            'statistics': {
                'total_orders': all_orders.count(),
                'pending_orders': pending_orders.count(),
                'in_production': in_production.count(),
                'ready_for_delivery': ready_for_delivery.count()
            },
            'pending_orders': OrderListSerializer(pending_orders, many=True).data,
            'in_production': OrderListSerializer(in_production, many=True).data,
            'ready_for_delivery': OrderListSerializer(ready_for_delivery, many=True).data,
            'recent_orders': OrderListSerializer(recent_orders, many=True).data
        })
    
    @action(detail=False, methods=['get'])
    def warehouse_dashboard_orders(self, request):
        """Warehouse dashboard: Production-focused order view"""
        user = request.user
        
        if user.role not in ['warehouse_worker', 'warehouse']:
            return Response({'error': 'Access denied: Warehouse access required'}, status=status.HTTP_403_FORBIDDEN)
        
        # Get orders relevant to warehouse
        warehouse_orders = self.get_queryset()
        
        # Orders by production stage
        not_started = warehouse_orders.filter(production_status='not_started')
        cutting = warehouse_orders.filter(production_status='cutting')
        sewing = warehouse_orders.filter(production_status='sewing')
        finishing = warehouse_orders.filter(production_status='finishing')
        quality_check = warehouse_orders.filter(production_status='quality_check')
        completed = warehouse_orders.filter(production_status='completed')
        
        # Orders assigned to current user
        my_orders = warehouse_orders.filter(assigned_to_warehouse=user) if user.role != 'warehouse_worker' else warehouse_orders
        
        return Response({
            'dashboard_type': 'warehouse',
            'permissions': {
                'can_create': False,
                'can_edit': False,
                'can_delete': False,
                'can_change_status': True,  # Only production status
                'can_assign_users': False,
                'can_escalate_priority': False
            },
            'statistics': {
                'total_orders': warehouse_orders.count(),
                'not_started': not_started.count(),
                'cutting': cutting.count(),
                'sewing': sewing.count(),
                'finishing': finishing.count(),
                'quality_check': quality_check.count(),
                'completed': completed.count()
            },
            'production_stages': {
                'not_started': OrderListSerializer(not_started, many=True).data,
                'cutting': OrderListSerializer(cutting, many=True).data,
                'sewing': OrderListSerializer(sewing, many=True).data,
                'finishing': OrderListSerializer(finishing, many=True).data,
                'quality_check': OrderListSerializer(quality_check, many=True).data,
                'completed': OrderListSerializer(completed, many=True).data
            },
            'my_orders': OrderListSerializer(my_orders, many=True).data if user.role != 'warehouse_worker' else []
        })
    
    @action(detail=False, methods=['get'])
    def delivery_dashboard_orders(self, request):
        """Delivery dashboard: Delivery-focused order view"""
        user = request.user
        
        if user.role != 'delivery':
            return Response({'error': 'Access denied: Delivery access required'}, status=status.HTTP_403_FORBIDDEN)
        
        # Get orders relevant to delivery
        delivery_orders = self.get_queryset()
        
        # Orders by delivery status
        ready_for_delivery = delivery_orders.filter(order_status='order_ready')
        out_for_delivery = delivery_orders.filter(order_status='out_for_delivery')
        delivered = delivery_orders.filter(order_status='delivered')
        
        # Orders assigned to current user
        my_deliveries = delivery_orders.filter(assigned_to_delivery=user)
        
        # Today's deliveries
        from django.utils import timezone
        today = timezone.now().date()
        todays_deliveries = delivery_orders.filter(
            expected_delivery_date=today,
            order_status__in=['order_ready', 'out_for_delivery']
        )
        
        return Response({
            'dashboard_type': 'delivery',
            'permissions': {
                'can_create': False,
                'can_edit': False,
                'can_delete': False,
                'can_change_status': True,  # Only delivery status
                'can_assign_users': False,
                'can_escalate_priority': False
            },
            'statistics': {
                'total_orders': delivery_orders.count(),
                'ready_for_delivery': ready_for_delivery.count(),
                'out_for_delivery': out_for_delivery.count(),
                'delivered': delivered.count(),
                'todays_deliveries': todays_deliveries.count()
            },
            'delivery_stages': {
                'ready_for_delivery': OrderListSerializer(ready_for_delivery, many=True).data,
                'out_for_delivery': OrderListSerializer(out_for_delivery, many=True).data,
                'delivered': OrderListSerializer(delivered[:10], many=True).data  # Recent deliveries
            },
            'my_deliveries': OrderListSerializer(my_deliveries, many=True).data,
            'todays_deliveries': OrderListSerializer(todays_deliveries, many=True).data
        })
    
    @action(detail=True, methods=['post'])
    def cancel_order(self, request, pk=None):
        """Cancel an order (owner/admin only)"""
        user = request.user
        order = self.get_object()
        
        if user.role not in ['owner', 'admin']:
            return Response({
                'error': 'Permission denied: Only Owner and Admin can cancel orders'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check if order can be cancelled
        if order.order_status in ['delivered', 'cancelled']:
            return Response({
                'error': f'Cannot cancel order: Order is already {order.order_status}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Cancel the order
        reason = request.data.get('reason', 'Cancelled by admin')
        old_status = order.order_status
        order.order_status = 'cancelled'
        order.save()
        
        # Log the cancellation
        OrderHistory.objects.create(
            order=order,
            user=user,
            action="Order cancelled",
            details=f"Cancelled from {old_status}. Reason: {reason}"
        )
        
        return Response({
            'message': 'Order cancelled successfully',
            'order_number': order.order_number,
            'previous_status': old_status,
            'cancelled_by': user.get_full_name() or user.username,
            'reason': reason
        })

    @action(detail=False, methods=['get'])
    def admin_warehouse_overview(self, request):
        """Read-only warehouse overview for admin dashboard"""
        try:
            user = request.user
            
            # Check permissions - only admin and owner can access
            if user.role not in ['admin', 'owner']:
                return Response({
                    'error': 'Permission denied: Only Admin and Owner can view warehouse overview'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Get warehouse-related orders
            warehouse_orders = self.get_queryset().filter(
                order_status__in=['deposit_paid', 'order_ready'],
                production_status__in=['cutting', 'sewing', 'finishing', 'quality_check', 'completed']
            )
            
            # Production pipeline stats
            production_stats = {
                'cutting': warehouse_orders.filter(production_status='cutting').count(),
                'sewing': warehouse_orders.filter(production_status='sewing').count(),
                'finishing': warehouse_orders.filter(production_status='finishing').count(),
                'quality_check': warehouse_orders.filter(production_status='quality_check').count(),
                'completed': warehouse_orders.filter(production_status='completed').count(),
                'total_in_production': warehouse_orders.count()
            }

            # Get active tasks from warehouse
            try:
                from tasks.models import Task
                active_tasks = Task.objects.filter(
                    status__in=['pending', 'in_progress', 'paused'],
                    assigned_to__role__in=['warehouse_worker', 'warehouse']
                )
        
                task_stats = {
                    'total_active_tasks': active_tasks.count(),
                    'pending_tasks': active_tasks.filter(status='pending').count(),
                    'in_progress_tasks': active_tasks.filter(status='in_progress').count(),
                    'paused_tasks': active_tasks.filter(status='paused').count()
                }
            except ImportError:
                # Tasks app not available
                task_stats = {
                    'total_active_tasks': 0,
                    'pending_tasks': 0,
                    'in_progress_tasks': 0,
                    'paused_tasks': 0
                }
        
            # Warehouse workforce
            try:
                from users.models import User
                warehouse_workers = User.objects.filter(
                    role__in=['warehouse_worker', 'warehouse'],
                    is_active=True
                )
        
                workforce_stats = {
                    'total_workers': warehouse_workers.count(),
                    'managers': warehouse_workers.filter(role='warehouse').count(),
                    'workers': warehouse_workers.filter(role__in=['warehouse_worker', 'warehouse']).count(),
                    'active_workers': warehouse_workers.filter(
                        id__in=active_tasks.values('assigned_to').distinct()
                    ).count() if 'active_tasks' in locals() else 0
                }
            except ImportError:
                workforce_stats = {
                    'total_workers': 0,
                    'managers': 0,
                    'workers': 0,
                    'active_workers': 0
                }
        
            # Stock alerts (if inventory system exists)
            stock_alerts = []
            try:
                from inventory.models import Material
                from django.db.models import F
                low_stock_materials = Material.objects.filter(
                    current_stock__lte=F('minimum_stock_level')
                )[:10]
                
                for material in low_stock_materials:
                    stock_alerts.append({
                        'material_name': material.name,
                        'current_stock': material.current_stock,
                        'minimum_level': material.minimum_stock_level,
                        'shortage': material.minimum_stock_level - material.current_stock
                    })
            except ImportError:
                # Inventory system not available
                pass
        
            # Recent warehouse activities
            warehouse_activities = OrderHistory.objects.filter(
                order__in=warehouse_orders,
                action__icontains='production'
            ).select_related('order', 'user').order_by('-timestamp')[:10]
        
            activities_data = []
            for activity in warehouse_activities:
                activities_data.append({
                    'order_number': activity.order.order_number,
                    'action': activity.action,
                    'details': activity.details,
                    'user': activity.user.get_full_name() if activity.user else 'System',
                    'timestamp': activity.timestamp
                })
        
            # Bottleneck analysis
            bottlenecks = []
            if production_stats['cutting'] > 10:
                bottlenecks.append({
                    'stage': 'Cutting',
                    'count': production_stats['cutting'],
                    'message': 'High number of orders in cutting stage'
                })
            if production_stats['sewing'] > 15:
                bottlenecks.append({
                    'stage': 'Sewing',
                    'count': production_stats['sewing'],
                    'message': 'Potential bottleneck in sewing department'
                })
            if production_stats['quality_check'] > 8:
                bottlenecks.append({
                    'stage': 'Quality Check',
                    'count': production_stats['quality_check'],
                    'message': 'Quality check backlog detected'
                })
        
            return Response({
                'production_pipeline': production_stats,
                'task_overview': task_stats,
                'workforce_summary': workforce_stats,
                'stock_alerts': stock_alerts,
                'recent_activities': activities_data,
                'bottleneck_analysis': bottlenecks,
                'navigation_message': {
                    'title': 'Warehouse Operations',
                    'description': 'For detailed warehouse management and operations control, please use the Warehouse Dashboard.',
                    'action_url': '/warehouse',
                    'action_text': 'Go to Warehouse Dashboard'
                },
                'last_updated': timezone.now()
            }) 
        except Exception as e:
            import traceback
            return Response({
                'error': f'Failed to fetch warehouse overview: {str(e)}',
                'traceback': traceback.format_exc()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='status_options')
    def status_options(self, request):
        """Expose status dropdown options to frontend consumers."""
        order_statuses = [{'value': choice[0], 'label': choice[1]} for choice in Order.ORDER_STATUS_CHOICES]
        production_statuses = [{'value': choice[0], 'label': choice[1]} for choice in Order.PRODUCTION_STATUS_CHOICES]
        return Response({
            'status_options': {
                'order_statuses': order_statuses,
                'production_statuses': production_statuses
            }
        })

class PaymentProofViewSet(viewsets.ModelViewSet):
    queryset = PaymentProof.objects.all()
    serializer_class = PaymentProofSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['order', 'payment_type']
    ordering = ['-uploaded_at']

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)


class OrderHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = OrderHistory.objects.all()
    serializer_class = OrderHistorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['order', 'user', 'action']
    ordering = ['-timestamp']

class ColorViewSet(viewsets.ModelViewSet):
    queryset = Color.objects.all()
    serializer_class = ColorSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering = ['name']


class FabricViewSet(viewsets.ModelViewSet):
    queryset = Fabric.objects.all()
    serializer_class = FabricSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering = ['name']

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, CanCreateProducts]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['product_name', 'name', 'description', 'model_code']
    ordering_fields = ['created_at', 'product_name', 'unit_price', 'stock']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        serializer.save()

class ColorReferenceViewSet(viewsets.ModelViewSet):
    queryset = ColorReference.objects.all()
    serializer_class = ColorReferenceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering = ['color_code']


class FabricReferenceViewSet(viewsets.ModelViewSet):
    queryset = FabricReference.objects.all()
    serializer_class = FabricReferenceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering = ['fabric_letter']

class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['order', 'product', 'color', 'fabric']
    ordering = ['-id']