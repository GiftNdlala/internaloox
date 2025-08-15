from rest_framework import serializers
from .models import (
    MaterialCategory, Supplier, Material, StockMovement,
    ProductMaterial, StockAlert, MaterialConsumptionPrediction
)
from orders.models import Product


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
    # Aliases expected by frontend
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, write_only=True)
    category_id = serializers.IntegerField(required=False, write_only=True)

    class Meta:
        model = Material
        fields = '__all__'

    def _normalize_unit(self, value: str) -> str:
        if not value:
            return value
        normalized = value.strip().lower()
        mapping = {
            'metres': 'meters',
            'meters': 'meters',
            'kilograms': 'kg',
            'kgs': 'kg',
            'kg': 'kg',
            'litres': 'liters',
            'liters': 'liters',
            'units': 'units',
            'boards': 'boards',
            'rolls': 'rolls',
            'pieces': 'pieces',
            'inches': 'inches',
        }
        return mapping.get(normalized, normalized)

    def validate(self, attrs):
        initial = getattr(self, 'initial_data', {})
        # Map unit alias
        unit_in = initial.get('unit') or attrs.get('unit')
        if unit_in:
            attrs['unit'] = self._normalize_unit(unit_in)
        # Map unit_price -> cost_per_unit
        if 'unit_price' in initial and initial.get('unit_price') not in [None, '']:
            attrs['cost_per_unit'] = initial.get('unit_price')
        # Map category_id -> category (MaterialCategory instance)
        if 'category_id' in initial and initial.get('category_id'):
            try:
                category_obj = MaterialCategory.objects.get(pk=initial.get('category_id'))
                attrs['category'] = category_obj
            except MaterialCategory.DoesNotExist:
                pass
        # Default category to 'other' if none provided
        if not attrs.get('category') and not initial.get('category') and not initial.get('category_id'):
            try:
                default_cat, _ = MaterialCategory.objects.get_or_create(name='other', defaults={'is_active': True})
                attrs['category'] = default_cat
            except Exception as e:
                # If category creation fails, allow material without category
                print(f"Category creation failed: {e}")
                pass
        return super().validate(attrs)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Echo unit_price for frontend using cost_per_unit
        data['unit_price'] = str(instance.cost_per_unit)
        # Ensure numeric stock and minimum values are numbers (string fallback safe)
        if 'current_stock' in data and isinstance(data['current_stock'], str):
            try:
                data['current_stock'] = float(data['current_stock'])
            except Exception:
                pass
        if 'minimum_stock' in data and isinstance(data['minimum_stock'], str):
            try:
                data['minimum_stock'] = float(data['minimum_stock'])
            except Exception:
                pass
        return data


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
    # Frontend alias fields
    direction = serializers.CharField(write_only=True, required=False)
    note = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = StockMovement
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at']

    def validate(self, attrs):
        initial = getattr(self, 'initial_data', {})
        # Map direction -> movement_type
        direction = initial.get('direction')
        if direction:
            direction = direction.lower().strip()
            if direction not in ['in', 'out']:
                raise serializers.ValidationError({'direction': 'Must be "in" or "out"'})
            attrs['movement_type'] = direction
        # unit_cost required only for 'in'
        movement_type = attrs.get('movement_type') or direction
        if movement_type == 'in':
            if initial.get('unit_cost') in [None, '', '0'] and not attrs.get('unit_cost'):
                raise serializers.ValidationError({'unit_cost': 'unit_cost is required for stock-in'})
        # Map note -> notes
        if 'note' in initial and initial.get('note') is not None:
            attrs['notes'] = initial.get('note')
        return super().validate(attrs)

    def create(self, validated_data):
        # Set the created_by field to the current user
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Expose direction instead of movement_type
        data['direction'] = data.get('movement_type')
        # Prefer note alias (from notes or reason)
        note_val = data.get('notes') or data.get('reason')
        if note_val is not None:
            data['note'] = note_val
        # For stock-out, present unit_cost as null if zero
        if data.get('direction') == 'out':
            try:
                if float(data.get('unit_cost') or 0) == 0:
                    data['unit_cost'] = None
            except Exception:
                pass
        return data


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


class ProductSerializer(serializers.ModelSerializer):
    """Product serializer for warehouse management"""
    category_name = serializers.CharField(source='category', read_only=True)
    available_colors = serializers.JSONField(read_only=True)
    available_fabrics = serializers.JSONField(read_only=True)
    stock_status = serializers.CharField(read_only=True)
    total_value = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    # Frontend compatibility fields
    unit_price = serializers.DecimalField(source='unit_price', max_digits=10, decimal_places=2, read_only=True)
    product_name = serializers.CharField(source='product_name', read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'product_name', 'model_code', 'description', 'category',
            'category_name', 'product_type', 'unit_price', 'unit_cost',
            'available_colors', 'available_fabrics', 'stock_status', 'total_value',
            'is_active', 'available_for_order', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'available_colors', 'available_fabrics']
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Ensure colors and fabrics are always arrays
        if not data.get('available_colors'):
            data['available_colors'] = []
        if not data.get('available_fabrics'):
            data['available_fabrics'] = []
        return data


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