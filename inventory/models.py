from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from users.models import User


class MaterialCategory(models.Model):
    """Categories for different types of materials"""
    CATEGORY_CHOICES = [
        ('foam', 'Foam'),
        ('wood', 'Wood/Boards'),
        ('fabric', 'Fabric'),
        ('accessories', 'Accessories'),
        ('packaging', 'Packaging'),
        ('hardware', 'Hardware'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=50, choices=CATEGORY_CHOICES, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Material Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.get_name_display()


class Supplier(models.Model):
    """Supplier information and contact details"""
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Material(models.Model):
    """Main material inventory model"""
    UNIT_CHOICES = [
        ('meters', 'Meters'),
        ('pieces', 'Pieces'),
        ('boards', 'Boards'),
        ('rolls', 'Rolls'),
        ('units', 'Units'),
        ('kg', 'Kilograms'),
        ('inches', 'Inches'),
        ('liters', 'Liters'),
    ]
    
    name = models.CharField(max_length=200)
    category = models.ForeignKey(MaterialCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='materials')
    description = models.TextField(blank=True, null=True)
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES)
    
    # Stock levels
    current_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    minimum_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ideal_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Pricing
    cost_per_unit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Supplier info
    primary_supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Material properties
    color_variants = models.TextField(blank=True, null=True, help_text="Comma-separated list of available colors")
    quality_grade = models.CharField(max_length=50, blank=True, null=True)
    
    # Custom order info
    is_custom_order = models.BooleanField(default=False, help_text="Material needs to be custom ordered")
    lead_time_days = models.IntegerField(default=7, help_text="Days to deliver if custom ordered")
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_restock_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['category', 'name']
        unique_together = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_unit_display()})"
    
    @property
    def is_low_stock(self):
        """Check if current stock is below minimum"""
        return self.current_stock <= self.minimum_stock
    
    @property
    def is_critical_stock(self):
        """Check if current stock is critically low (50% of minimum)"""
        return self.current_stock <= (self.minimum_stock * 0.5)
    
    @property
    def stock_status(self):
        """Return stock status as string"""
        if self.is_critical_stock:
            return 'critical'
        elif self.is_low_stock:
            return 'low'
        elif self.current_stock >= self.ideal_stock:
            return 'optimal'
        else:
            return 'normal'
    
    @property
    def total_value(self):
        """Calculate total value of current stock"""
        return self.current_stock * self.cost_per_unit


class StockMovement(models.Model):
    """Track all stock movements (in/out)"""
    MOVEMENT_TYPES = [
        ('in', 'Stock In'),
        ('out', 'Stock Out'),
        ('adjustment', 'Stock Adjustment'),
        ('return', 'Return'),
        ('waste', 'Waste/Damage'),
    ]
    
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name='movements')
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Reference info
    reference_type = models.CharField(max_length=50, blank=True, null=True, help_text="Order, Purchase, etc.")
    reference_id = models.CharField(max_length=50, blank=True, null=True)
    
    # Details
    reason = models.CharField(max_length=200, help_text="Reason for movement")
    notes = models.TextField(blank=True, null=True)
    
    # Tracking
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_movement_type_display()}: {self.material.name} - {self.quantity}"
    
    def save(self, *args, **kwargs):
        """Update material stock when movement is saved"""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            # Update material stock
            material = self.material
            if self.movement_type == 'in':
                material.current_stock += self.quantity
                material.last_restock_date = timezone.now()
            elif self.movement_type in ['out', 'waste']:
                material.current_stock -= self.quantity
            elif self.movement_type == 'adjustment':
                # For adjustments, quantity can be positive or negative
                material.current_stock += self.quantity
            elif self.movement_type == 'return':
                material.current_stock += self.quantity
            
            material.save()


class ProductMaterial(models.Model):
    """Define materials required for each product"""
    product = models.ForeignKey('orders.Product', on_delete=models.CASCADE, related_name='required_materials')
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    quantity_required = models.DecimalField(max_digits=10, decimal_places=2, help_text="Quantity needed per product unit")
    is_optional = models.BooleanField(default=False, help_text="Material is optional for this product")
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        unique_together = ['product', 'material']
        ordering = ['product', 'material']
    
    def __str__(self):
        return f"{self.product.product_name} requires {self.quantity_required} {self.material.unit} of {self.material.name}"
    
    @property
    def total_cost_per_product(self):
        """Calculate material cost for this product"""
        return self.quantity_required * self.material.cost_per_unit


class StockAlert(models.Model):
    """Track stock alerts and notifications"""
    ALERT_TYPES = [
        ('low_stock', 'Low Stock'),
        ('critical_stock', 'Critical Stock'),
        ('custom_order_needed', 'Custom Order Needed'),
        ('reorder_point', 'Reorder Point Reached'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('acknowledged', 'Acknowledged'),
        ('resolved', 'Resolved'),
    ]
    
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name='alerts')
    alert_type = models.CharField(max_length=30, choices=ALERT_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    message = models.TextField()
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    acknowledged_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['material', 'alert_type', 'status']
    
    def __str__(self):
        return f"{self.get_alert_type_display()}: {self.material.name}"
    
    def acknowledge(self, user):
        """Mark alert as acknowledged"""
        self.status = 'acknowledged'
        self.acknowledged_by = user
        self.acknowledged_at = timezone.now()
        self.save()
    
    def resolve(self):
        """Mark alert as resolved"""
        self.status = 'resolved'
        self.resolved_at = timezone.now()
        self.save()


class MaterialConsumptionPrediction(models.Model):
    """Predict material consumption based on current orders"""
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name='predictions')
    
    # Prediction data
    total_orders_in_queue = models.IntegerField(default=0)
    total_material_needed = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    current_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    predicted_shortage = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Timeline
    estimated_depletion_date = models.DateField(null=True, blank=True)
    days_until_shortage = models.IntegerField(null=True, blank=True)
    
    # Metadata
    calculated_at = models.DateTimeField(auto_now_add=True)
    is_current = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-calculated_at']
    
    def __str__(self):
        return f"Prediction for {self.material.name} - {self.calculated_at.strftime('%Y-%m-%d')}"
    
    @classmethod
    def calculate_for_material(cls, material):
        """Calculate consumption prediction for a material"""
        from orders.models import Order, OrderItem
        
        # Get all orders in production queue
        active_orders = Order.objects.filter(
            order_status__in=['deposit_paid', 'order_ready'],
            production_status__in=['not_started', 'cutting', 'sewing', 'finishing']
        )
        
        total_needed = 0
        order_count = 0
        
        for order in active_orders:
            for item in order.items.all():
                # Check if this product requires the material
                product_materials = item.product.required_materials.filter(material=material)
                for pm in product_materials:
                    total_needed += pm.quantity_required * item.quantity
                    order_count += 1
        
        # Calculate shortage
        shortage = max(0, total_needed - material.current_stock)
        
        # Estimate depletion date (assuming 5 working days per week)
        days_until_shortage = None
        depletion_date = None
        
        if shortage > 0 and order_count > 0:
            # Rough estimate: if we have X orders and complete 1 order per day
            days_until_shortage = max(1, int(material.current_stock / (total_needed / order_count)))
            depletion_date = timezone.now().date() + timezone.timedelta(days=days_until_shortage)
        
        # Mark previous predictions as not current
        cls.objects.filter(material=material, is_current=True).update(is_current=False)
        
        # Create new prediction
        prediction = cls.objects.create(
            material=material,
            total_orders_in_queue=order_count,
            total_material_needed=total_needed,
            current_stock=material.current_stock,
            predicted_shortage=shortage,
            estimated_depletion_date=depletion_date,
            days_until_shortage=days_until_shortage,
        )
        
        return prediction