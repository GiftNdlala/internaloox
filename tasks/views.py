from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count, Sum, Avg
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from datetime import timedelta, date

from users.models import User
from .models import (
    TaskType, Task, TaskTimeSession, TaskNote, TaskNotification,
    TaskMaterial, TaskTemplate, TaskTemplateStep, WorkerProductivity
)
from .serializers import (
    TaskTypeSerializer, TaskSerializer, TaskListSerializer, TaskTimeSessionSerializer,
    TaskNoteSerializer, TaskNotificationSerializer, TaskMaterialSerializer,
    TaskTemplateSerializer, TaskTemplateStepSerializer, WorkerProductivitySerializer,
    TaskActionSerializer, TaskAssignmentSerializer, WorkerTaskSummarySerializer,
    TaskDashboardSerializer
)


class TaskTypeViewSet(viewsets.ModelViewSet):
    queryset = TaskType.objects.all()
    serializer_class = TaskTypeSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['requires_materials', 'is_active']
    search_fields = ['name', 'description']
    ordering = ['sequence_order', 'name']


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'priority', 'assigned_to', 'assigned_by', 'task_type', 'order']
    search_fields = ['title', 'description', 'assigned_to__username', 'order__order_number']
    ordering = ['-priority', 'due_date', 'created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return TaskListSerializer
        return TaskSerializer
    
    def get_queryset(self):
        queryset = Task.objects.select_related(
            'assigned_to', 'assigned_by', 'task_type', 'order'
        ).prefetch_related('notes', 'time_sessions', 'required_materials')
        
        # Filter by user role and permissions
        user = self.request.user
        
        # If user is warehouse worker, only show their tasks
        if user.role == 'warehouse':
            queryset = queryset.filter(assigned_to=user)
        
        # Filter by overdue status
        if self.request.query_params.get('overdue') == 'true':
            queryset = queryset.filter(
                due_date__lt=timezone.now(),
                status__in=['assigned', 'started', 'paused']
            )
        
        # Filter by running status
        if self.request.query_params.get('running') == 'true':
            queryset = queryset.filter(status='started')
        
        return queryset
    
    def perform_create(self, serializer):
        """Set assigned_by to current user when creating task"""
        serializer.save(assigned_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_tasks(self, request):
        """Get tasks assigned to current user"""
        tasks = self.get_queryset().filter(assigned_to=request.user)
        serializer = TaskListSerializer(tasks, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def assigned_by_me(self, request):
        """Get tasks assigned by current user"""
        tasks = self.get_queryset().filter(assigned_by=request.user)
        serializer = TaskListSerializer(tasks, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def action(self, request, pk=None):
        """Perform actions on task (start, pause, complete, etc.)"""
        task = get_object_or_404(Task, pk=pk)
        serializer = TaskActionSerializer(data=request.data)
        
        if serializer.is_valid():
            action_type = serializer.validated_data['action']
            reason = serializer.validated_data.get('reason', '')
            
            # Check permissions
            if action_type in ['start', 'pause', 'resume', 'complete'] and task.assigned_to != request.user:
                return Response({'error': 'You can only perform this action on your own tasks'}, 
                              status=status.HTTP_403_FORBIDDEN)
            
            if action_type in ['approve', 'reject'] and not self._can_approve_task(request.user, task):
                return Response({'error': 'You do not have permission to approve/reject this task'}, 
                              status=status.HTTP_403_FORBIDDEN)
            
            # Perform the action
            success = False
            message = ''
            
            if action_type == 'start':
                success = task.start_task()
                message = 'Task started successfully'
            elif action_type == 'pause':
                success = task.pause_task(reason)
                message = 'Task paused successfully'
            elif action_type == 'resume':
                success = task.resume_task()
                message = 'Task resumed successfully'
            elif action_type == 'complete':
                success = task.complete_task()
                message = 'Task completed successfully'
            elif action_type == 'approve':
                success = task.approve_task(request.user)
                message = 'Task approved successfully'
            elif action_type == 'reject':
                success = task.reject_task(request.user, reason)
                message = 'Task rejected successfully'
            
            if success:
                return Response({
                    'message': message,
                    'task_status': task.status,
                    'task_id': task.id
                })
            else:
                return Response({'error': f'Cannot {action_type} task in current state'}, 
                              status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _can_approve_task(self, user, task):
        """Check if user can approve/reject a task"""
        # Owner, admin, and the person who assigned the task can approve
        return (user.role in ['owner', 'admin'] or 
                user == task.assigned_by or
                (user.role == 'warehouse' and task.assigned_to.role == 'warehouse'))
    
    @action(detail=False, methods=['post'])
    def bulk_assign(self, request):
        """Bulk assign tasks to workers"""
        serializer = TaskAssignmentSerializer(data=request.data, many=True)
        
        if serializer.is_valid():
            created_tasks = []
            
            for task_data in serializer.validated_data:
                try:
                    assigned_to = User.objects.get(id=task_data['assigned_to'])
                    task_type = TaskType.objects.get(id=task_data['task_type'])
                    
                    task = Task.objects.create(
                        assigned_to=assigned_to,
                        assigned_by=request.user,
                        task_type=task_type,
                        title=task_data['title'],
                        description=task_data.get('description', ''),
                        priority=task_data.get('priority', 'normal'),
                        due_date=task_data.get('due_date'),
                        order_id=task_data.get('order'),
                        order_item_id=task_data.get('order_item'),
                        estimated_duration=timedelta(minutes=task_type.estimated_duration_minutes)
                    )
                    
                    created_tasks.append({
                        'task_id': task.id,
                        'title': task.title,
                        'assigned_to': assigned_to.username,
                        'status': 'created'
                    })
                    
                except (User.DoesNotExist, TaskType.DoesNotExist) as e:
                    created_tasks.append({
                        'title': task_data.get('title', 'Unknown'),
                        'status': 'error',
                        'message': str(e)
                    })
            
            return Response({'results': created_tasks})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get dashboard data for tasks"""
        user = request.user
        
        # Base queryset depends on user role
        if user.role == 'warehouse':
            base_queryset = Task.objects.filter(assigned_to=user)
        else:
            base_queryset = Task.objects.all()
        
        # Calculate statistics
        total_tasks = base_queryset.count()
        tasks_assigned = base_queryset.filter(status='assigned').count()
        tasks_in_progress = base_queryset.filter(status='started').count()
        tasks_completed = base_queryset.filter(status__in=['completed', 'approved']).count()
        tasks_overdue = base_queryset.filter(
            due_date__lt=timezone.now(),
            status__in=['assigned', 'started', 'paused']
        ).count()
        
        # Recent tasks
        recent_tasks = base_queryset.order_by('-created_at')[:10]
        
        # Worker summaries (only for supervisors)
        worker_summaries = []
        if user.role in ['owner', 'admin', 'warehouse']:
            warehouse_users = User.objects.filter(role='warehouse')
            for worker in warehouse_users:
                worker_tasks = Task.objects.filter(assigned_to=worker)
                total_assigned = worker_tasks.count()
                total_completed = worker_tasks.filter(status__in=['completed', 'approved']).count()
                total_approved = worker_tasks.filter(status='approved').count()
                total_in_progress = worker_tasks.filter(status='started').count()
                total_overdue = worker_tasks.filter(
                    due_date__lt=timezone.now(),
                    status__in=['assigned', 'started', 'paused']
                ).count()
                
                completion_rate = (total_completed / total_assigned * 100) if total_assigned > 0 else 0
                
                # Calculate average task time
                completed_tasks = worker_tasks.filter(status__in=['completed', 'approved'])
                avg_time = completed_tasks.aggregate(avg_time=Avg('total_time_spent'))['avg_time']
                avg_time_str = "0h 0m"
                if avg_time:
                    total_seconds = int(avg_time.total_seconds())
                    hours = total_seconds // 3600
                    minutes = (total_seconds % 3600) // 60
                    avg_time_str = f"{hours}h {minutes}m"
                
                worker_summaries.append({
                    'worker': worker.get_full_name() or worker.username,
                    'total_assigned': total_assigned,
                    'total_completed': total_completed,
                    'total_approved': total_approved,
                    'total_in_progress': total_in_progress,
                    'total_overdue': total_overdue,
                    'completion_rate': round(completion_rate, 2),
                    'average_task_time': avg_time_str
                })
        
        dashboard_data = {
            'total_tasks': total_tasks,
            'tasks_assigned': tasks_assigned,
            'tasks_in_progress': tasks_in_progress,
            'tasks_completed': tasks_completed,
            'tasks_overdue': tasks_overdue,
            'recent_tasks': TaskListSerializer(recent_tasks, many=True).data,
            'worker_summaries': worker_summaries
        }
        
        return Response(dashboard_data)


class TaskTimeSessionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TaskTimeSession.objects.all()
    serializer_class = TaskTimeSessionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['task', 'task__assigned_to']
    ordering = ['-started_at']
    
    def get_queryset(self):
        queryset = TaskTimeSession.objects.select_related('task')
        
        # If user is warehouse worker, only show their sessions
        if self.request.user.role == 'warehouse':
            queryset = queryset.filter(task__assigned_to=self.request.user)
        
        return queryset


class TaskNoteViewSet(viewsets.ModelViewSet):
    queryset = TaskNote.objects.all()
    serializer_class = TaskNoteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['task', 'note_type', 'user']
    search_fields = ['content']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = TaskNote.objects.select_related('task', 'user')
        
        # If user is warehouse worker, only show notes for their tasks
        if self.request.user.role == 'warehouse':
            queryset = queryset.filter(task__assigned_to=self.request.user)
        
        return queryset


class TaskNotificationViewSet(viewsets.ModelViewSet):
    queryset = TaskNotification.objects.all()
    serializer_class = TaskNotificationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['notification_type', 'is_read', 'recipient']
    ordering = ['-created_at']
    
    def get_queryset(self):
        # Users can only see their own notifications
        return TaskNotification.objects.filter(recipient=self.request.user)
    
    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Get unread notifications"""
        notifications = self.get_queryset().filter(is_read=False)
        serializer = self.get_serializer(notifications, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark notification as read"""
        notification = get_object_or_404(TaskNotification, pk=pk, recipient=request.user)
        notification.mark_as_read()
        return Response({'message': 'Notification marked as read'})
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        count = self.get_queryset().filter(is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        return Response({'message': f'{count} notifications marked as read'})


class TaskMaterialViewSet(viewsets.ModelViewSet):
    queryset = TaskMaterial.objects.all()
    serializer_class = TaskMaterialSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['task', 'material', 'is_allocated']
    search_fields = ['task__title', 'material__name']
    
    @action(detail=True, methods=['post'])
    def allocate(self, request, pk=None):
        """Allocate material for a task"""
        task_material = get_object_or_404(TaskMaterial, pk=pk)
        
        if task_material.allocate_material(request.user):
            return Response({'message': 'Material allocated successfully'})
        else:
            return Response({'error': 'Cannot allocate material - insufficient stock or already allocated'}, 
                          status=status.HTTP_400_BAD_REQUEST)


class TaskTemplateViewSet(viewsets.ModelViewSet):
    queryset = TaskTemplate.objects.all()
    serializer_class = TaskTemplateSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['product_type', 'is_active']
    search_fields = ['name', 'description']
    
    @action(detail=True, methods=['post'])
    def create_tasks_from_template(self, request, pk=None):
        """Create tasks from template for a specific order"""
        template = get_object_or_404(TaskTemplate, pk=pk)
        order_id = request.data.get('order_id')
        assigned_to_id = request.data.get('assigned_to_id')
        
        if not order_id or not assigned_to_id:
            return Response({'error': 'order_id and assigned_to_id are required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from orders.models import Order
            order = Order.objects.get(id=order_id)
            assigned_to = User.objects.get(id=assigned_to_id)
            
            created_tasks = []
            for step in template.steps.all():
                task = Task.objects.create(
                    title=f"{step.task_type.name} - {order.order_number}",
                    description=step.description or f"{step.task_type.name} for order {order.order_number}",
                    task_type=step.task_type,
                    assigned_to=assigned_to,
                    assigned_by=request.user,
                    order=order,
                    estimated_duration=step.estimated_duration,
                    priority='normal'
                )
                created_tasks.append({
                    'task_id': task.id,
                    'title': task.title,
                    'sequence': step.sequence_order
                })
            
            return Response({
                'message': f'{len(created_tasks)} tasks created from template',
                'tasks': created_tasks
            })
            
        except (Order.DoesNotExist, User.DoesNotExist) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class WorkerProductivityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = WorkerProductivity.objects.all()
    serializer_class = WorkerProductivitySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['worker', 'date']
    ordering = ['-date']
    
    def get_queryset(self):
        queryset = WorkerProductivity.objects.select_related('worker')
        
        # If user is warehouse worker, only show their own productivity
        if self.request.user.role == 'warehouse':
            queryset = queryset.filter(worker=self.request.user)
        
        return queryset
    
    @action(detail=False, methods=['post'])
    def calculate_daily_productivity(self, request):
        """Calculate productivity for all workers for a specific date"""
        target_date = request.data.get('date')
        if not target_date:
            target_date = timezone.now().date()
        else:
            target_date = timezone.datetime.strptime(target_date, '%Y-%m-%d').date()
        
        warehouse_users = User.objects.filter(role='warehouse')
        calculated_count = 0
        
        for worker in warehouse_users:
            productivity = WorkerProductivity.calculate_daily_productivity(worker, target_date)
            if productivity:
                calculated_count += 1
        
        return Response({
            'message': f'Calculated productivity for {calculated_count} workers',
            'date': target_date,
            'total_workers': warehouse_users.count()
        })
    
    @action(detail=False, methods=['get'])
    def summary_report(self, request):
        """Get productivity summary report"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date or not end_date:
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=7)  # Last 7 days
        else:
            start_date = timezone.datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = timezone.datetime.strptime(end_date, '%Y-%m-%d').date()
        
        productivity_records = self.get_queryset().filter(
            date__range=[start_date, end_date]
        )
        
        # Aggregate by worker
        worker_summaries = {}
        for record in productivity_records:
            worker_id = record.worker.id
            if worker_id not in worker_summaries:
                worker_summaries[worker_id] = {
                    'worker': record.worker.get_full_name() or record.worker.username,
                    'total_tasks_assigned': 0,
                    'total_tasks_completed': 0,
                    'total_tasks_approved': 0,
                    'total_time_worked': timedelta(0),
                    'average_completion_rate': 0,
                    'days_worked': 0
                }
            
            summary = worker_summaries[worker_id]
            summary['total_tasks_assigned'] += record.tasks_assigned
            summary['total_tasks_completed'] += record.tasks_completed
            summary['total_tasks_approved'] += record.tasks_approved
            summary['total_time_worked'] += record.total_time_worked
            summary['average_completion_rate'] += record.completion_rate
            summary['days_worked'] += 1
        
        # Calculate averages
        for summary in worker_summaries.values():
            if summary['days_worked'] > 0:
                summary['average_completion_rate'] = summary['average_completion_rate'] / summary['days_worked']
            
            # Format time worked
            total_seconds = int(summary['total_time_worked'].total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            summary['total_time_worked_formatted'] = f"{hours}h {minutes}m"
        
        return Response({
            'date_range': {
                'start_date': start_date,
                'end_date': end_date
            },
            'worker_summaries': list(worker_summaries.values())
        })