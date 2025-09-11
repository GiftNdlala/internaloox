from rest_framework import serializers
from django.utils import timezone
from .models import (
    TaskType, Task, TaskTimeSession, TaskNote, TaskNotification,
    TaskMaterial, TaskTemplate, TaskTemplateStep, WorkerProductivity
)


class TaskTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskType
        fields = '__all__'


class TaskTimeSessionSerializer(serializers.ModelSerializer):
    duration_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = TaskTimeSession
        fields = '__all__'
        read_only_fields = ['duration']
    
    def get_duration_formatted(self, obj):
        duration = obj.duration
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{hours}h {minutes}m"


class TaskNoteSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = TaskNote
        fields = '__all__'
        read_only_fields = ['user', 'created_at']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class TaskMaterialSerializer(serializers.ModelSerializer):
    material_name = serializers.CharField(source='material.name', read_only=True)
    material_unit = serializers.CharField(source='material.unit', read_only=True)
    allocated_by_username = serializers.CharField(source='allocated_by.username', read_only=True)
    
    class Meta:
        model = TaskMaterial
        fields = '__all__'
        read_only_fields = ['allocated_at', 'allocated_by']


class TaskSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    assigned_to_username = serializers.CharField(source='assigned_to.username', read_only=True)
    assigned_by_name = serializers.CharField(source='assigned_by.get_full_name', read_only=True)
    assigned_by_username = serializers.CharField(source='assigned_by.username', read_only=True)
    task_type_name = serializers.CharField(source='task_type.name', read_only=True)
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    order_item_details = serializers.SerializerMethodField()
    
    # Time tracking fields
    is_overdue = serializers.BooleanField(read_only=True)
    is_running = serializers.BooleanField(read_only=True)
    time_elapsed_formatted = serializers.SerializerMethodField()
    total_time_formatted = serializers.SerializerMethodField()
    
    # Related data
    notes = TaskNoteSerializer(many=True, read_only=True)
    time_sessions = TaskTimeSessionSerializer(many=True, read_only=True)
    required_materials = TaskMaterialSerializer(many=True, read_only=True)
    
    class Meta:
        model = Task
        fields = '__all__'
        read_only_fields = [
            'actual_start_time', 'actual_end_time', 'total_time_spent',
            'completed_at', 'created_at', 'updated_at'
        ]
    
    def get_time_elapsed_formatted(self, obj):
        duration = obj.time_elapsed
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{hours}h {minutes}m"
    
    def get_total_time_formatted(self, obj):
        duration = obj.total_time_spent
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{hours}h {minutes}m"

    def get_order_item_details(self, obj):
        item = getattr(obj, 'order_item', None)
        if not item:
            return None
        # Build product image URL if available
        product_image_url = None
        try:
            if item.product_id and getattr(item.product, 'main_image', None):
                from django.urls import reverse
                request = self.context.get('request') if hasattr(self, 'context') else None
                url_path = reverse('orders:product-main-image', kwargs={'pk': item.product_id})
                product_image_url = request.build_absolute_uri(url_path) if request else url_path
        except Exception:
            product_image_url = None
        return {
            'id': item.id,
            'product_name': getattr(item.product, 'product_name', None) or getattr(item.product, 'name', None),
            'quantity': item.quantity,
            'unit_price': str(item.unit_price),
            'color_name': getattr(item, 'color_name', None),
            'fabric_name': getattr(item, 'fabric_name', None),
            'product_image_url': product_image_url,
        }


class TaskListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing tasks"""
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    assigned_by_name = serializers.CharField(source='assigned_by.get_full_name', read_only=True)
    task_type_name = serializers.CharField(source='task_type.name', read_only=True)
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    order_item_details = serializers.SerializerMethodField()
    is_overdue = serializers.BooleanField(read_only=True)
    is_running = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'status', 'priority', 'assigned_to', 'assigned_to_name',
            'assigned_by', 'assigned_by_name', 'task_type', 'task_type_name',
            'order', 'order_number', 'order_item', 'order_item_details', 'due_date', 'is_overdue', 'is_running',
            'created_at', 'updated_at'
        ]

    def get_order_item_details(self, obj):
        item = getattr(obj, 'order_item', None)
        if not item:
            return None
        # Build product image URL if available
        product_image_url = None
        try:
            if item.product_id and getattr(item.product, 'main_image', None):
                from django.urls import reverse
                request = self.context.get('request') if hasattr(self, 'context') else None
                url_path = reverse('orders:product-main-image', kwargs={'pk': item.product_id})
                product_image_url = request.build_absolute_uri(url_path) if request else url_path
        except Exception:
            product_image_url = None
        return {
            'id': item.id,
            'product_name': getattr(item.product, 'product_name', None) or getattr(item.product, 'name', None),
            'quantity': item.quantity,
            'unit_price': str(item.unit_price),
            'color_name': getattr(item, 'color_name', None),
            'fabric_name': getattr(item, 'fabric_name', None),
            'product_image_url': product_image_url,
        }


class TaskNotificationSerializer(serializers.ModelSerializer):
    task_title = serializers.CharField(source='task.title', read_only=True)
    
    class Meta:
        model = TaskNotification
        fields = '__all__'
        read_only_fields = ['created_at', 'read_at']


class TaskTemplateStepSerializer(serializers.ModelSerializer):
    task_type_name = serializers.CharField(source='task_type.name', read_only=True)
    
    class Meta:
        model = TaskTemplateStep
        fields = '__all__'


class TaskTemplateSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product_type.product_name', read_only=True)
    steps = TaskTemplateStepSerializer(many=True, read_only=True)
    
    class Meta:
        model = TaskTemplate
        fields = '__all__'


class WorkerProductivitySerializer(serializers.ModelSerializer):
    worker_name = serializers.CharField(source='worker.get_full_name', read_only=True)
    worker_username = serializers.CharField(source='worker.username', read_only=True)
    
    class Meta:
        model = WorkerProductivity
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class TaskActionSerializer(serializers.Serializer):
    """Serializer for task actions (start, pause, complete, etc.)"""
    action = serializers.ChoiceField(choices=[
        ('start', 'Start Task'),
        ('pause', 'Pause Task'),
        ('resume', 'Resume Task'),
        ('complete', 'Complete Task'),
        ('approve', 'Approve Task'),
        ('reject', 'Reject Task'),
    ])
    reason = serializers.CharField(required=False, allow_blank=True)


class TaskAssignmentSerializer(serializers.Serializer):
    """Serializer for bulk task assignment"""
    assigned_to = serializers.IntegerField()
    task_type = serializers.IntegerField()
    title = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, allow_blank=True)
    priority = serializers.ChoiceField(choices=Task.PRIORITY_CHOICES, default='normal')
    due_date = serializers.DateTimeField(required=False)
    order = serializers.IntegerField(required=False)
    order_item = serializers.IntegerField(required=False)


class WorkerTaskSummarySerializer(serializers.Serializer):
    """Serializer for worker task summary"""
    worker = serializers.CharField()
    total_assigned = serializers.IntegerField()
    total_completed = serializers.IntegerField()
    total_approved = serializers.IntegerField()
    total_in_progress = serializers.IntegerField()
    total_overdue = serializers.IntegerField()
    completion_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    average_task_time = serializers.CharField()


class TaskDashboardSerializer(serializers.Serializer):
    """Serializer for task dashboard data"""
    total_tasks = serializers.IntegerField()
    tasks_assigned = serializers.IntegerField()
    tasks_in_progress = serializers.IntegerField()
    tasks_completed = serializers.IntegerField()
    tasks_overdue = serializers.IntegerField()
    recent_tasks = TaskListSerializer(many=True)
    worker_summaries = WorkerTaskSummarySerializer(many=True)