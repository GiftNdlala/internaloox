from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Sum, F
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from datetime import timedelta

from .models import (
    MaterialCategory, Supplier, Material, StockMovement,
    ProductMaterial, StockAlert, MaterialConsumptionPrediction
)
from .serializers import (
    MaterialCategorySerializer, SupplierSerializer, MaterialSerializer, MaterialListSerializer,
    StockMovementSerializer, ProductMaterialSerializer, StockAlertSerializer,
    MaterialConsumptionPredictionSerializer, MaterialStockUpdateSerializer,
    LowStockReportSerializer, MaterialUsageReportSerializer
)


class MaterialCategoryViewSet(viewsets.ModelViewSet):
    queryset = MaterialCategory.objects.all()
    serializer_class = MaterialCategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'description']
    ordering = ['name']


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'contact_person', 'phone', 'email']
    ordering = ['name']


class MaterialViewSet(viewsets.ModelViewSet):
    queryset = Material.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'unit', 'is_custom_order', 'is_active', 'primary_supplier']
    search_fields = ['name', 'description', 'color_variants']
    ordering = ['category', 'name']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return MaterialListSerializer
        return MaterialSerializer
    
    def get_queryset(self):
        queryset = Material.objects.select_related('category', 'primary_supplier')
        
        # Filter by stock status
        stock_status = self.request.query_params.get('stock_status')
        if stock_status == 'low':
            queryset = queryset.filter(current_stock__lte=F('minimum_stock'))
        elif stock_status == 'critical':
            queryset = queryset.filter(current_stock__lte=F('minimum_stock') * 0.5)
        elif stock_status == 'optimal':
            queryset = queryset.filter(current_stock__gte=F('ideal_stock'))
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Get materials with low stock"""
        materials = self.get_queryset().filter(current_stock__lte=F('minimum_stock'))
        serializer = MaterialListSerializer(materials, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def critical_stock(self, request):
        """Get materials with critical stock"""
        materials = self.get_queryset().filter(current_stock__lte=F('minimum_stock') * 0.5)
        serializer = MaterialListSerializer(materials, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def update_stock(self, request, pk=None):
        """Update stock for a specific material"""
        material = get_object_or_404(Material, pk=pk)
        serializer = MaterialStockUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            new_stock = serializer.validated_data['new_stock']
            reason = serializer.validated_data['reason']
            unit_cost = serializer.validated_data.get('unit_cost', 0)
            
            # Calculate movement type and quantity
            current_stock = material.current_stock
            if new_stock > current_stock:
                movement_type = 'in'
                quantity = new_stock - current_stock
            elif new_stock < current_stock:
                movement_type = 'out'
                quantity = current_stock - new_stock
            else:
                return Response({'error': 'No stock change detected'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Create stock movement
            StockMovement.objects.create(
                material=material,
                movement_type=movement_type,
                quantity=quantity,
                unit_cost=unit_cost,
                reason=reason,
                created_by=request.user
            )
            
            return Response({
                'message': f'Stock updated successfully for {material.name}',
                'old_stock': current_stock,
                'new_stock': new_stock,
                'movement_type': movement_type,
                'quantity': quantity
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def bulk_stock_update(self, request):
        """Bulk update stock for multiple materials"""
        serializer = MaterialStockUpdateSerializer(data=request.data, many=True)
        
        if serializer.is_valid():
            results = []
            for item in serializer.validated_data:
                try:
                    material = Material.objects.get(id=item['material_id'])
                    new_stock = item['new_stock']
                    reason = item['reason']
                    unit_cost = item.get('unit_cost', 0)
                    
                    current_stock = material.current_stock
                    if new_stock != current_stock:
                        movement_type = 'in' if new_stock > current_stock else 'out'
                        quantity = abs(new_stock - current_stock)
                        
                        StockMovement.objects.create(
                            material=material,
                            movement_type=movement_type,
                            quantity=quantity,
                            unit_cost=unit_cost,
                            reason=reason,
                            created_by=request.user
                        )
                        
                        results.append({
                            'material_id': material.id,
                            'material_name': material.name,
                            'status': 'updated',
                            'old_stock': current_stock,
                            'new_stock': new_stock
                        })
                    else:
                        results.append({
                            'material_id': material.id,
                            'material_name': material.name,
                            'status': 'no_change'
                        })
                        
                except Material.DoesNotExist:
                    results.append({
                        'material_id': item['material_id'],
                        'status': 'error',
                        'message': 'Material not found'
                    })
            
            return Response({'results': results})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        """Get dashboard statistics for materials"""
        total_materials = Material.objects.filter(is_active=True).count()
        low_stock_count = Material.objects.filter(
            is_active=True,
            current_stock__lte=F('minimum_stock')
        ).count()
        critical_stock_count = Material.objects.filter(
            is_active=True,
            current_stock__lte=F('minimum_stock') * 0.5
        ).count()
        
        total_value = Material.objects.filter(is_active=True).aggregate(
            total=Sum(F('current_stock') * F('cost_per_unit'))
        )['total'] or 0
        
        return Response({
            'total_materials': total_materials,
            'low_stock_count': low_stock_count,
            'critical_stock_count': critical_stock_count,
            'total_inventory_value': total_value,
            'stock_status_summary': {
                'optimal': total_materials - low_stock_count,
                'low': low_stock_count - critical_stock_count,
                'critical': critical_stock_count
            }
        })


class StockMovementViewSet(viewsets.ModelViewSet):
    queryset = StockMovement.objects.all()
    serializer_class = StockMovementSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['movement_type', 'material', 'created_by']
    search_fields = ['material__name', 'reason', 'notes']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = StockMovement.objects.select_related('material', 'created_by')
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def recent_movements(self, request):
        """Get recent stock movements"""
        movements = self.get_queryset()[:20]
        serializer = self.get_serializer(movements, many=True)
        return Response(serializer.data)


class ProductMaterialViewSet(viewsets.ModelViewSet):
    queryset = ProductMaterial.objects.all()
    serializer_class = ProductMaterialSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['product', 'material', 'is_optional']
    search_fields = ['product__product_name', 'material__name']
    
    @action(detail=False, methods=['get'])
    def by_product(self, request):
        """Get materials required by a specific product"""
        product_id = request.query_params.get('product_id')
        if not product_id:
            return Response({'error': 'product_id parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        materials = self.get_queryset().filter(product_id=product_id)
        serializer = self.get_serializer(materials, many=True)
        return Response(serializer.data)


class StockAlertViewSet(viewsets.ModelViewSet):
    queryset = StockAlert.objects.all()
    serializer_class = StockAlertSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['alert_type', 'status', 'material']
    search_fields = ['material__name', 'message']
    ordering = ['-created_at']
    
    @action(detail=False, methods=['get'])
    def active_alerts(self, request):
        """Get active alerts"""
        alerts = self.get_queryset().filter(status='active')
        serializer = self.get_serializer(alerts, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """Acknowledge an alert"""
        alert = get_object_or_404(StockAlert, pk=pk)
        alert.acknowledge(request.user)
        return Response({'message': 'Alert acknowledged successfully'})
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Resolve an alert"""
        alert = get_object_or_404(StockAlert, pk=pk)
        alert.resolve()
        return Response({'message': 'Alert resolved successfully'})
    
    @action(detail=False, methods=['post'])
    def generate_low_stock_alerts(self, request):
        """Generate alerts for low stock materials"""
        materials = Material.objects.filter(
            is_active=True,
            current_stock__lte=F('minimum_stock')
        )
        
        created_count = 0
        for material in materials:
            alert_type = 'critical_stock' if material.is_critical_stock else 'low_stock'
            message = f"{material.name} stock is {'critically low' if material.is_critical_stock else 'low'}. Current: {material.current_stock} {material.unit}, Minimum: {material.minimum_stock} {material.unit}"
            
            # Check if alert already exists
            existing_alert = StockAlert.objects.filter(
                material=material,
                alert_type=alert_type,
                status='active'
            ).first()
            
            if not existing_alert:
                StockAlert.objects.create(
                    material=material,
                    alert_type=alert_type,
                    message=message
                )
                created_count += 1
        
        return Response({
            'message': f'{created_count} new stock alerts generated',
            'total_low_stock_materials': materials.count()
        })


class MaterialConsumptionPredictionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MaterialConsumptionPrediction.objects.all()
    serializer_class = MaterialConsumptionPredictionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['material', 'is_current']
    ordering = ['-calculated_at']
    
    @action(detail=False, methods=['post'])
    def calculate_predictions(self, request):
        """Calculate consumption predictions for all materials"""
        materials = Material.objects.filter(is_active=True)
        predictions_created = 0
        
        for material in materials:
            prediction = MaterialConsumptionPrediction.calculate_for_material(material)
            if prediction:
                predictions_created += 1
        
        return Response({
            'message': f'Calculated predictions for {predictions_created} materials',
            'total_materials': materials.count()
        })
    
    @action(detail=False, methods=['get'])
    def shortage_predictions(self, request):
        """Get materials predicted to have shortages"""
        predictions = self.get_queryset().filter(
            is_current=True,
            predicted_shortage__gt=0
        ).order_by('-predicted_shortage')
        
        serializer = self.get_serializer(predictions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def reports(self, request):
        """Generate various inventory reports"""
        report_type = request.query_params.get('type', 'low_stock')
        
        if report_type == 'low_stock':
            materials = Material.objects.filter(
                is_active=True,
                current_stock__lte=F('minimum_stock')
            ).select_related('category', 'primary_supplier')
            
            report_data = []
            for material in materials:
                shortage = material.minimum_stock - material.current_stock
                cost_to_restock = shortage * material.cost_per_unit
                days_since_restock = 0
                
                if material.last_restock_date:
                    days_since_restock = (timezone.now().date() - material.last_restock_date.date()).days
                
                report_data.append({
                    'material': MaterialListSerializer(material).data,
                    'shortage_amount': shortage,
                    'estimated_cost_to_restock': cost_to_restock,
                    'days_since_last_restock': days_since_restock
                })
            
            return Response(report_data)
        
        elif report_type == 'usage':
            # Material usage report based on stock movements
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=30)  # Last 30 days
            
            movements = StockMovement.objects.filter(
                movement_type='out',
                created_at__date__range=[start_date, end_date]
            ).select_related('material')
            
            usage_data = {}
            for movement in movements:
                material_id = movement.material.id
                if material_id not in usage_data:
                    usage_data[material_id] = {
                        'material': movement.material,
                        'total_used': 0,
                        'total_cost': 0,
                        'usage_count': 0
                    }
                
                usage_data[material_id]['total_used'] += movement.quantity
                usage_data[material_id]['total_cost'] += movement.quantity * movement.unit_cost
                usage_data[material_id]['usage_count'] += 1
            
            report_data = []
            for data in usage_data.values():
                avg_per_usage = data['total_used'] / data['usage_count'] if data['usage_count'] > 0 else 0
                report_data.append({
                    'material': MaterialListSerializer(data['material']).data,
                    'total_used': data['total_used'],
                    'total_cost': data['total_cost'],
                    'usage_count': data['usage_count'],
                    'average_per_order': avg_per_usage
                })
            
            return Response(report_data)
        
        return Response({'error': 'Invalid report type'}, status=status.HTTP_400_BAD_REQUEST)