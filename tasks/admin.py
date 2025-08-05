from django.contrib import admin
from django.utils.html import format_html
from .models import (
    TaskType, Task, TaskTimeSession, TaskNote, TaskNotification,
    TaskMaterial, TaskTemplate, TaskTemplateStep, WorkerProductivity
)


@admin.register(TaskType)
class TaskTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'sequence_order', 'estimated_duration_minutes', 'requires_materials', 'is_active']
    list_filter = ['requires_materials', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['sequence_order', 'name']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'assigned_to', 'assigned_by', 'status', 'priority', 'order', 'created_at', 'is_overdue']
    list_filter = ['status', 'priority', 'task_type', 'assigned_to', 'assigned_by', 'created_at']
    search_fields = ['title', 'description', 'assigned_to__username', 'order__order_number']
    readonly_fields = ['created_at', 'updated_at', 'completed_at', 'actual_start_time', 'actual_end_time', 'total_time_spent', 'time_elapsed']
    
    fieldsets = (
        ('Task Information', {
            'fields': ('title', 'description', 'task_type', 'priority')
        }),
        ('Assignment', {
            'fields': ('assigned_to', 'assigned_by', 'order', 'order_item')
        }),
        ('Status & Timing', {
            'fields': ('status', 'estimated_duration', 'due_date')
        }),
        ('Time Tracking', {
            'fields': ('actual_start_time', 'actual_end_time', 'total_time_spent', 'time_elapsed'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_started', 'mark_as_completed', 'mark_as_approved']
    
    def is_overdue(self, obj):
        if obj.is_overdue:
            return format_html('<span style="color: red;">⚠️ Overdue</span>')
        return '✅ On Time'
    is_overdue.short_description = 'Status'
    
    def mark_as_started(self, request, queryset):
        count = 0
        for task in queryset:
            if task.start_task():
                count += 1
        self.message_user(request, f"{count} tasks marked as started.")
    mark_as_started.short_description = "Mark selected tasks as started"
    
    def mark_as_completed(self, request, queryset):
        count = 0
        for task in queryset:
            if task.complete_task():
                count += 1
        self.message_user(request, f"{count} tasks marked as completed.")
    mark_as_completed.short_description = "Mark selected tasks as completed"
    
    def mark_as_approved(self, request, queryset):
        count = 0
        for task in queryset:
            if task.approve_task(request.user):
                count += 1
        self.message_user(request, f"{count} tasks approved.")
    mark_as_approved.short_description = "Approve selected tasks"


@admin.register(TaskTimeSession)
class TaskTimeSessionAdmin(admin.ModelAdmin):
    list_display = ['task', 'started_at', 'ended_at', 'duration', 'is_active']
    list_filter = ['started_at', 'ended_at', 'task__assigned_to']
    search_fields = ['task__title', 'task__assigned_to__username']
    readonly_fields = ['duration', 'is_active']
    
    def duration(self, obj):
        duration = obj.duration
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{hours}h {minutes}m"
    
    def is_active(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">🟢 Active</span>')
        return '⚫ Ended'


@admin.register(TaskNote)
class TaskNoteAdmin(admin.ModelAdmin):
    list_display = ['task', 'user', 'note_type', 'content_preview', 'created_at']
    list_filter = ['note_type', 'created_at', 'user']
    search_fields = ['task__title', 'content', 'user__username']
    readonly_fields = ['created_at']
    
    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'


@admin.register(TaskNotification)
class TaskNotificationAdmin(admin.ModelAdmin):
    list_display = ['task', 'recipient', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at', 'recipient']
    search_fields = ['task__title', 'recipient__username', 'message']
    readonly_fields = ['created_at', 'read_at']
    
    actions = ['mark_as_read']
    
    def mark_as_read(self, request, queryset):
        count = 0
        for notification in queryset:
            if not notification.is_read:
                notification.mark_as_read()
                count += 1
        self.message_user(request, f"{count} notifications marked as read.")
    mark_as_read.short_description = "Mark selected notifications as read"


@admin.register(TaskMaterial)
class TaskMaterialAdmin(admin.ModelAdmin):
    list_display = ['task', 'material', 'quantity_needed', 'quantity_allocated', 'is_allocated', 'allocated_by']
    list_filter = ['is_allocated', 'allocated_at', 'material__category']
    search_fields = ['task__title', 'material__name']
    readonly_fields = ['allocated_at']
    
    actions = ['allocate_materials']
    
    def allocate_materials(self, request, queryset):
        count = 0
        for task_material in queryset:
            if task_material.allocate_material(request.user):
                count += 1
        self.message_user(request, f"{count} materials allocated.")
    allocate_materials.short_description = "Allocate selected materials"


@admin.register(TaskTemplate)
class TaskTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'product_type', 'is_active', 'created_at']
    list_filter = ['is_active', 'product_type', 'created_at']
    search_fields = ['name', 'description']


@admin.register(TaskTemplateStep)
class TaskTemplateStepAdmin(admin.ModelAdmin):
    list_display = ['template', 'sequence_order', 'task_type', 'estimated_duration', 'requires_previous_completion']
    list_filter = ['template', 'task_type', 'requires_previous_completion']
    search_fields = ['template__name', 'task_type__name', 'description']
    ordering = ['template', 'sequence_order']


@admin.register(WorkerProductivity)
class WorkerProductivityAdmin(admin.ModelAdmin):
    list_display = ['worker', 'date', 'tasks_assigned', 'tasks_completed', 'completion_rate', 'total_time_worked']
    list_filter = ['date', 'worker']
    search_fields = ['worker__username']
    readonly_fields = ['created_at', 'updated_at']
    
    def completion_rate(self, obj):
        return f"{obj.completion_rate:.1f}%"
    
    def total_time_worked(self, obj):
        total_seconds = int(obj.total_time_worked.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{hours}h {minutes}m"