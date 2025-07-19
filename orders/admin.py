from django.contrib import admin
from .models import Order, Customer, PaymentProof, OrderHistory, Product

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'email', 'created_at']
    search_fields = ['name', 'phone', 'email']
    list_filter = ['created_at']
    ordering = ['-created_at']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'customer', 'products_list', 'total_amount',
        'payment_status', 'order_status', 'expected_delivery_date', 'created_by'
    ]
    list_filter = [
        'payment_status', 'order_status', 'expected_delivery_date', 'created_at'
    ]
    search_fields = ['order_number', 'customer__name']
    readonly_fields = ['order_number', 'total_amount', 'balance_amount', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'customer')
        }),
        ('Financial Details', {
            'fields': ('total_amount', 'deposit_amount', 'balance_amount', 'payment_status')
        }),
        ('Order Status', {
            'fields': ('order_status', 'expected_delivery_date', 'actual_delivery_date')
        }),
        ('Assignment', {
            'fields': ('assigned_to_warehouse', 'assigned_to_delivery')
        }),
        ('Notes', {
            'fields': ('admin_notes', 'warehouse_notes', 'delivery_notes'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def products_list(self, obj):
        return ", ".join([item.product.name for item in obj.items.all()])
    products_list.short_description = "Products"

@admin.register(PaymentProof)
class PaymentProofAdmin(admin.ModelAdmin):
    list_display = ['order', 'payment_type', 'amount', 'uploaded_by', 'uploaded_at']
    list_filter = ['payment_type', 'uploaded_at']
    search_fields = ['order__order_number', 'payment_type']
    readonly_fields = ['uploaded_by', 'uploaded_at']
    ordering = ['-uploaded_at']

@admin.register(OrderHistory)
class OrderHistoryAdmin(admin.ModelAdmin):
    list_display = ['order', 'user', 'action', 'timestamp']
    list_filter = ['timestamp', 'user__role']
    search_fields = ['order__order_number', 'action', 'user__username']
    readonly_fields = ['order', 'user', 'action', 'details', 'timestamp']
    ordering = ['-timestamp'] 

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'base_price', 'stock', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name'] 