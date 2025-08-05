from django.contrib import admin
from .models import (
    MaterialCategory, Supplier, Material, StockMovement, 
    ProductMaterial, StockAlert, MaterialConsumptionPrediction
)


@admin.register(MaterialCategory)
class MaterialCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_person', 'phone', 'email', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'contact_person', 'phone', 'email']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'current_stock', 'minimum_stock', 'stock_status', 'cost_per_unit', 'primary_supplier']
    list_filter = ['category', 'unit', 'is_custom_order', 'is_active', 'primary_supplier']
    search_fields = ['name', 'description', 'color_variants']
    readonly_fields = ['created_at', 'updated_at', 'last_restock_date', 'stock_status', 'total_value']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'category', 'description', 'unit')
        }),
        ('Stock Levels', {
            'fields': ('current_stock', 'minimum_stock', 'ideal_stock', 'stock_status')
        }),
        ('Pricing & Supplier', {
            'fields': ('cost_per_unit', 'total_value', 'primary_supplier')
        }),
        ('Properties', {
            'fields': ('color_variants', 'quality_grade')
        }),
        ('Custom Order Info', {
            'fields': ('is_custom_order', 'lead_time_days')
        }),
        ('Status & Timestamps', {
            'fields': ('is_active', 'created_at', 'updated_at', 'last_restock_date')
        }),
    )
    
    def stock_status(self, obj):
        status = obj.stock_status
        colors = {
            'critical': 'red',
            'low': 'orange', 
            'normal': 'blue',
            'optimal': 'green'
        }
        return f'<span style="color: {colors.get(status, "black")};">{status.title()}</span>'
    stock_status.allow_tags = True


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ['material', 'movement_type', 'quantity', 'reason', 'created_by', 'created_at']
    list_filter = ['movement_type', 'created_at', 'material__category']
    search_fields = ['material__name', 'reason', 'notes']
    readonly_fields = ['created_at']
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing existing object
            return self.readonly_fields + ['material', 'movement_type', 'quantity']
        return self.readonly_fields


@admin.register(ProductMaterial)
class ProductMaterialAdmin(admin.ModelAdmin):
    list_display = ['product', 'material', 'quantity_required', 'total_cost_per_product', 'is_optional']
    list_filter = ['is_optional', 'material__category']
    search_fields = ['product__product_name', 'material__name']
    
    def total_cost_per_product(self, obj):
        return f"R{obj.total_cost_per_product:.2f}"


@admin.register(StockAlert)
class StockAlertAdmin(admin.ModelAdmin):
    list_display = ['material', 'alert_type', 'status', 'created_at', 'acknowledged_by']
    list_filter = ['alert_type', 'status', 'created_at']
    search_fields = ['material__name', 'message']
    readonly_fields = ['created_at', 'acknowledged_at', 'resolved_at']
    
    actions = ['mark_acknowledged', 'mark_resolved']
    
    def mark_acknowledged(self, request, queryset):
        for alert in queryset:
            alert.acknowledge(request.user)
        self.message_user(request, f"{queryset.count()} alerts marked as acknowledged.")
    mark_acknowledged.short_description = "Mark selected alerts as acknowledged"
    
    def mark_resolved(self, request, queryset):
        for alert in queryset:
            alert.resolve()
        self.message_user(request, f"{queryset.count()} alerts marked as resolved.")
    mark_resolved.short_description = "Mark selected alerts as resolved"


@admin.register(MaterialConsumptionPrediction)
class MaterialConsumptionPredictionAdmin(admin.ModelAdmin):
    list_display = ['material', 'total_orders_in_queue', 'predicted_shortage', 'days_until_shortage', 'calculated_at', 'is_current']
    list_filter = ['is_current', 'calculated_at', 'material__category']
    search_fields = ['material__name']
    readonly_fields = ['calculated_at']
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing existing object
            return list(self.readonly_fields) + [
                'material', 'total_orders_in_queue', 'total_material_needed',
                'current_stock', 'predicted_shortage', 'estimated_depletion_date',
                'days_until_shortage'
            ]
        return self.readonly_fields