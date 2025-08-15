from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Sum, F
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from datetime import timedelta

from .models import (
    MaterialCategory, Supplier, Material, StockMovement,
    ProductMaterial, StockAlert, MaterialConsumptionPrediction
)
from orders.models import Product
from .serializers import (
    MaterialCategorySerializer, SupplierSerializer, MaterialSerializer, MaterialListSerializer,
    StockMovementSerializer, ProductMaterialSerializer, StockAlertSerializer,
    MaterialConsumptionPredictionSerializer, MaterialStockUpdateSerializer,
    LowStockReportSerializer, MaterialUsageReportSerializer, ProductSerializer
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

    @action(detail=False, methods=['get'])
    def warehouse_dashboard(self, request):
        """Complete warehouse dashboard data for frontend"""
        try:
            # Stock overview
            total_materials = Material.objects.filter(is_active=True).count()
            low_stock_materials = Material.objects.filter(
                is_active=True,
                current_stock__lte=F('minimum_stock')
            )
            critical_stock_materials = Material.objects.filter(
                is_active=True,
                current_stock__lte=F('minimum_stock') * 0.5
            )
            
            # Calculate total inventory value
            total_value = Material.objects.filter(is_active=True).aggregate(
                total=Sum(F('current_stock') * F('cost_per_unit'))
            )['total'] or 0
            
            # Recent stock movements (handle empty queryset)
            try:
                recent_movements = StockMovement.objects.select_related('material', 'created_by').order_by('-created_at')[:10]
                recent_movements_data = StockMovementSerializer(recent_movements, many=True).data
            except Exception as e:
                print(f"Error serializing stock movements: {e}")
                recent_movements_data = []
            
            # Active alerts (handle empty queryset)
            try:
                active_alerts = StockAlert.objects.filter(status='active').select_related('material')[:5]
                active_alerts_data = StockAlertSerializer(active_alerts, many=True).data
            except Exception as e:
                print(f"Error serializing stock alerts: {e}")
                active_alerts_data = []
            
            # Materials by category
            materials_by_category = {}
            for category in MaterialCategory.objects.filter(is_active=True):
                try:
                    materials_by_category[category.get_name_display()] = {
                        'total': Material.objects.filter(category=category, is_active=True).count(),
                        'low_stock': Material.objects.filter(
                            category=category, 
                            is_active=True,
                            current_stock__lte=F('minimum_stock')
                        ).count(),
                        'total_value': Material.objects.filter(
                            category=category, 
                            is_active=True
                        ).aggregate(
                            total=Sum(F('current_stock') * F('cost_per_unit'))
                        )['total'] or 0
                    }
                except Exception as e:
                    print(f"Error processing category {category.name}: {e}")
                    materials_by_category[category.get_name_display()] = {
                        'total': 0,
                        'low_stock': 0,
                        'total_value': 0
                    }
            
            # Top suppliers by material count
            supplier_stats = []
            for supplier in Supplier.objects.filter(is_active=True):
                try:
                    material_count = Material.objects.filter(primary_supplier=supplier, is_active=True).count()
                    if material_count > 0:
                        supplier_stats.append({
                            'id': supplier.id,
                            'name': supplier.name,
                            'material_count': material_count,
                            'contact_person': supplier.contact_person,
                            'phone': supplier.phone
                        })
                except Exception as e:
                    print(f"Error processing supplier {supplier.name}: {e}")
                    continue
            
            # Serialize materials with error handling
            try:
                low_stock_data = MaterialListSerializer(low_stock_materials[:10], many=True).data
            except Exception as e:
                print(f"Error serializing low stock materials: {e}")
                low_stock_data = []
            
            try:
                critical_stock_data = MaterialListSerializer(critical_stock_materials, many=True).data
            except Exception as e:
                print(f"Error serializing critical stock materials: {e}")
                critical_stock_data = []
            
            return Response({
                'overview': {
                    'total_materials': total_materials,
                    'low_stock_count': low_stock_materials.count(),
                    'critical_stock_count': critical_stock_materials.count(),
                    'total_inventory_value': float(total_value),
                    'active_alerts_count': len(active_alerts_data)
                },
                'stock_status': {
                    'optimal': total_materials - low_stock_materials.count(),
                    'low': low_stock_materials.count() - critical_stock_materials.count(),
                    'critical': critical_stock_materials.count()
                },
                'low_stock_materials': low_stock_data,
                'critical_stock_materials': critical_stock_data,
                'recent_movements': recent_movements_data,
                'active_alerts': active_alerts_data,
                'materials_by_category': materials_by_category,
                'top_suppliers': sorted(supplier_stats, key=lambda x: x['material_count'], reverse=True)[:5]
            })
        except Exception as e:
            print(f"Error in warehouse_dashboard: {e}")
            import traceback
            traceback.print_exc()
            return Response({
                'error': 'Failed to load warehouse dashboard data',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def stock_locations(self, request):
        """Get stock locations for materials (for frontend location tracking)"""
        # This can be extended later with actual location tracking
        # For now, return materials with their basic info
        materials = Material.objects.filter(is_active=True).select_related('category', 'primary_supplier')
        
        locations_data = []
        for material in materials:
            locations_data.append({
                'material_id': material.id,
                'material_name': material.name,
                'category': material.category.get_name_display(),
                'current_stock': float(material.current_stock),
                'unit': material.get_unit_display(),
                'location': f"Section {material.category.name.upper()}-{material.id:03d}",  # Generated location
                'last_updated': material.updated_at,
                'supplier': material.primary_supplier.name if material.primary_supplier else None
            })
        
        return Response(locations_data)
    
    @action(detail=False, methods=['post'])
    def quick_stock_entry(self, request):
        """Quick stock entry endpoint for warehouse workers"""
        entries = request.data.get('entries', [])
        
        if not entries:
            return Response({'error': 'No entries provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        created_movements = []
        errors = []
        
        for i, entry_data in enumerate(entries):
            try:
                # Validate required fields
                required_fields = ['material_id', 'movement_type', 'quantity']
                for field in required_fields:
                    if field not in entry_data:
                        errors.append(f"Entry {i+1}: Missing required field '{field}'")
                        continue
                
                if errors:
                    continue
                    
                material = Material.objects.get(id=entry_data['material_id'])
                
                # Create stock movement
                movement_data = {
                    'material': material,
                    'movement_type': entry_data['movement_type'],  # 'in' or 'out'
                    'quantity': float(entry_data['quantity']),
                    'reason': entry_data.get('reason', ''),
                    'location': entry_data.get('location', ''),
                    'batch_number': entry_data.get('batch_number', ''),
                    'created_by': request.user
                }
                
                # Set expiry date if provided
                if entry_data.get('expiry_date'):
                    from django.utils.dateparse import parse_date
                    expiry_date = parse_date(entry_data['expiry_date'])
                    if expiry_date:
                        movement_data['expiry_date'] = expiry_date
                
                movement = StockMovement.objects.create(**movement_data)
                
                # Update material stock
                if entry_data['movement_type'] == 'in':
                    material.current_stock += movement_data['quantity']
                else:  # 'out'
                    material.current_stock -= movement_data['quantity']
                    if material.current_stock < 0:
                        material.current_stock = 0  # Prevent negative stock
                
                material.save()
                
                created_movements.append({
                    'movement_id': movement.id,
                    'material_name': material.name,
                    'movement_type': movement.movement_type,
                    'quantity': movement.quantity,
                    'new_stock_level': material.current_stock,
                    'status': 'success'
                })
                
            except Material.DoesNotExist:
                errors.append(f"Entry {i+1}: Material with ID {entry_data.get('material_id')} not found")
            except ValueError as e:
                errors.append(f"Entry {i+1}: Invalid quantity value")
            except Exception as e:
                errors.append(f"Entry {i+1}: {str(e)}")
        
        response_data = {
            'message': f'{len(created_movements)} stock movements created',
            'movements': created_movements,
            'success_count': len(created_movements),
            'error_count': len(errors)
        }
        
        if errors:
            response_data['errors'] = errors
        
        return Response(response_data)


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


class ProductViewSet(viewsets.ModelViewSet):
    """Product management for warehouse managers"""
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'product_type', 'is_active', 'available_for_order']
    search_fields = ['product_name', 'name', 'model_code', 'description']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter products based on user role"""
        user = self.request.user
        
        # Warehouse managers can see all products
        if user.role in ['owner', 'admin', 'warehouse']:
            return Product.objects.all()
        
        # Workers see only active products
        return Product.objects.filter(is_active=True, available_for_order=True)
    
    @action(detail=True, methods=['post'])
    def add_color(self, request, pk=None):
        """Add a new color variant to a product"""
        product = get_object_or_404(Product, pk=pk)
        
        color_name = request.data.get('color_name')
        color_code = request.data.get('color_code')
        image_url = request.data.get('image_url')
        
        if not color_name:
            return Response({'error': 'Color name is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            product.add_color(color_name, color_code, image_url)
            return Response({
                'message': f'Color "{color_name}" added successfully',
                'available_colors': product.get_active_colors()
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def add_fabric(self, request, pk=None):
        """Add a new fabric variant to a product"""
        product = get_object_or_404(Product, pk=pk)
        
        fabric_name = request.data.get('fabric_name')
        fabric_code = request.data.get('fabric_code')
        sample_url = request.data.get('sample_url')
        
        if not fabric_name:
            return Response({'error': 'Fabric name is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            product.add_fabric(fabric_name, fabric_code, sample_url)
            return Response({
                'message': f'Fabric "{fabric_name}" added successfully',
                'available_fabrics': product.get_active_fabrics()
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def toggle_color(self, request, pk=None):
        """Enable/disable a color variant"""
        product = get_object_or_404(Product, pk=pk)
        color_name = request.data.get('color_name')
        
        if not color_name:
            return Response({'error': 'Color name is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        for color in product.available_colors:
            if color.get('name') == color_name:
                color['is_active'] = not color.get('is_active', True)
                product.save()
                status_text = 'enabled' if color['is_active'] else 'disabled'
                return Response({
                    'message': f'Color "{color_name}" {status_text}',
                    'available_colors': product.get_active_colors()
                })
        
        return Response({'error': 'Color not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def toggle_fabric(self, request, pk=None):
        """Enable/disable a fabric variant"""
        product = get_object_or_404(Product, pk=pk)
        fabric_name = request.data.get('fabric_name')
        
        if not fabric_name:
            return Response({'error': 'Fabric name is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        for fabric in product.available_fabrics:
            if fabric.get('name') == fabric_name:
                fabric['is_active'] = not fabric.get('is_active', True)
                product.save()
                status_text = 'enabled' if fabric['is_active'] else 'disabled'
                return Response({
                    'message': f'Fabric "{fabric_name}" {status_text}',
                    'available_fabrics': product.get_active_fabrics()
                })
        
        return Response({'error': 'Fabric not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'])
    def colors_and_fabrics(self, request):
        """Get all available colors and fabrics across products"""
        colors = set()
        fabrics = set()
        
        for product in Product.objects.filter(is_active=True):
            colors.update(product.get_active_colors())
            fabrics.update(product.get_active_fabrics())
        
        return Response({
            'available_colors': sorted(list(colors)),
            'available_fabrics': sorted(list(fabrics))
        })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_product_with_options(request):
    """Create a new product with colors and fabrics"""
    user = request.user
    
    # Check permissions
    if user.role not in ['owner', 'admin', 'warehouse']:
        return Response({'error': 'Insufficient permissions'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        # Extract product data
        product_data = {
            'product_name': request.data.get('product_name'),
            'description': request.data.get('description', ''),
            'category': request.data.get('category', ''),
            'product_type': request.data.get('product_type', 'furniture'),
            'unit_cost': request.data.get('unit_cost', 0),
            'unit_price': request.data.get('unit_price', 0),
            'estimated_build_time': request.data.get('estimated_build_time', 1),
            'production_time_days': request.data.get('production_time_days', 1),
            'default_quantity_unit': request.data.get('default_quantity_unit', 'pieces'),
            'stock': request.data.get('stock', 0),
            'available_for_order': request.data.get('available_for_order', True),
            'is_active': True
        }
        
        # Validate required fields
        if not product_data['product_name']:
            return Response({'error': 'Product name is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not product_data['unit_cost'] or not product_data['unit_price']:
            return Response({'error': 'Unit cost and price are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create product
        product = Product.objects.create(**product_data)
        
        # Add colors if provided
        colors = request.data.get('colors', [])
        for color in colors:
            if isinstance(color, str):
                product.add_color(color)
            elif isinstance(color, dict):
                product.add_color(
                    color.get('name'),
                    color.get('code'),
                    color.get('image_url')
                )
        
        # Add fabrics if provided
        fabrics = request.data.get('fabrics', [])
        for fabric in fabrics:
            if isinstance(fabric, str):
                product.add_fabric(fabric)
            elif isinstance(fabric, dict):
                product.add_fabric(
                    fabric.get('name'),
                    fabric.get('code'),
                    fabric.get('sample_url')
                )
        
        return Response({
            'message': 'Product created successfully',
            'product_id': product.id,
            'product_name': product.product_name,
            'available_colors': product.get_active_colors(),
            'available_fabrics': product.get_active_fabrics()
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)