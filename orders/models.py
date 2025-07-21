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
        ('set', 'Set'),
        ('single', 'Single Item'),
    ]
    
    PRODUCT_CATEGORY_CHOICES = [
        ('couch', 'Couch'),
        ('mattress', 'Mattress'),
        ('base', 'Base'),
        ('coffee_table', 'Coffee Table'),
        ('tv_stand', 'TV Stand'),
        ('accessory', 'Accessory'),
        ('other', 'Other'),
    ]
    
    # Core fields (compatible with existing database)
    name = models.CharField(max_length=200, default='Unnamed Product')  # Fallback for existing data
    description = models.TextField(blank=True, null=True)
    price = models.CharField(max_length=50, default='R0.00')  # String format for compatibility
    stock_quantity = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # MVP Optional Fields (for new functionality)
    product_name = models.CharField(max_length=200, blank=True, null=True)
    product_type = models.CharField(max_length=32, choices=PRODUCT_TYPE_CHOICES, blank=True, null=True)
    product_category = models.CharField(max_length=100, choices=PRODUCT_CATEGORY_CHOICES, blank=True, null=True)
    default_fabric_letter = models.CharField(max_length=1, blank=True, null=True, help_text="Default fabric code (A-Z)")
    default_color_code = models.CharField(max_length=2, blank=True, null=True, help_text="Default color code (1-99)")
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text="Cost to produce")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text="Selling price")
    estimated_build_time = models.PositiveIntegerField(blank=True, null=True, help_text="Days to build")
    is_active = models.BooleanField(default=True)
    date_added = models.DateTimeField(blank=True, null=True)
    
    # Additional fields for existing compatibility
    model_code = models.CharField(max_length=32, unique=True, blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        # Use product_name if available, otherwise fall back to name
        display_name = self.product_name or self.name
        return f"{display_name}"
    
    @property
    def display_name(self):
        """Return the best available name for this product"""
        return self.product_name or self.name
    
    @property
    def display_price(self):
        """Return the best available price for this product"""
        if self.unit_price:
            return f"R{self.unit_price:.2f}"
        return self.price or "R0.00"
    
    @property
    def profit_margin(self):
        """Calculate profit margin if cost and price are available"""
        if self.unit_cost and self.unit_price:
            if self.unit_cost > 0:
                margin = ((self.unit_price - self.unit_cost) / self.unit_cost) * 100
                return round(margin, 2)
        return 0.0

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

class Order(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('deposit_only', 'Deposit Only'),
        ('fifty_percent', '50% Paid'),
        ('fully_paid', 'Fully Paid'),
    ]
    
    # MVP Production Status Choices
    PRODUCTION_STATUS_CHOICES = [
        ('not_started', '🟡 Not Started'),
        ('in_production', '🟠 In Production'),
        ('ready_for_delivery', '🟢 Ready for Delivery'),
    ]
    
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('in_production', 'In Production'),
        ('ready_for_delivery', 'Ready for Delivery'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    order_number = models.CharField(max_length=20, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='orders', blank=True, null=True)
    customer_name = models.CharField(max_length=200, blank=True, null=True, help_text="Optional internal tracking")
    
    # MVP Financial Fields
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    balance_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='deposit_only')
    order_status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    
    # MVP Production Tracking
    production_status = models.CharField(max_length=20, choices=PRODUCTION_STATUS_CHOICES, default='not_started')
    delivery_deadline = models.DateField(help_text="Target delivery date")
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

# MVP Reference Tables for Physical Boards
class ColorReference(models.Model):
    """Master color reference with codes for physical board"""
    color_code = models.CharField(max_length=2, unique=True, help_text="Number code (1-99)")
    color_name = models.CharField(max_length=50)
    hex_color = models.CharField(max_length=7, blank=True, null=True, help_text="For digital reference #FFFFFF")
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['color_code']
    
    def __str__(self):
        return f"{self.color_code} - {self.color_name}"

class FabricReference(models.Model):
    """Master fabric reference with letter codes for physical board"""
    fabric_letter = models.CharField(max_length=1, unique=True, help_text="Letter code (A-Z)")
    fabric_name = models.CharField(max_length=50)
    fabric_type = models.CharField(max_length=50, blank=True, null=True, help_text="e.g., Suede, Leather, Cotton")
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['fabric_letter']
    
    def __str__(self):
        return f"{self.fabric_letter} - {self.fabric_name}"

# Legacy models for compatibility
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
    
    # MVP Fabric and Color using codes
    assigned_fabric_letter = models.CharField(max_length=1, help_text="Fabric code from reference board")
    assigned_color_code = models.CharField(max_length=2, help_text="Color code from reference board")
    
    # Legacy fields for compatibility
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True)
    fabric = models.ForeignKey(Fabric, on_delete=models.SET_NULL, null=True, blank=True)
    product_description = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"
    
    def __str__(self):
        return f"{self.product.product_name} x{self.quantity} (Fabric: {self.assigned_fabric_letter}, Color: {self.assigned_color_code})"
    
    @property
    def total_price(self):
        return self.quantity * self.unit_price
    
    @property  
    def fabric_name(self):
        """Get fabric name from reference"""
        try:
            fabric_ref = FabricReference.objects.get(fabric_letter=self.assigned_fabric_letter)
            return fabric_ref.fabric_name
        except FabricReference.DoesNotExist:
            return f"Fabric {self.assigned_fabric_letter}"
    
    @property
    def color_name(self):
        """Get color name from reference"""
        try:
            color_ref = ColorReference.objects.get(color_code=self.assigned_color_code)
            return color_ref.color_name
        except ColorReference.DoesNotExist:
            return f"Color {self.assigned_color_code}"

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