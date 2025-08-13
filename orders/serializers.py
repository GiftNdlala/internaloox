from rest_framework import serializers
from .models import Order, Customer, PaymentProof, PaymentTransaction, OrderHistory, Product, Color, Fabric, OrderItem, ColorReference, FabricReference
from users.serializers import UserSerializer
from decimal import Decimal

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class PaymentProofSerializer(serializers.ModelSerializer):
    uploaded_by = UserSerializer(read_only=True)
    
    class Meta:
        model = PaymentProof
        fields = '__all__'
        read_only_fields = ['uploaded_by', 'uploaded_at']


class PaymentTransactionSerializer(serializers.ModelSerializer):
    actor_user = UserSerializer(read_only=True)
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    proof = PaymentProofSerializer(read_only=True)
    
    class Meta:
        model = PaymentTransaction
        fields = [
            'id', 'order', 'order_number', 'actor_user',
            'total_amount_delta', 'deposit_delta', 'balance_delta',
            'amount_delta', 'previous_balance', 'new_balance',
            'payment_method', 'payment_status', 'proof', 'notes', 'created_at'
        ]
        read_only_fields = fields

class OrderHistorySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = OrderHistory
        fields = '__all__'
        read_only_fields = ['user', 'timestamp']

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    color_name = serializers.CharField(source='color.name', read_only=True)
    fabric_name = serializers.CharField(source='fabric.name', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = '__all__'

class OrderSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer(read_only=True)
    customer_id = serializers.IntegerField(write_only=True, required=False)
    customer_update = serializers.DictField(write_only=True, required=False)  # For customer updates
    created_by = UserSerializer(read_only=True)
    assigned_to_warehouse = UserSerializer(read_only=True)
    assigned_to_delivery = UserSerializer(read_only=True)
    payment_proofs = PaymentProofSerializer(many=True, read_only=True)
    history = OrderHistorySerializer(many=True, read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    balance_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = [
            'order_number', 'created_by', 'created_at', 'updated_at'
        ]
    
    def create(self, validated_data):
        print("ORDER CREATE - validated_data:", validated_data)
        print("ORDER CREATE - initial_data:", self.initial_data)
        
        # Ensure total_amount, deposit_amount, balance_amount are Decimal
        for field in ['total_amount', 'deposit_amount', 'balance_amount']:
            if field in validated_data and validated_data[field] is not None:
                validated_data[field] = Decimal(str(validated_data[field]))
        
        # Get items data from context or initial_data
        items_data = self.context.get('items_data', [])
        if not items_data and 'items' in self.initial_data:
            items_data = self.initial_data['items']
        
        print("ORDER CREATE - items_data:", items_data)
        
        validated_data.pop('items_data', None)
        validated_data['created_by'] = self.context['request'].user
        order = super().create(validated_data)
        
        # Create order items
        for item_data in items_data:
            print("ORDER CREATE - Creating item:", item_data)
            OrderItem.objects.create(
                order=order,
                product_id=item_data['product'],
                quantity=item_data['quantity'],
                unit_price=item_data['unit_price'],
                color_id=item_data.get('color'),
                fabric_id=item_data.get('fabric'),
                product_description=item_data.get('product_description', '')
            )
        
        print("ORDER CREATE - Order created successfully with", len(items_data), "items")
        return order

    def update(self, instance, validated_data):
        print("ORDER UPDATE - initial_data:", self.initial_data)
        print("ORDER UPDATE - validated_data:", validated_data)
        print("ORDER UPDATE - initial_data keys:", list(self.initial_data.keys()))
        print("ORDER UPDATE - request.data:", self.context.get('request').data)
        
        # Update customer info if present - check multiple sources
        customer_data = None
        
        # Try customer_update field first
        if 'customer_update' in self.initial_data:
            customer_data = self.initial_data['customer_update']
            print("ORDER UPDATE - Found customer_update in initial_data")
        elif 'customer_update' in self.context.get('request').data:
            customer_data = self.context.get('request').data['customer_update']
            print("ORDER UPDATE - Found customer_update in request.data")
        elif 'customer' in self.initial_data:
            customer_data = self.initial_data['customer']
            print("ORDER UPDATE - Found customer in initial_data")
        elif 'customer' in self.context.get('request').data:
            customer_data = self.context.get('request').data['customer']
            print("ORDER UPDATE - Found customer in request.data")
        
        # If still no customer data, try to get it from validated_data
        if not customer_data and 'customer_update' in validated_data:
            customer_data = validated_data.pop('customer_update')
            print("ORDER UPDATE - Found customer_update in validated_data")
        elif not customer_data and 'customer_data' in validated_data:
            customer_data = validated_data.pop('customer_data')
            print("ORDER UPDATE - Found customer_data in validated_data")
        elif not customer_data and 'customer_data' in self.initial_data:
            customer_data = self.initial_data['customer_data']
            print("ORDER UPDATE - Found customer_data in initial_data")
        
        print("ORDER UPDATE - customer_data:", customer_data)
        
        if customer_data:
            customer = instance.customer
            print("ORDER UPDATE - Updating customer fields:", list(customer_data.keys()))
            for field, value in customer_data.items():
                if hasattr(customer, field) and field != 'id':  # Don't update the ID
                    setattr(customer, field, value)
                    print(f"ORDER UPDATE - Set {field} = {value}")
            customer.save()
            print("ORDER UPDATE - Customer updated successfully")
        else:
            print("ORDER UPDATE - No customer data found in any source")

        # Update order fields
        for attr, value in validated_data.items():
            if attr not in ['items', 'items_data', 'customer_id']:
                setattr(instance, attr, value)
        instance.save()

        # Update order items
        items_data = self.context.get('items_data', self.initial_data.get('items', []))
        existing_items = {item.id: item for item in instance.items.all()}
        sent_item_ids = set()
        for item_data in items_data:
            item_id = item_data.get('id')
            if item_id and item_id in existing_items:
                # Update existing item
                item = existing_items[item_id]
                item.product_id = item_data['product']
                item.quantity = item_data['quantity']
                item.unit_price = item_data['unit_price']
                item.color_id = item_data.get('color')
                item.fabric_id = item_data.get('fabric')
                item.save()
                sent_item_ids.add(item_id)
            else:
                # Create new item
                OrderItem.objects.create(
                    order=instance,
                    product_id=item_data['product'],
                    quantity=item_data['quantity'],
                    unit_price=item_data['unit_price'],
                    color_id=item_data.get('color'),
                    fabric_id=item_data.get('fabric')
                )
        # Delete items not in the update payload
        for item_id, item in existing_items.items():
            if item_id not in sent_item_ids:
                item.delete()
        return instance

class OrderListSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer(read_only=True)
    customer_name = serializers.CharField(read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'customer', 'customer_name',
            'order_date', 'expected_delivery_date', 'delivery_deadline',
            'order_status', 'production_status', 'payment_status',
            'deposit_amount', 'balance_amount', 'total_amount',
            'admin_notes', 'warehouse_notes', 'delivery_notes',
            'created_at', 'updated_at',
            # New queue management fields
            'deposit_paid_date', 'queue_position', 'is_priority_order',
            'production_start_date', 'estimated_completion_date'
        ]

class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['order_status', 'warehouse_notes', 'delivery_notes']
    
    def update(self, instance, validated_data):
        # Create history entry
        OrderHistory.objects.create(
            order=instance,
            user=self.context['request'].user,
            action=f"Status updated to {validated_data.get('order_status', instance.order_status)}",
            details=f"Updated by {self.context['request'].user.username}"
        )
        return super().update(instance, validated_data) 

class ProductSerializer(serializers.ModelSerializer):
    # Write-only fields from frontend contract
    price = serializers.DecimalField(max_digits=10, decimal_places=2, write_only=True, required=False)
    currency = serializers.CharField(write_only=True, required=False, default='ZAR')
    color = serializers.CharField(write_only=True, required=False, allow_blank=True)
    fabric = serializers.CharField(write_only=True, required=False, allow_blank=True)
    colors = serializers.ListField(child=serializers.CharField(allow_blank=False), write_only=True, required=False, allow_empty=True)
    fabrics = serializers.ListField(child=serializers.CharField(allow_blank=False), write_only=True, required=False, allow_empty=True)
    sku = serializers.CharField(write_only=True, required=False, allow_blank=True)
    attributes = serializers.JSONField(required=False)

    # Make model-required fields optional at serializer layer
    product_type = serializers.CharField(required=False)
    product_name = serializers.CharField(required=False)
    default_fabric_letter = serializers.CharField(required=False)
    default_color_code = serializers.CharField(required=False)
    unit_cost = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    estimated_build_time = serializers.IntegerField(required=False)

    # Read-only aliased fields in responses
    created_at = serializers.DateTimeField(read_only=True)
    colors = serializers.ListField(child=serializers.CharField(), read_only=True)
    fabrics = serializers.ListField(child=serializers.CharField(), read_only=True)

    class Meta:
        model = Product
        fields = '__all__'

    def validate(self, attrs):
        # Map name to product_name
        name = attrs.get('name') or attrs.get('product_name') or self.initial_data.get('name')
        if name:
            attrs['product_name'] = name
            attrs['name'] = name
        # Unit price from price
        if 'price' in self.initial_data and self.initial_data.get('price') not in [None, ""]:
            attrs['unit_price'] = Decimal(str(self.initial_data.get('price')))
        elif 'unit_price' in attrs and attrs['unit_price'] is not None:
            attrs['unit_price'] = Decimal(str(attrs['unit_price']))
        # Defaults for required fields
        attrs.setdefault('product_type', 'single')
        attrs.setdefault('unit_cost', Decimal('0'))
        attrs.setdefault('estimated_build_time', 1)
        fabric_name = self.initial_data.get('fabric') or attrs.get('fabric') or ''
        attrs.setdefault('default_fabric_letter', (fabric_name[:1].upper() if fabric_name else 'A'))
        attrs.setdefault('default_color_code', '01')
        # Model code from sku
        sku_value = self.initial_data.get('sku') or attrs.get('sku')
        if sku_value:
            attrs['model_code'] = sku_value
        # Attributes passthrough
        if 'attributes' in self.initial_data and isinstance(self.initial_data.get('attributes'), dict):
            attrs['attributes'] = self.initial_data.get('attributes')
        return attrs

    def create(self, validated_data):
        # Extract write-only contract fields
        price = Decimal(str(validated_data.pop('price', validated_data.get('unit_price', 0) or 0)))
        currency = validated_data.pop('currency', 'ZAR')
        color_name = validated_data.pop('color', '').strip() if 'color' in validated_data else (self.initial_data.get('color', '').strip() if hasattr(self, 'initial_data') else '')
        fabric_name = validated_data.pop('fabric', '').strip() if 'fabric' in validated_data else (self.initial_data.get('fabric', '').strip() if hasattr(self, 'initial_data') else '')
        color_list = validated_data.pop('colors', self.initial_data.get('colors', []) if hasattr(self, 'initial_data') else []) or []
        fabric_list = validated_data.pop('fabrics', self.initial_data.get('fabrics', []) if hasattr(self, 'initial_data') else []) or []
        sku = validated_data.pop('sku', '').strip() if 'sku' in validated_data else (self.initial_data.get('sku', '').strip() if hasattr(self, 'initial_data') else '')
        attributes = validated_data.pop('attributes', validated_data.get('attributes', None))

        # Ensure final mappings already handled in validate; just enforce unit_price
        validated_data['unit_price'] = price
        if sku and not validated_data.get('model_code'):
            validated_data['model_code'] = sku
        if attributes is not None:
            validated_data['attributes'] = attributes

        # Create product
        product = super().create(validated_data)

        # Persist color/fabric as options (legacy simple storage)
        from .models import ProductOption
        # Build unique sets from singletons + arrays
        color_values = {v.strip() for v in ([color_name] if color_name else []) + list(color_list) if isinstance(v, str) and v.strip()}
        fabric_values = {v.strip() for v in ([fabric_name] if fabric_name else []) + list(fabric_list) if isinstance(v, str) and v.strip()}
        for cv in color_values:
            Color.objects.get_or_create(name=cv)
            ProductOption.objects.get_or_create(product=product, option_type='color', value=cv)
        for fv in fabric_values:
            Fabric.objects.get_or_create(name=fv)
            ProductOption.objects.get_or_create(product=product, option_type='fabric', value=fv)

        # Attach currency and echo fields for response
        self._response_currency = currency
        self._response_colors = list(color_values)
        self._response_fabrics = list(fabric_values)
        self._response_sku = sku
        self._response_price = price
        self._response_attributes = attributes
        return product

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Map fields back to frontend contract
        data.setdefault('name', instance.product_name or instance.name)
        data['price'] = str(self._response_price) if hasattr(self, '_response_price') else str(instance.unit_price or instance.base_price or 0)
        data['currency'] = getattr(self, '_response_currency', 'ZAR')
        # sku alias
        data['sku'] = getattr(self, '_response_sku', instance.model_code or '')
        # attributes
        data['attributes'] = instance.attributes or getattr(self, '_response_attributes', {}) or {}
        # Try fetch options for colors/fabrics
        colors_list = getattr(self, '_response_colors', None)
        fabrics_list = getattr(self, '_response_fabrics', None)
        try:
            if colors_list is None:
                colors_list = list(instance.options.filter(option_type='color').values_list('value', flat=True))
            if fabrics_list is None:
                fabrics_list = list(instance.options.filter(option_type='fabric').values_list('value', flat=True))
        except Exception:
            pass
        data['colors'] = colors_list or []
        data['fabrics'] = fabrics_list or []
        return data

class ColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Color
        fields = '__all__'

class FabricSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fabric
        fields = '__all__'

# MVP Reference Serializers
class ColorReferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ColorReference
        fields = '__all__'

class FabricReferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = FabricReference
        fields = '__all__' 