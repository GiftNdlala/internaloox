from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from datetime import timedelta
from users.models import User


class TaskType(models.Model):
    """Different types of tasks that can be assigned"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    estimated_duration_minutes = models.IntegerField(default=60, help_text="Estimated time in minutes")
    requires_materials = models.BooleanField(default=False, help_text="Task requires material allocation")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Task sequence (for workflow ordering)
    sequence_order = models.IntegerField(default=0, help_text="Order in production workflow")
    color_code = models.CharField(max_length=7, default="#007bff", help_text="Color for UI display")
    
    class Meta:
        ordering = ['sequence_order', 'name']
    
    def __str__(self):
        return self.name


class TaskTemplate(models.Model):
    """Pre-defined task templates for common workflows"""
    name = models.CharField(max_length=100)
    description = models.TextField()
    task_type = models.ForeignKey(TaskType, on_delete=models.CASCADE, null=True, blank=True)
    priority = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ], default='normal')
    estimated_duration = models.IntegerField(help_text="Duration in minutes", default=60)
    instructions = models.TextField(blank=True)
    materials_needed = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name


class Task(models.Model):
    """Individual task assignments to warehouse workers"""
    STATUS_CHOICES = [
        ('assigned', '📋 Assigned'),
        ('started', '🟡 Started'),
        ('paused', '⏸️ Paused'),
        ('completed', '✅ Completed'),
        ('review_needed', '🔍 Review Needed'),
        ('approved', '✅ Approved'),
        ('rejected', '❌ Rejected'),
        ('cancelled', '🚫 Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
        ('critical', 'Critical'),  # Added critical priority
    ]
    
    # Basic task info
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    task_type = models.ForeignKey(TaskType, on_delete=models.CASCADE, related_name='tasks')
    
    # Assignment
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_tasks')
    assigned_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks_assigned')
    
    # Status and priority
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='assigned')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    
    # Order relationship - REQUIRED for order-task workflow
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE, related_name='tasks', null=True, blank=True)
    order_item = models.ForeignKey('orders.OrderItem', on_delete=models.CASCADE, related_name='tasks', null=True, blank=True)
    
    # Time tracking
    estimated_duration = models.DurationField(default=timedelta(hours=1))
    actual_start_time = models.DateTimeField(null=True, blank=True)
    actual_end_time = models.DateTimeField(null=True, blank=True)
    total_time_spent = models.DurationField(default=timedelta(0))
    time_elapsed_seconds = models.IntegerField(default=0, help_text="Elapsed time in seconds for real-time tracking")
    is_timer_running = models.BooleanField(default=False)
    
    # Deadlines
    due_date = models.DateTimeField(null=True, blank=True)
    deadline = models.DateTimeField(null=True, blank=True)  # Alternative field name for frontend compatibility
    
    # Additional workflow fields
    instructions = models.TextField(blank=True)
    materials_needed = models.TextField(blank=True)
    completion_notes = models.TextField(blank=True)
    progress_percentage = models.IntegerField(default=0)
    
    # Approval workflow
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_tasks')
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-priority', 'due_date', 'created_at']
    
    def __str__(self):
        return f"{self.title} - {self.assigned_to.username} ({self.get_status_display()})"
    
    @property
    def is_overdue(self):
        """Check if task is overdue"""
        deadline = self.deadline or self.due_date
        if not deadline:
            return False
        return timezone.now() > deadline and self.status not in ['completed', 'approved', 'cancelled']
    
    @property
    def time_elapsed(self):
        """Calculate time elapsed since task started"""
        if not self.actual_start_time:
            return timedelta(0)
        
        end_time = self.actual_end_time or timezone.now()
        return end_time - self.actual_start_time
    
    @property
    def is_running(self):
        """Check if task is currently running (started but not completed)"""
        return self.status == 'started' and self.is_timer_running


class Notification(models.Model):
    """System notifications for users"""
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    TYPE_CHOICES = [
        ('info', 'Information'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('task_assigned', 'Task Assigned'),
        ('task_completed', 'Task Completed'),
        ('task_overdue', 'Task Overdue'),
        ('stock_alert', 'Stock Alert'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='info')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal')
    is_read = models.BooleanField(default=False)
    
    # Optional links to related objects
    task = models.ForeignKey(Task, on_delete=models.CASCADE, null=True, blank=True)
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.message[:50]}..."
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()


def create_notification(user, message, notification_type='info', priority='normal', task=None, order=None):
    """Helper function to create notifications"""
    return Notification.objects.create(
        user=user,
        message=message,
        type=notification_type,
        priority=priority,
        task=task,
        order=order
    )
    
    def start_task(self):
        """Start the task and begin time tracking"""
        if self.status == 'assigned':
            self.status = 'started'
            self.actual_start_time = timezone.now()
            self.save()
            
            # Create time session
            TaskTimeSession.objects.create(
                task=self,
                started_at=self.actual_start_time
            )
            return True
        return False
    
    def pause_task(self, reason=""):
        """Pause the task and stop time tracking"""
        if self.status == 'started':
            self.status = 'paused'
            current_time = timezone.now()
            
            # End current time session
            current_session = self.time_sessions.filter(ended_at__isnull=True).first()
            if current_session:
                current_session.ended_at = current_time
                current_session.save()
                
                # Update total time spent
                session_duration = current_session.ended_at - current_session.started_at
                self.total_time_spent += session_duration
            
            self.save()
            
            # Log the pause
            TaskNote.objects.create(
                task=self,
                user=self.assigned_to,
                note_type='pause',
                content=f"Task paused. Reason: {reason}" if reason else "Task paused."
            )
            return True
        return False
    
    def resume_task(self):
        """Resume a paused task"""
        if self.status == 'paused':
            self.status = 'started'
            current_time = timezone.now()
            self.save()
            
            # Create new time session
            TaskTimeSession.objects.create(
                task=self,
                started_at=current_time
            )
            return True
        return False
    
    def complete_task(self):
        """Mark task as completed"""
        if self.status in ['started', 'paused']:
            self.status = 'completed'
            self.completed_at = timezone.now()
            self.actual_end_time = self.completed_at
            
            # End current time session if running
            current_session = self.time_sessions.filter(ended_at__isnull=True).first()
            if current_session:
                current_session.ended_at = self.completed_at
                current_session.save()
                
                # Update total time spent
                session_duration = current_session.ended_at - current_session.started_at
                self.total_time_spent += session_duration
            
            self.save()
            
            # Create notification for supervisor
            TaskNotification.objects.create(
                task=self,
                recipient=self.assigned_by,
                notification_type='task_completed',
                message=f"Task '{self.title}' has been completed by {self.assigned_to.get_full_name() or self.assigned_to.username}"
            )
            return True
        return False
    
    def approve_task(self, approver):
        """Approve a completed task"""
        if self.status == 'completed':
            self.status = 'approved'
            self.save()
            
            # Create notification for worker
            TaskNotification.objects.create(
                task=self,
                recipient=self.assigned_to,
                notification_type='task_approved',
                message=f"Your task '{self.title}' has been approved by {approver.get_full_name() or approver.username}"
            )
            return True
        return False
    
    def reject_task(self, rejector, reason=""):
        """Reject a completed task and send back for revision"""
        if self.status == 'completed':
            self.status = 'rejected'
            self.save()
            
            # Log rejection reason
            TaskNote.objects.create(
                task=self,
                user=rejector,
                note_type='rejection',
                content=f"Task rejected. Reason: {reason}" if reason else "Task rejected."
            )
            
            # Create notification for worker
            TaskNotification.objects.create(
                task=self,
                recipient=self.assigned_to,
                notification_type='task_rejected',
                message=f"Your task '{self.title}' has been rejected by {rejector.get_full_name() or rejector.username}. Reason: {reason}"
            )
            return True
        return False


class TaskTimeSession(models.Model):
    """Track individual work sessions for a task"""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='time_sessions')
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.task.title} - Session {self.started_at.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def duration(self):
        """Calculate session duration"""
        if not self.ended_at:
            return timezone.now() - self.started_at
        return self.ended_at - self.started_at
    
    @property
    def is_active(self):
        """Check if session is currently active"""
        return self.ended_at is None


class TaskNote(models.Model):
    """Notes and comments on tasks"""
    NOTE_TYPES = [
        ('general', 'General Note'),
        ('issue', 'Issue/Problem'),
        ('pause', 'Task Paused'),
        ('material_request', 'Material Request'),
        ('rejection', 'Rejection Reason'),
        ('completion', 'Completion Note'),
    ]
    
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='notes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    note_type = models.CharField(max_length=20, choices=NOTE_TYPES, default='general')
    content = models.TextField()
    
    # Attachments (optional)
    attachment = models.FileField(upload_to='task_attachments/', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Note on {self.task.title} by {self.user.username}"


class TaskNotification(models.Model):
    """Notifications for task status changes"""
    NOTIFICATION_TYPES = [
        ('task_assigned', 'Task Assigned'),
        ('task_started', 'Task Started'),
        ('task_completed', 'Task Completed'),
        ('task_paused', 'Task Paused'),
        ('task_overdue', 'Task Overdue'),
        ('task_approved', 'Task Approved'),
        ('task_rejected', 'Task Rejected'),
        ('material_needed', 'Material Needed'),
    ]
    
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='notifications')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='task_notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    message = models.TextField()
    
    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_notification_type_display()} - {self.recipient.username}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()


class TaskMaterial(models.Model):
    """Materials required for a specific task"""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='required_materials')
    material = models.ForeignKey('inventory.Material', on_delete=models.CASCADE)
    quantity_needed = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_allocated = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_allocated = models.BooleanField(default=False)
    allocated_at = models.DateTimeField(null=True, blank=True)
    allocated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        unique_together = ['task', 'material']
    
    def __str__(self):
        return f"{self.task.title} needs {self.quantity_needed} {self.material.unit} of {self.material.name}"
    
    def allocate_material(self, user):
        """Allocate material for this task"""
        if not self.is_allocated and self.material.current_stock >= self.quantity_needed:
            self.quantity_allocated = self.quantity_needed
            self.is_allocated = True
            self.allocated_at = timezone.now()
            self.allocated_by = user
            self.save()
            
            # Create stock movement
            from inventory.models import StockMovement
            StockMovement.objects.create(
                material=self.material,
                movement_type='out',
                quantity=self.quantity_needed,
                reason=f"Allocated for task: {self.task.title}",
                reference_type='Task',
                reference_id=str(self.task.id),
                created_by=user
            )
            return True
        return False


class TaskTemplateStep(models.Model):
    """Individual steps in a task template"""
    template = models.ForeignKey(TaskTemplate, on_delete=models.CASCADE, related_name='steps')
    task_type = models.ForeignKey(TaskType, on_delete=models.CASCADE)
    sequence_order = models.IntegerField()
    estimated_duration = models.DurationField(default=timedelta(hours=1))
    description = models.TextField(blank=True, null=True)
    requires_previous_completion = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['sequence_order']
        unique_together = ['template', 'sequence_order']
    
    def __str__(self):
        return f"{self.template.name} - Step {self.sequence_order}: {self.task_type.name}"


class WorkerProductivity(models.Model):
    """Track worker productivity metrics"""
    worker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='productivity_records')
    date = models.DateField()
    
    # Daily metrics
    tasks_assigned = models.IntegerField(default=0)
    tasks_completed = models.IntegerField(default=0)
    tasks_approved = models.IntegerField(default=0)
    total_time_worked = models.DurationField(default=timedelta(0))
    
    # Efficiency metrics
    average_task_time = models.DurationField(null=True, blank=True)
    completion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)  # Percentage
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['worker', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.worker.username} - {self.date}"
    
    @classmethod
    def calculate_daily_productivity(cls, worker, date):
        """Calculate productivity metrics for a worker on a specific date"""
        tasks = Task.objects.filter(
            assigned_to=worker,
            created_at__date=date
        )
        
        completed_tasks = tasks.filter(status__in=['completed', 'approved'])
        approved_tasks = tasks.filter(status='approved')
        
        total_time = timedelta(0)
        for task in completed_tasks:
            total_time += task.total_time_spent
        
        # Calculate average task time
        avg_time = None
        if completed_tasks.count() > 0:
            avg_time = total_time / completed_tasks.count()
        
        # Calculate completion rate
        completion_rate = 0
        if tasks.count() > 0:
            completion_rate = (completed_tasks.count() / tasks.count()) * 100
        
        # Update or create productivity record
        productivity, created = cls.objects.update_or_create(
            worker=worker,
            date=date,
            defaults={
                'tasks_assigned': tasks.count(),
                'tasks_completed': completed_tasks.count(),
                'tasks_approved': approved_tasks.count(),
                'total_time_worked': total_time,
                'average_task_time': avg_time,
                'completion_rate': completion_rate,
            }
        )
        
        return productivity