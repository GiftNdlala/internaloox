from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('warehouse_manager', 'Warehouse Manager'),  # NEW ROLE
        ('warehouse_worker', 'Warehouse Worker'),    # NEW ROLE
        ('warehouse', 'Warehouse Staff'),            # LEGACY - Keep for backward compatibility
        ('delivery', 'Delivery'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='warehouse_worker')
    phone = models.CharField(max_length=15, blank=True, null=True)
    
    # Additional fields for warehouse workers
    employee_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    shift_start = models.TimeField(null=True, blank=True)
    shift_end = models.TimeField(null=True, blank=True)
    is_active_worker = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    @property
    def is_admin(self):
        return self.role == 'admin'
    
    @property
    def is_warehouse(self):
        return self.role in ['warehouse', 'warehouse_worker', 'warehouse_manager']
    
    @property
    def is_warehouse_manager(self):
        return self.role == 'warehouse_manager'
    
    @property
    def is_warehouse_worker(self):
        return self.role in ['warehouse_worker']  # 'warehouse' now acts as manager
    
    @property
    def is_delivery(self):
        return self.role == 'delivery' 
    
    @property
    def is_owner(self):
        return self.role == 'owner'
    
    @property
    def can_manage_tasks(self):
        """Check if user can create and assign tasks"""
        return self.role in ['owner', 'admin', 'warehouse_manager']
    
    @property
    def can_manage_workers(self):
        """Check if user can manage warehouse workers"""
        return self.role in ['owner', 'admin', 'warehouse_manager'] 