from rest_framework import serializers
from .models import Order, Customer, PaymentProof, OrderHistory, Product, Color, Fabric, OrderItem, ColorReference, FabricReference
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
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'customer', 'total_amount', 
            'payment_status', 'order_status', 'expected_delivery_date', 
            'created_at'
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
    class Meta:
        model = Product
        fields = '__all__' 

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