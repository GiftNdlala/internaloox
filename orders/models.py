from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from datetime import date, timedelta
from users.models import User

def get_default_delivery_date():
    return timezone.now().date()

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
    # Match EXACT Supabase orders_product table structure
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    stock = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    available_for_order = models.BooleanField(default=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    category = models.CharField(max_length=200, blank=True, null=True)
    default_quantity_unit = models.CharField(max_length=50, blank=True, null=True)
    model_code = models.CharField(max_length=100, blank=True, null=True, unique=True)
    product_type = models.CharField(max_length=100)
    production_time_days = models.IntegerField(blank=True, null=True)
    product_name = models.CharField(max_length=200)
    default_fabric_letter = models.CharField(max_length=1)
    default_color_code = models.CharField(max_length=10)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    estimated_build_time = models.IntegerField()
    is_active = models.BooleanField(default=True)
    date_added = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'orders_product'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.product_name or self.name or 'Unnamed Product'}"
    
    @property
    def display_name(self):
        """Return the best available name"""
        return self.product_name or self.name or 'Unnamed Product'
    
    @property
    def display_price(self):
        """Return unit_price or base_price"""
        if self.unit_price:
            return f"R{self.unit_price:.2f}"
        elif self.base_price:
            return f"R{self.base_price:.2f}"
        return "R0.00"
        
    @property
    def stock_quantity(self):
        """Return stock field"""
        return self.stock or 0

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
        ('deposit_pending', 'Deposit Pending'),
        ('deposit_paid', 'Deposit Paid'),
        ('fully_paid', 'Fully Paid'),
        ('overdue', 'Overdue'),
        # Legacy statuses for backward compatibility
        ('pending', 'Pending'),
        ('partial', 'Partial'),
        ('paid', 'Paid'),
        ('deposit_only', 'Deposit Only'),
        ('fifty_percent', '50% Paid'),
    ]
    
    # MVP Production Status Choices (Enhanced for Frontend)
    PRODUCTION_STATUS_CHOICES = [
        ('not_started', '🟡 Not Started'),
        ('cutting', '🔧 Cutting'),
        ('sewing', '🧵 Sewing'),
        ('finishing', '🎨 Finishing'),
        ('quality_check', '🔍 Quality Check'),
        ('completed', '✅ Completed'),
        ('in_production', '🟠 In Production'),  # Generic fallback
        ('ready_for_delivery', '🟢 Ready for Delivery'),
    ]
    
    ORDER_STATUS_CHOICES = [
        ('deposit_pending', 'Deposit Pending'),
        ('deposit_paid', 'Deposit Paid - In Queue'),
        ('order_ready', 'Order Ready'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        # Legacy statuses for backward compatibility
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('in_production', 'In Production'),
        ('ready_for_delivery', 'Ready for Delivery'),
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
    delivery_deadline = models.DateField(help_text="Target delivery date", default=get_default_delivery_date)
    order_date = models.DateTimeField(auto_now_add=True)
    expected_delivery_date = models.DateField(null=True, blank=True, help_text="Set only when order is ready")
    actual_delivery_date = models.DateField(null=True, blank=True)
    
    # New fields for queue management
    deposit_paid_date = models.DateTimeField(null=True, blank=True, help_text="When deposit was paid - starts queue timer")
    queue_position = models.IntegerField(null=True, blank=True, help_text="Position in production queue")
    is_priority_order = models.BooleanField(default=False, help_text="Owner-escalated priority order")
    production_start_date = models.DateField(null=True, blank=True, help_text="When production actually started")
    estimated_completion_date = models.DateField(null=True, blank=True, help_text="Auto-calculated based on queue")
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
        
        # Handle status change logic
        self._handle_status_changes()
        
        super().save(*args, **kwargs)
    
    def _handle_status_changes(self):
        """Handle automatic actions when status changes"""
        if self.order_status == 'deposit_paid' and not self.deposit_paid_date:
            # Automatically set deposit paid date and add to queue
            self.deposit_paid_date = timezone.now()
            self._add_to_queue()
        
        if self.order_status == 'order_ready' and not self.expected_delivery_date:
            # If order is ready but no delivery date set, calculate default
            if self.deposit_paid_date:
                # Give 3 days for delivery from ready status
                self.expected_delivery_date = (timezone.now() + timedelta(days=3)).date()
    
    def _add_to_queue(self):
        """Add order to production queue"""
        if not self.queue_position:
            # Get the highest queue position and add 1
            highest_position = Order.objects.filter(
                order_status='deposit_paid',
                queue_position__isnull=False
            ).aggregate(max_position=models.Max('queue_position'))['max_position']
            
            self.queue_position = (highest_position or 0) + 1
            
            # Calculate estimated completion date (20 business days from deposit paid)
            if self.deposit_paid_date:
                business_days = 20
                current_date = self.deposit_paid_date.date()
                while business_days > 0:
                    current_date += timedelta(days=1)
                    if current_date.weekday() < 5:  # Monday to Friday
                        business_days -= 1
                self.estimated_completion_date = current_date
    
    def can_set_delivery_date(self):
        """Check if delivery date can be set"""
        return self.order_status == 'order_ready'
    
    def is_in_queue(self):
        """Check if order is in production queue"""
        return self.order_status == 'deposit_paid' and self.queue_position is not None
    
    def days_in_queue(self):
        """Calculate days spent in queue"""
        if self.deposit_paid_date:
            return (timezone.now().date() - self.deposit_paid_date.date()).days
        return 0
    
    def is_queue_expired(self):
        """Check if order has exceeded 20-day queue limit"""
        return self.days_in_queue() > 20
    
    def can_escalate_priority(self, user):
        """Check if user can escalate this order to priority"""
        return user.role == 'owner' and self.order_status in ['deposit_paid', 'order_ready']
    
    def escalate_to_priority(self, user):
        """Escalate order to priority (owner only)"""
        if self.can_escalate_priority(user):
            self.is_priority_order = True
            self.queue_position = 1  # Move to front of queue
            # Move other orders down
            Order.objects.filter(
                order_status='deposit_paid',
                queue_position__gte=1
            ).exclude(id=self.id).update(queue_position=models.F('queue_position') + 1)
            return True
        return False

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
    assigned_fabric_letter = models.CharField(max_length=1, help_text="Fabric code from reference board", blank=True, default="")
    assigned_color_code = models.CharField(max_length=2, help_text="Color code from reference board", blank=True, default="")
    
    # Legacy fields for compatibility
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True)
    fabric = models.ForeignKey(Fabric, on_delete=models.SET_NULL, null=True, blank=True)
    product_description = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"
    
    def __str__(self):
        fabric = self.assigned_fabric_letter or "N/A"
        color = self.assigned_color_code or "N/A"
        return f"{self.product.product_name} x{self.quantity} (Fabric: {fabric}, Color: {color})"
    
    @property
    def total_price(self):
        return self.quantity * self.unit_price
    
    @property  
    def fabric_name(self):
        """Get fabric name from reference"""
        if not self.assigned_fabric_letter:
            return "No fabric assigned"
        try:
            fabric_ref = FabricReference.objects.get(fabric_letter=self.assigned_fabric_letter)
            return fabric_ref.fabric_name
        except FabricReference.DoesNotExist:
            return f"Fabric {self.assigned_fabric_letter}"
    
    @property
    def color_name(self):
        """Get color name from reference"""
        if not self.assigned_color_code:
            return "No color assigned"
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