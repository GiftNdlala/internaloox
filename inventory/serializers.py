from rest_framework import serializers
from .models import (
    MaterialCategory, Supplier, Material, StockMovement,
    ProductMaterial, StockAlert, MaterialConsumptionPrediction
)


class MaterialCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MaterialCategory
        fields = '__all__'


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = '__all__'


class MaterialSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.get_name_display', read_only=True)
    supplier_name = serializers.CharField(source='primary_supplier.name', read_only=True)
    stock_status = serializers.CharField(read_only=True)
    total_value = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)
    is_critical_stock = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Material
        fields = '__all__'


class MaterialListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing materials"""
    category_name = serializers.CharField(source='category.get_name_display', read_only=True)
    supplier_name = serializers.CharField(source='primary_supplier.name', read_only=True)
    stock_status = serializers.CharField(read_only=True)
    
    class Meta:
        model = Material
        fields = [
            'id', 'name', 'category', 'category_name', 'unit',
            'current_stock', 'minimum_stock', 'stock_status',
            'cost_per_unit', 'primary_supplier', 'supplier_name',
            'is_active', 'last_restock_date'
        ]


class StockMovementSerializer(serializers.ModelSerializer):
    material_name = serializers.CharField(source='material.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = StockMovement
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at']
    
    def create(self, validated_data):
        # Set the created_by field to the current user
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class ProductMaterialSerializer(serializers.ModelSerializer):
    material_name = serializers.CharField(source='material.name', read_only=True)
    material_unit = serializers.CharField(source='material.unit', read_only=True)
    product_name = serializers.CharField(source='product.product_name', read_only=True)
    total_cost_per_product = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = ProductMaterial
        fields = '__all__'


class StockAlertSerializer(serializers.ModelSerializer):
    material_name = serializers.CharField(source='material.name', read_only=True)
    acknowledged_by_username = serializers.CharField(source='acknowledged_by.username', read_only=True)
    
    class Meta:
        model = StockAlert
        fields = '__all__'
        read_only_fields = ['created_at', 'acknowledged_by', 'acknowledged_at', 'resolved_at']


class MaterialConsumptionPredictionSerializer(serializers.ModelSerializer):
    material_name = serializers.CharField(source='material.name', read_only=True)
    material_unit = serializers.CharField(source='material.unit', read_only=True)
    
    class Meta:
        model = MaterialConsumptionPrediction
        fields = '__all__'
        read_only_fields = ['calculated_at']


class MaterialStockUpdateSerializer(serializers.Serializer):
    """Serializer for bulk stock updates"""
    material_id = serializers.IntegerField()
    new_stock = serializers.DecimalField(max_digits=10, decimal_places=2)
    reason = serializers.CharField(max_length=200)
    unit_cost = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=0)


class LowStockReportSerializer(serializers.Serializer):
    """Serializer for low stock report"""
    material = MaterialListSerializer()
    shortage_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    estimated_cost_to_restock = serializers.DecimalField(max_digits=10, decimal_places=2)
    days_since_last_restock = serializers.IntegerField()


class MaterialUsageReportSerializer(serializers.Serializer):
    """Serializer for material usage reports"""
    material = MaterialListSerializer()
    total_used = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_cost = serializers.DecimalField(max_digits=10, decimal_places=2)
    usage_count = serializers.IntegerField()
    average_per_order = serializers.DecimalField(max_digits=10, decimal_places=2)