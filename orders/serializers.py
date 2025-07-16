from rest_framework import serializers
from .models import Order, Customer, PaymentProof, OrderHistory
from users.serializers import UserSerializer

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

class OrderSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer(read_only=True)
    customer_id = serializers.IntegerField(write_only=True)
    created_by = UserSerializer(read_only=True)
    assigned_to_warehouse = UserSerializer(read_only=True)
    assigned_to_delivery = UserSerializer(read_only=True)
    payment_proofs = PaymentProofSerializer(many=True, read_only=True)
    history = OrderHistorySerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = [
            'order_number', 'total_amount', 'balance_amount', 
            'created_by', 'created_at', 'updated_at'
        ]
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

class OrderListSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer(read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'customer', 'product_name', 
            'total_amount', 'payment_status', 'order_status',
            'expected_delivery_date', 'created_at'
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