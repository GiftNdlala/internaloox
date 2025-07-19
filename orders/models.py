from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from users.models import User

class Customer(models.Model):
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.phone})"

class Product(models.Model):
    PRODUCT_TYPE_CHOICES = [
        ('Couch', 'Couch'),
        ('Mattress', 'Mattress'),
        ('Base', 'Base'),
        ('CoffeeTable', 'Coffee Table'),
        ('TVStand', 'TV Stand'),
        ('Set', 'Set'),
        ('Accessory', 'Accessory'),
        ('Other', 'Other'),
    ]
    name = models.CharField(max_length=200, blank=True, null=True)
    product_type = models.CharField(max_length=32, choices=PRODUCT_TYPE_CHOICES, blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    model_code = models.CharField(max_length=32, unique=True, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    production_time_days = models.PositiveIntegerField(default=0, blank=True, null=True)
    default_quantity_unit = models.CharField(max_length=32, default='unit', blank=True, null=True)
    available_for_order = models.BooleanField(default=True)
    stock = models.PositiveIntegerField(default=0, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ['name']
        unique_together = ('name', 'model_code')
    def __str__(self):
        return f"{self.name} ({self.model_code})"

class ProductOption(models.Model):
    OPTION_TYPE_CHOICES = [
        ('color', 'Color'),
        ('fabric', 'Fabric'),
    ]
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='options')
    option_type = models.CharField(max_length=20, choices=OPTION_TYPE_CHOICES)
    value = models.CharField(max_length=100)
    def __str__(self):
        return f"{self.product.name} - {self.option_type}: {self.value}"

# Update Order: remove product fields
class Order(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('deposit_only', 'Deposit Only'),
        ('fifty_percent', '50% Paid'),
        ('fully_paid', 'Fully Paid'),
    ]
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed (Deposit Paid)'),
        ('in_production', 'In Production'),
        ('ready_for_delivery', 'Ready for Delivery'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    order_number = models.CharField(max_length=20, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='orders')
    # Remove product_name, product_description, quantity, unit_price
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2)
    balance_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='deposit_only')
    order_status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    order_date = models.DateTimeField(auto_now_add=True)
    expected_delivery_date = models.DateField()
    actual_delivery_date = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_orders')
    assigned_to_warehouse = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='warehouse_orders')
    assigned_to_delivery = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='delivery_orders')
    admin_notes = models.TextField(blank=True)
    warehouse_notes = models.TextField(blank=True)
    delivery_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ['-created_at']
    def __str__(self):
        return f"Order #{self.order_number} - {self.customer.name}"
    def save(self, *args, **kwargs):
        # Auto-generate order number if not provided
        if not self.order_number:
            last_order = Order.objects.order_by('-id').first()
            if last_order:
                last_number = int(last_order.order_number[3:])  # Remove "OOX" prefix
                self.order_number = f"OOX{last_number + 1:06d}"
            else:
                self.order_number = "OOX000001"
        super().save(*args, **kwargs)

class Color(models.Model):
    name = models.CharField(max_length=50, unique=True)
    def __str__(self):
        return self.name

class Fabric(models.Model):
    name = models.CharField(max_length=50, unique=True)
    def __str__(self):
        return self.name

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True)
    fabric = models.ForeignKey(Fabric, on_delete=models.SET_NULL, null=True, blank=True)
    # Add more customization fields as needed
    def __str__(self):
        return f"{self.product.name} x{self.quantity} for {self.order.order_number}"

class PaymentProof(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payment_proofs')
    payment_type = models.CharField(max_length=50)  # e.g., "Final Payment", "Balance Payment"
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    proof_image = models.ImageField(upload_to='payment_proofs/')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"Payment Proof for Order #{self.order.order_number} - {self.payment_type}"

class OrderHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='history')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=100)
    details = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = 'Order histories'
    
    def __str__(self):
        return f"{self.action} on Order #{self.order.order_number} by {self.user}" 