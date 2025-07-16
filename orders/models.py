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
    
    # Order details
    order_number = models.CharField(max_length=20, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='orders')
    
    # Product details
    product_name = models.CharField(max_length=200)
    product_description = models.TextField(blank=True)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Financial details
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2)
    balance_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='deposit_only')
    
    # Order status
    order_status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    
    # Dates
    order_date = models.DateTimeField(auto_now_add=True)
    expected_delivery_date = models.DateField()
    actual_delivery_date = models.DateField(null=True, blank=True)
    
    # User tracking
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_orders')
    assigned_to_warehouse = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='warehouse_orders')
    assigned_to_delivery = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='delivery_orders')
    
    # Notes
    admin_notes = models.TextField(blank=True)
    warehouse_notes = models.TextField(blank=True)
    delivery_notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order #{self.order_number} - {self.customer.name}"
    
    def save(self, *args, **kwargs):
        # Auto-calculate total and balance
        self.total_amount = self.unit_price * self.quantity
        self.balance_amount = self.total_amount - self.deposit_amount
        
        # Auto-generate order number if not provided
        if not self.order_number:
            last_order = Order.objects.order_by('-id').first()
            if last_order:
                last_number = int(last_order.order_number[3:])  # Remove "OOX" prefix
                self.order_number = f"OOX{last_number + 1:06d}"
            else:
                self.order_number = "OOX000001"
        
        super().save(*args, **kwargs)
    
    @property
    def is_deposit_paid(self):
        return self.payment_status in ['deposit_only', 'fifty_percent', 'fully_paid']
    
    @property
    def can_mark_ready(self):
        return self.order_status in ['confirmed', 'in_production'] and self.is_deposit_paid
    
    @property
    def can_deliver(self):
        return self.order_status == 'ready_for_delivery'
    
    @property
    def is_overdue(self):
        return self.expected_delivery_date < timezone.now().date() and self.order_status not in ['delivered', 'cancelled']

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