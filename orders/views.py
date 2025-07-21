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