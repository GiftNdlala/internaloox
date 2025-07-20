from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Order, Customer, PaymentProof, OrderHistory, Product, OrderItem,
    ColorReference, FabricReference, Color, Fabric
)

# MVP Reference Tables Admin
@admin.register(ColorReference)
class ColorReferenceAdmin(admin.ModelAdmin):
    list_display = ['color_code', 'color_name', 'hex_color_display', 'is_active']
    list_filter = ['is_active']
    search_fields = ['color_code', 'color_name']
    ordering = ['color_code']
    
    def hex_color_display(self, obj):
        if obj.hex_color:
            return format_html(
                '<span style="background-color: {}; padding: 2px 10px; border-radius: 3px; color: white;">{}</span>',
                obj.hex_color, obj.hex_color
            )
        return "-"
    hex_color_display.short_description = "Color Preview"

@admin.register(FabricReference) 
class FabricReferenceAdmin(admin.ModelAdmin):
    list_display = ['fabric_letter', 'fabric_name', 'fabric_type', 'is_active']
    list_filter = ['fabric_type', 'is_active']
    search_fields = ['fabric_letter', 'fabric_name']
    ordering = ['fabric_letter']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'product_name', 'product_type', 'product_category', 
        'default_fabric_letter', 'default_color_code',
        'unit_cost', 'unit_price', 'profit_margin_display', 
        'estimated_build_time', 'is_active'
    ]
    list_filter = ['product_type', 'product_category', 'is_active']
    search_fields = ['product_name', 'model_code']
    ordering = ['product_name']
    
    fieldsets = (
        ('Product Information', {
            'fields': ('product_name', 'product_type', 'product_category', 'description')
        }),
        ('Default Settings', {
            'fields': ('default_fabric_letter', 'default_color_code')
        }),
        ('Pricing & Production', {
            'fields': ('unit_cost', 'unit_price', 'estimated_build_time')
        }),
        ('Status', {
            'fields': ('is_active', 'model_code')
        })
    )
    
    def profit_margin_display(self, obj):
        margin = obj.profit_margin
        color = 'green' if margin > 50 else 'orange' if margin > 20 else 'red'
        return format_html(
            '<span style="color: {};">{:.1f}%</span>',
            color, margin
        )
    profit_margin_display.short_description = "Profit Margin"

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    fields = ['product', 'quantity', 'unit_price', 'assigned_fabric_letter', 'assigned_color_code', 'total_price']
    readonly_fields = ['total_price']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'customer_display', 'total_amount',
        'production_status_display', 'delivery_deadline', 
        'order_status', 'created_by'
    ]
    list_filter = [
        'production_status', 'order_status', 'delivery_deadline', 'order_date'
    ]
    search_fields = ['order_number', 'customer__name', 'customer_name']
    readonly_fields = ['order_number', 'order_date', 'updated_at']
    ordering = ['-order_date']
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'customer', 'customer_name', 'delivery_deadline')
        }),
        ('Production Tracking', {
            'fields': ('production_status', 'order_status'),
            'classes': ['wide']
        }),
        ('Financial Details', {
            'fields': ('total_amount', 'deposit_amount', 'balance_amount', 'payment_status')
        }),
        ('Assignment & Notes', {
            'fields': ('created_by', 'assigned_to_warehouse', 'admin_notes', 'warehouse_notes'),
            'classes': ['collapse']
        }),
        ('Timeline', {
            'fields': ('order_date', 'expected_delivery_date', 'actual_delivery_date', 'updated_at'),
            'classes': ['collapse']
        })
    )
    
    def customer_display(self, obj):
        return obj.customer.name if obj.customer else obj.customer_name or "No Customer"
    customer_display.short_description = "Customer"
    
    def production_status_display(self, obj):
        status_colors = {
            'not_started': '#FFA500',  # Orange
            'in_production': '#FF6B6B',  # Red  
            'ready_for_delivery': '#4ECDC4'  # Green
        }
        color = status_colors.get(obj.production_status, '#666')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
            color, obj.get_production_status_display()
        )
    production_status_display.short_description = "Production Status"

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'email', 'created_at']
    search_fields = ['name', 'phone', 'email']
    list_filter = ['created_at']
    ordering = ['-created_at']

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