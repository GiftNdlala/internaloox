from django.shortcuts import render
import sys
import traceback
from django.http import JsonResponse
from rest_framework import status, viewsets, filters
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import AllowAny, IsAuthenticated
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

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [AllowAny]
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

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['payment_status', 'order_status', 'created_by', 'assigned_to_warehouse', 'assigned_to_delivery']
    search_fields = ['order_number', 'customer__name']
    ordering_fields = ['created_at', 'expected_delivery_date', 'total_amount']
    ordering = ['-created_at']

    def get_serializer_class(self):
        # Always use OrderSerializer for retrieve, update, partial_update, and create
        if self.action in ['list']:
            return OrderListSerializer
        return OrderSerializer

    def retrieve(self, request, *args, **kwargs):
        """Override retrieve to add debugging"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        print(f"RETRIEVING ORDER {instance.id}:")
        print(f"Order items count: {len(data.get('items', []))}")
        print(f"Order items data: {data.get('items', [])}")
        return Response(data)

    def get_queryset(self):
        return Order.objects.all()
    
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
        required_fields = ['title', 'task_type_id', 'assigned_to_id']
        for field in required_fields:
            if field not in request.data:
                return Response({
                    'error': f'Missing required field: {field}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get task type
            task_type = TaskType.objects.get(id=request.data['task_type_id'])
            
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
            
            # Serialize and return task data
            serializer = TaskSerializer(task)
            return Response({
                'message': 'Task created successfully',
                'task': serializer.data
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
    def update_status(self, request, pk=None):
        order = self.get_object()
        serializer = OrderStatusUpdateSerializer(order, data=request.data, partial=True, context={'request': request})
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
                'is_priority_order': order.is_priority_order
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
                assigned_to = User.objects.get(id=task_data['assigned_to_id'], role='warehouse')
                task_type = TaskType.objects.get(id=task_data['task_type_id'])
                
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

class PaymentProofViewSet(viewsets.ModelViewSet):
    queryset = PaymentProof.objects.all()
    serializer_class = PaymentProofSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['order', 'payment_type']
    ordering = ['-uploaded_at']

    def list(self, request, *args, **kwargs):
        if not PaymentProof.objects.exists():
            # Return mock data for frontend testing
            mock_data = [
                {
                    'id': 1,
                    'order': 1,
                    'payment_type': 'deposit',
                    'amount': 'R50000.00',
                    'payment_date': '2024-07-01',
                    'reference_number': 'REF123',
                    'notes': '',
                    'uploaded_by': None,
                    'uploaded_at': '2024-07-01T12:00:00Z',
                }
            ]
            return Response(mock_data)
        return super().list(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)

class OrderHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = OrderHistory.objects.all()
    serializer_class = OrderHistorySerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['order', 'user', 'action']
    ordering = ['-timestamp']

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['product_name', 'name', 'description', 'model_code']
    ordering_fields = ['created_at', 'product_name', 'unit_price', 'stock']
    ordering = ['-created_at']

    # Remove mock data logic - use real database data

    def perform_create(self, serializer):
        # Remove created_by field since it doesn't exist in simplified Product model
        serializer.save()
    
    def list(self, request, *args, **kwargs):
        """Override list to add error handling"""
        try:
            return super().list(request, *args, **kwargs)
        except Exception as e:
            from rest_framework.response import Response
            from rest_framework import status
            import traceback
            return Response({
                'error': str(e),
                'message': 'Error fetching products',
                'traceback': traceback.format_exc(),
                'results': []
            }, status=status.HTTP_200_OK)  # Return 200 with error info instead of 500

# Legacy Color/Fabric ViewSets (for compatibility)
class ColorViewSet(viewsets.ModelViewSet):
    queryset = Color.objects.all()
    serializer_class = ColorSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering = ['name']

class FabricViewSet(viewsets.ModelViewSet):
    queryset = Fabric.objects.all()
    serializer_class = FabricSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering = ['name']

# MVP Reference ViewSets (for physical boards)
class ColorReferenceViewSet(viewsets.ModelViewSet):
    queryset = ColorReference.objects.all()
    serializer_class = ColorReferenceSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering = ['color_code']

class FabricReferenceViewSet(viewsets.ModelViewSet):
    queryset = FabricReference.objects.all()
    serializer_class = FabricReferenceSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering = ['fabric_letter']

class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['order', 'product', 'color', 'fabric']
    ordering = ['-id']

    def list(self, request, *args, **kwargs):
        """List order items with optional order filter"""
        order_id = request.query_params.get('order')
        if order_id:
            queryset = self.queryset.filter(order_id=order_id)
        else:
            queryset = self.queryset
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

@api_view(['GET'])
@permission_classes([AllowAny])
def dashboard_stats(request):
    """
    Comprehensive dashboard statistics for OOX Furniture frontend
    """
    from django.db.models import Count, Sum, Q
    from datetime import datetime, timedelta
    from django.utils import timezone
    
    # Calculate date ranges
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Order Statistics
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(order_status='pending').count()
    confirmed_orders = Order.objects.filter(order_status='confirmed').count()
    in_production = Order.objects.filter(production_status='in_production').count()
    ready_for_delivery = Order.objects.filter(production_status='ready_for_delivery').count()
    delivered_orders = Order.objects.filter(order_status='delivered').count()
    
    # Overdue orders (past delivery deadline)
    overdue_orders = Order.objects.filter(
        delivery_deadline__lt=today,
        order_status__in=['pending', 'confirmed', 'in_production', 'ready_for_delivery']
    ).count()
    
    # Customer Statistics
    from .models import Customer
    total_customers = Customer.objects.count()
    new_customers_week = Customer.objects.filter(created_at__gte=week_ago).count()
    active_customers = Customer.objects.filter(
        orders__order_date__gte=month_ago
    ).distinct().count()
    
    # Financial Statistics
    total_revenue = Order.objects.aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    pending_payments = Order.objects.filter(
        payment_status__in=['pending', 'partial', 'overdue']
    ).aggregate(total=Sum('balance_amount'))['total'] or 0
    
    revenue_this_month = Order.objects.filter(
        order_date__gte=month_ago
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Production Statistics
    not_started = Order.objects.filter(production_status='not_started').count()
    cutting = Order.objects.filter(production_status='cutting').count()
    sewing = Order.objects.filter(production_status='sewing').count()
    finishing = Order.objects.filter(production_status='finishing').count()
    quality_check = Order.objects.filter(production_status='quality_check').count()
    completed = Order.objects.filter(production_status='completed').count()
    
    # User/Team Statistics
    from users.models import User
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    owners = User.objects.filter(role='owner').count()
    admins = User.objects.filter(role='admin').count()
    warehouse_users = User.objects.filter(role='warehouse').count()
    delivery_users = User.objects.filter(role='delivery').count()
    
    # Recent Activity
    recent_orders = Order.objects.filter(
        order_date__gte=week_ago
    ).count()
    
    return Response({
        # Core Order Stats
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'confirmed_orders': confirmed_orders,
        'in_production': in_production,
        'ready_for_delivery': ready_for_delivery,
        'delivered_orders': delivered_orders,
        'overdue_orders': overdue_orders,
        
        # Customer Stats
        'total_customers': total_customers,
        'new_customers_week': new_customers_week,
        'active_customers': active_customers,
        
        # Financial Stats
        'total_revenue': float(total_revenue),
        'pending_payments': float(pending_payments),
        'revenue_this_month': float(revenue_this_month),
        
        # Production Pipeline Stats
        'production_stats': {
            'not_started': not_started,
            'cutting': cutting,
            'sewing': sewing,
            'finishing': finishing,
            'quality_check': quality_check,
            'completed': completed,
        },
        
        # Team Stats
        'team_stats': {
            'total_users': total_users,
            'active_users': active_users,
            'owners': owners,
            'admins': admins,
            'warehouse_users': warehouse_users,
            'delivery_users': delivery_users,
        },
        
        # Recent Activity
        'recent_activity': {
            'orders_this_week': recent_orders,
        },
        
        # Quick Metrics for Dashboard Cards
        'quick_metrics': {
            'orders_today': Order.objects.filter(order_date__date=today).count(),
            'deliveries_today': Order.objects.filter(
                expected_delivery_date=today,
                order_status='ready_for_delivery'
            ).count(),
            'urgent_orders': overdue_orders,
            'production_capacity': in_production + cutting + sewing + finishing,
        }
    }) 