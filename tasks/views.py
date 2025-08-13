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
    TaskMaterial, TaskTemplate, TaskTemplateStep, WorkerProductivity,
    Notification, create_notification
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

    def list(self, request, *args, **kwargs):
        # Auto-seed defaults if empty so frontend always gets task types
        if not TaskType.objects.exists():
            defaults = [
                {'name': 'Material Preparation', 'description': 'Prepare and gather materials for production', 'estimated_duration_minutes': 30, 'requires_materials': True, 'sequence_order': 1},
                {'name': 'Cutting', 'description': 'Cut materials according to specifications', 'estimated_duration_minutes': 60, 'requires_materials': True, 'sequence_order': 2},
                {'name': 'Frame Assembly', 'description': 'Assemble wooden frame structure', 'estimated_duration_minutes': 90, 'requires_materials': True, 'sequence_order': 3},
                {'name': 'Foam Installation', 'description': 'Install foam padding and cushioning', 'estimated_duration_minutes': 45, 'requires_materials': True, 'sequence_order': 4},
                {'name': 'Upholstery', 'description': 'Apply fabric covering and upholstery work', 'estimated_duration_minutes': 120, 'requires_materials': True, 'sequence_order': 5},
                {'name': 'Finishing', 'description': 'Final touches, trimming, and detail work', 'estimated_duration_minutes': 60, 'requires_materials': True, 'sequence_order': 6},
                {'name': 'Quality Check', 'description': 'Inspect finished product for quality', 'estimated_duration_minutes': 30, 'requires_materials': False, 'sequence_order': 7},
                {'name': 'Packaging', 'description': 'Package product for delivery', 'estimated_duration_minutes': 20, 'requires_materials': True, 'sequence_order': 8},
                {'name': 'Stock Management', 'description': 'Update inventory and stock levels', 'estimated_duration_minutes': 15, 'requires_materials': False, 'sequence_order': 9},
                {'name': 'Maintenance', 'description': 'Equipment and workspace maintenance', 'estimated_duration_minutes': 45, 'requires_materials': False, 'sequence_order': 10},
            ]
            for d in defaults:
                TaskType.objects.get_or_create(name=d['name'], defaults=d)
        return super().list(request, *args, **kwargs)


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['priority', 'assigned_to', 'assigned_by', 'task_type', 'order']
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
        if user.is_warehouse_worker and not user.can_manage_tasks:
            queryset = queryset.filter(assigned_to=user)
        
        # Filter by assigned worker (for task history functionality)
        assigned_worker = self.request.query_params.get('assigned_worker')
        if assigned_worker:
            try:
                worker_id = int(assigned_worker)
                queryset = queryset.filter(assigned_to_id=worker_id)
            except (ValueError, TypeError):
                # Invalid worker ID, return empty queryset
                queryset = queryset.none()
        
        # Filter by overdue status
        if self.request.query_params.get('overdue') == 'true':
            queryset = queryset.filter(
                due_date__lt=timezone.now(),
                status__in=['assigned', 'started', 'paused']
            )
        
        # Filter by running status
        if self.request.query_params.get('running') == 'true':
            queryset = queryset.filter(status='started')
        
        # Filter by status
        status_param = self.request.query_params.get('status')
        if status_param and status_param != 'all':
            # Handle multiple status values separated by comma
            if ',' in status_param:
                status_list = [s.strip() for s in status_param.split(',')]
                queryset = queryset.filter(status__in=status_list)
            else:
                queryset = queryset.filter(status=status_param)
        
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
    def perform_action(self, request, pk=None):
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
                    'task_id': task.id,
                    'is_running': task.is_timer_running,
                    'time_elapsed': task.time_elapsed_seconds,
                    'progress_percentage': task.progress_percentage,
                    'can_start': task.status == 'assigned',
                    'can_pause': task.status == 'started',
                    'can_resume': task.status == 'paused',
                    'can_complete': task.status in ['started', 'paused']
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
    
    @action(detail=False, methods=['post'])
    def bulk_reassign(self, request):
        """Reassign multiple existing tasks to a worker"""
        if not request.user.can_manage_tasks:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        task_ids = request.data.get('task_ids', [])
        worker_id = request.data.get('worker_id')
        
        if not task_ids or not worker_id:
            return Response({'error': 'task_ids and worker_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            worker = User.objects.get(id=worker_id)
            if not worker.is_warehouse_worker:
                return Response({'error': 'Can only assign tasks to warehouse workers'}, status=status.HTTP_400_BAD_REQUEST)
            
            tasks = Task.objects.filter(id__in=task_ids)
            updated_count = tasks.update(
                assigned_to=worker,
                status='assigned'
            )
            
            # Send notification to worker
            create_notification(
                user=worker,
                message=f"{updated_count} tasks assigned to you",
                notification_type='task_assigned',
                priority='normal'
            )
            
            return Response({
                'message': f'{updated_count} tasks assigned successfully',
                'assigned_count': updated_count
            })
            
        except User.DoesNotExist:
            return Response({'error': 'Worker not found'}, status=status.HTTP_404_NOT_FOUND)
    
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
            'worker_summaries': list(worker_summaries.values()),
            'manage_workers_endpoint': '/api/users/users/?role=warehouse_worker,warehouse',
            'can_manage_workers': True
        })


# Add comprehensive warehouse worker dashboard endpoints
class WarehouseDashboardViewSet(viewsets.ViewSet):
    """Comprehensive warehouse dashboard endpoints for frontend"""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def worker_dashboard(self, request):
        """Complete dashboard for warehouse workers"""
        user = request.user
        
        # Only warehouse workers and managers can access this view
        if not user.is_warehouse:
            return Response({'error': 'Access denied - Warehouse role required'}, status=status.HTTP_403_FORBIDDEN)
        
        # Worker's tasks
        my_tasks = Task.objects.filter(assigned_to=user).select_related('task_type', 'order')
        
        # Task statistics
        total_tasks = my_tasks.count()
        assigned_tasks = my_tasks.filter(status='assigned').count()
        in_progress_tasks = my_tasks.filter(status='started').count()
        paused_tasks = my_tasks.filter(status='paused').count()
        completed_today = my_tasks.filter(
            status__in=['completed', 'approved'],
            completed_at__date=timezone.now().date()
        ).count()
        overdue_tasks = my_tasks.filter(
            due_date__lt=timezone.now(),
            status__in=['assigned', 'started', 'paused']
        ).count()
        
        # Current active task (if any)
        active_task = my_tasks.filter(status='started').first()
        
        # Next task to work on (highest priority assigned task)
        next_task = my_tasks.filter(status='assigned').order_by('-priority', 'due_date', 'created_at').first()
        
        # Recent notifications
        recent_notifications = TaskNotification.objects.filter(
            recipient=user,
            is_read=False
        ).order_by('-created_at')[:5]
        
        # Today's productivity
        today = timezone.now().date()
        today_productivity = WorkerProductivity.objects.filter(
            worker=user,
            date=today
        ).first()
        
        # Time tracking for active task
        active_session = None
        time_elapsed_today = timedelta(0)
        if active_task:
            active_session = active_task.time_sessions.filter(ended_at__isnull=True).first()
            # Calculate total time worked today
            today_sessions = TaskTimeSession.objects.filter(
                task__assigned_to=user,
                started_at__date=today
            )
            for session in today_sessions:
                if session.ended_at:
                    time_elapsed_today += session.duration
                elif session == active_session:
                    time_elapsed_today += timezone.now() - session.started_at
        
        # Task history (last 10 completed tasks)
        completed_tasks = my_tasks.filter(
            status__in=['completed', 'approved']
        ).order_by('-completed_at')[:10]
        
        # Tasks by priority for worker planning
        urgent_tasks = my_tasks.filter(priority='urgent', status__in=['assigned', 'started', 'paused']).count()
        high_tasks = my_tasks.filter(priority='high', status__in=['assigned', 'started', 'paused']).count()
        
        return Response({
            'worker_info': {
                'id': user.id,
                'name': user.get_full_name() or user.username,
                'role': user.get_role_display(),
                'username': user.username,
                'employee_id': getattr(user, 'employee_id', None),
                'shift_start': getattr(user, 'shift_start', None),
                'shift_end': getattr(user, 'shift_end', None)
            },
            'task_summary': {
                'total_tasks': total_tasks,
                'assigned': assigned_tasks,
                'in_progress': in_progress_tasks,
                'paused': paused_tasks,
                'completed_today': completed_today,
                'overdue': overdue_tasks,
                'urgent_pending': urgent_tasks,
                'high_pending': high_tasks
            },
            'active_task': TaskSerializer(active_task).data if active_task else None,
            'next_task': TaskSerializer(next_task).data if next_task else None,
            'active_session': TaskTimeSessionSerializer(active_session).data if active_session else None,
            'time_tracking': {
                'time_elapsed_today': str(time_elapsed_today),
                'time_elapsed_today_formatted': self._format_duration(time_elapsed_today),
                'is_timer_running': active_task.is_timer_running if active_task else False
            },
            'recent_tasks': TaskListSerializer(my_tasks.order_by('-updated_at')[:10], many=True).data,
            'completed_tasks_history': TaskListSerializer(completed_tasks, many=True).data,
            'notifications': TaskNotificationSerializer(recent_notifications, many=True).data,
            'today_productivity': WorkerProductivitySerializer(today_productivity).data if today_productivity else None,
            'quick_actions': {
                'can_start_task': next_task is not None,
                'can_pause_active': active_task is not None and active_task.status == 'started',
                'can_resume_paused': my_tasks.filter(status='paused').exists(),
                'can_complete_active': active_task is not None and active_task.status in ['started', 'paused']
            }
        })
    
    @action(detail=False, methods=['get'])
    def supervisor_dashboard(self, request):
        """Dashboard for supervisors (admin, owner, warehouse managers)"""
        user = request.user
        
        # Only supervisors can access
        if user.role not in ['owner', 'admin', 'warehouse']:
            return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
        
        # All warehouse workers (include legacy and manager for overview)
        warehouse_workers = User.objects.filter(
            Q(role='warehouse_worker') | Q(role='warehouse')
        )
        
        # Task overview (restrict to warehouse roles only)
        all_tasks = Task.objects.filter(
            Q(assigned_to__role__in=['warehouse_worker', 'warehouse'])
        )
        total_tasks = all_tasks.count()
        assigned_tasks = all_tasks.filter(status='assigned').count()
        in_progress_tasks = all_tasks.filter(status='started').count()
        completed_tasks = all_tasks.filter(status__in=['completed', 'approved']).count()
        overdue_tasks = all_tasks.filter(
            due_date__lt=timezone.now(),
            status__in=['assigned', 'started', 'paused']
        ).count()
        
        # Worker status
        worker_status = []
        for worker in warehouse_workers:
            worker_tasks = all_tasks.filter(assigned_to=worker)
            active_task = worker_tasks.filter(status='started').first()
            
            worker_status.append({
                'worker_id': worker.id,
                'worker_name': worker.get_full_name() or worker.username,
                'total_tasks': worker_tasks.count(),
                'active_task': TaskListSerializer(active_task).data if active_task else None,
                'completed_today': worker_tasks.filter(
                    status__in=['completed', 'approved'],
                    completed_at__date=timezone.now().date()
                ).count(),
                'overdue_tasks': worker_tasks.filter(
                    due_date__lt=timezone.now(),
                    status__in=['assigned', 'started', 'paused']
                ).count()
            })
        
        # Recent task activities
        recent_activities = Task.objects.filter(
            updated_at__gte=timezone.now() - timedelta(hours=24)
        ).select_related('assigned_to', 'task_type').order_by('-updated_at')[:20]
        
        # Tasks needing approval
        tasks_for_approval = all_tasks.filter(status='completed')
        
        return Response({
            'overview': {
                'total_tasks': total_tasks,
                'assigned': assigned_tasks,
                'in_progress': in_progress_tasks,
                'completed': completed_tasks,
                'overdue': overdue_tasks,
                'total_workers': warehouse_workers.count()
            },
            'worker_status': worker_status,
            'recent_activities': TaskListSerializer(recent_activities, many=True).data,
            'tasks_for_approval': TaskListSerializer(tasks_for_approval, many=True).data,
            'overdue_tasks': TaskListSerializer(
                all_tasks.filter(
                    due_date__lt=timezone.now(),
                    status__in=['assigned', 'started', 'paused']
                )[:10], 
                many=True
            ).data
        })
    
    @action(detail=False, methods=['get'])
    def task_assignment_data(self, request):
        """Data needed for task assignment interface"""
        # Available workers
        warehouse_workers = User.objects.filter(
            Q(role='warehouse_worker') | Q(role='warehouse'), 
            is_active=True
        )
        
        # Available task types
        task_types = TaskType.objects.filter(is_active=True)
        
        # Recent orders that might need tasks
        from orders.models import Order
        recent_orders = Order.objects.filter(
            order_status__in=['deposit_paid', 'order_ready']
        ).order_by('-created_at')[:20]
        
        # Task templates
        task_templates = TaskTemplate.objects.filter(is_active=True)
        
        return Response({
            'workers': [
                {
                    'id': worker.id,
                    'name': worker.get_full_name() or worker.username,
                    'username': worker.username,
                    'active_tasks_count': Task.objects.filter(
                        assigned_to=worker,
                        status__in=['assigned', 'started']
                    ).count()
                }
                for worker in warehouse_workers
            ],
            'task_types': TaskTypeSerializer(task_types, many=True).data,
            'recent_orders': [
                {
                    'id': order.id,
                    'order_number': order.order_number,
                    'customer_name': order.customer.name if order.customer else order.customer_name,
                    'status': order.order_status,
                    'created_at': order.created_at
                }
                for order in recent_orders
            ],
            'task_templates': TaskTemplateSerializer(task_templates, many=True).data
        })
    
    @action(detail=False, methods=['post'])
    def quick_task_assign(self, request):
        """Quick task assignment for supervisors"""
        assigned_to_id = request.data.get('assigned_to')
        task_type_id = request.data.get('task_type')
        title = request.data.get('title')
        description = request.data.get('description', '')
        priority = request.data.get('priority', 'normal')
        due_date = request.data.get('due_date')
        order_id = request.data.get('order_id')
        
        try:
            assigned_to = User.objects.get(id=assigned_to_id, role='warehouse')
            task_type = TaskType.objects.get(id=task_type_id)
            
            task = Task.objects.create(
                assigned_to=assigned_to,
                assigned_by=request.user,
                task_type=task_type,
                title=title,
                description=description,
                priority=priority,
                due_date=due_date,
                order_id=order_id,
                estimated_duration=timedelta(minutes=task_type.estimated_duration_minutes)
            )
            
            return Response({
                'message': 'Task assigned successfully',
                'task': TaskSerializer(task).data
            })
            
        except (User.DoesNotExist, TaskType.DoesNotExist) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def real_time_updates(self, request):
        """Real-time updates for dashboard (to be called periodically)"""
        user = request.user
        
        # Get timestamp from last check
        last_check = request.query_params.get('last_check')
        if last_check:
            last_check = timezone.datetime.fromisoformat(last_check.replace('Z', '+00:00'))
        else:
            last_check = timezone.now() - timedelta(minutes=5)
        
        updates = {
            'timestamp': timezone.now().isoformat(),
            'new_notifications': [],
            'task_updates': [],
            'stock_alerts': []
        }
        
        # New notifications
        new_notifications = TaskNotification.objects.filter(
            recipient=user,
            created_at__gt=last_check
        ).order_by('-created_at')
        updates['new_notifications'] = TaskNotificationSerializer(new_notifications, many=True).data
        
        # Task updates (for supervisors)
        if user.role in ['owner', 'admin', 'warehouse']:
            updated_tasks = Task.objects.filter(
                updated_at__gt=last_check
            ).select_related('assigned_to', 'order')
            updates['task_updates'] = TaskListSerializer(updated_tasks, many=True).data
        
        # Stock alerts (if user has inventory access)
        if user.role in ['owner', 'admin', 'warehouse']:
            from inventory.models import StockAlert
            new_alerts = StockAlert.objects.filter(
                status='active',
                created_at__gt=last_check
            ).select_related('material')
            from inventory.serializers import StockAlertSerializer
            updates['stock_alerts'] = StockAlertSerializer(new_alerts, many=True).data
        
        return Response(updates)
    
    @action(detail=False, methods=['post'])
    def quick_start_next_task(self, request):
        """Quick start the next assigned task for current worker"""
        user = request.user
        
        if not user.is_warehouse:
            return Response({'error': 'Access denied - Warehouse role required'}, status=status.HTTP_403_FORBIDDEN)
        
        # Check if user already has a running task
        running_task = Task.objects.filter(assigned_to=user, status='started').first()
        if running_task:
            return Response({
                'error': 'You already have a task in progress',
                'current_task': {
                    'id': running_task.id,
                    'title': running_task.title,
                    'time_elapsed': running_task.time_elapsed_seconds
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get next task to work on
        next_task = Task.objects.filter(
            assigned_to=user,
            status='assigned'
        ).order_by('-priority', 'due_date', 'created_at').first()
        
        if not next_task:
            return Response({
                'error': 'No assigned tasks available to start',
                'suggestion': 'Check with your supervisor for new task assignments'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Start the task
        if next_task.start_task():
            return Response({
                'message': f'Task "{next_task.title}" started successfully',
                'task': TaskSerializer(next_task).data,
                'quick_actions': {
                    'can_pause': True,
                    'can_complete': True,
                    'can_start_next': False
                }
            })
        else:
            return Response({
                'error': 'Failed to start task',
                'task_status': next_task.status
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def quick_pause_active_task(self, request):
        """Quick pause the currently active task for current worker"""
        user = request.user
        
        if not user.is_warehouse:
            return Response({'error': 'Access denied - Warehouse role required'}, status=status.HTTP_403_FORBIDDEN)
        
        active_task = Task.objects.filter(assigned_to=user, status='started').first()
        if not active_task:
            return Response({
                'error': 'No active task to pause',
                'suggestion': 'Start a task first before pausing'
            }, status=status.HTTP_404_NOT_FOUND)
        
        reason = request.data.get('reason', 'Quick pause from dashboard')
        
        if active_task.pause_task(reason):
            return Response({
                'message': f'Task "{active_task.title}" paused successfully',
                'task': TaskSerializer(active_task).data,
                'quick_actions': {
                    'can_resume': True,
                    'can_complete': True,
                    'can_start_next': True
                }
            })
        else:
            return Response({
                'error': 'Failed to pause task',
                'task_status': active_task.status
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def quick_complete_active_task(self, request):
        """Quick complete the currently active task for current worker"""
        user = request.user
        
        if not user.is_warehouse:
            return Response({'error': 'Access denied - Warehouse role required'}, status=status.HTTP_403_FORBIDDEN)
        
        # Get active or paused task
        active_task = Task.objects.filter(
            assigned_to=user,
            status__in=['started', 'paused']
        ).first()
        
        if not active_task:
            return Response({
                'error': 'No active task to complete',
                'suggestion': 'Start a task first before completing'
            }, status=status.HTTP_404_NOT_FOUND)
        
        completion_notes = request.data.get('completion_notes', '')
        if completion_notes:
            active_task.completion_notes = completion_notes
            active_task.save()
        
        if active_task.complete_task():
            return Response({
                'message': f'Task "{active_task.title}" completed successfully',
                'task': TaskSerializer(active_task).data,
                'quick_actions': {
                    'can_start_next': True,
                    'can_pause': False,
                    'can_complete': False
                },
                'next_steps': 'Task is now ready for supervisor review'
            })
        else:
            return Response({
                'error': 'Failed to complete task',
                'task_status': active_task.status
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def orders_with_tasks(self, request):
        """Get orders organized by task status for warehouse management"""
        from orders.models import Order
        
        # Get orders that are in warehouse processing
        warehouse_orders = Order.objects.filter(
            order_status__in=['deposit_paid', 'order_ready'],
            production_status__in=['not_started', 'cutting', 'sewing', 'finishing', 'quality_check']
        ).select_related('customer').prefetch_related('tasks__assigned_to', 'tasks__task_type')
        
        orders_by_status = {
            'no_tasks': [],
            'in_progress': [],
            'completed': [],
            'mixed_status': []
        }
        
        for order in warehouse_orders:
            tasks = order.tasks.all()
            
            if not tasks.exists():
                # Orders without tasks assigned
                orders_by_status['no_tasks'].append({
                    'id': order.id,
                    'order_number': order.order_number,
                    'customer_name': order.customer.name if order.customer else order.customer_name,
                    'delivery_deadline': order.delivery_deadline,
                    'urgency': self._calculate_urgency(order),
                    'items_count': order.items.count(),
                    'total_amount': float(order.total_amount),
                    'tasks': []
                })
            else:
                # Orders with tasks
                task_statuses = list(tasks.values_list('status', flat=True))
                completed_statuses = ['completed', 'approved']
                in_progress_statuses = ['started']
                
                tasks_data = []
                for task in tasks:
                    tasks_data.append({
                        'id': task.id,
                        'title': task.title,
                        'task_type': task.task_type.name,
                        'assigned_to': task.assigned_to.get_full_name() or task.assigned_to.username,
                        'assigned_to_id': task.assigned_to.id,
                        'status': task.status,
                        'priority': task.priority,
                        'is_running': task.is_running,
                        'time_elapsed_formatted': self._format_duration(task.time_elapsed),
                        'estimated_duration': str(task.estimated_duration)
                    })
                
                order_data = {
                    'id': order.id,
                    'order_number': order.order_number,
                    'customer_name': order.customer.name if order.customer else order.customer_name,
                    'delivery_deadline': order.delivery_deadline,
                    'urgency': self._calculate_urgency(order),
                    'items_count': order.items.count(),
                    'total_amount': float(order.total_amount),
                    'tasks': tasks_data,
                    'task_summary': {
                        'total': len(tasks_data),
                        'completed': len([t for t in tasks_data if t['status'] in completed_statuses]),
                        'in_progress': len([t for t in tasks_data if t['status'] in in_progress_statuses]),
                        'pending': len([t for t in tasks_data if t['status'] == 'assigned'])
                    }
                }
                
                # Categorize based on task completion
                if all(status in completed_statuses for status in task_statuses):
                    orders_by_status['completed'].append(order_data)
                elif any(status in in_progress_statuses for status in task_statuses):
                    orders_by_status['in_progress'].append(order_data)
                else:
                    orders_by_status['mixed_status'].append(order_data)
        
        # Sort each category by urgency
        for category in orders_by_status.values():
            category.sort(key=lambda x: (
                0 if x['urgency'] == 'critical' else
                1 if x['urgency'] == 'high' else
                2 if x['urgency'] == 'medium' else 3
            ))
        
        return Response({
            'orders_by_status': orders_by_status,
            'summary': {
                'no_tasks': len(orders_by_status['no_tasks']),
                'in_progress': len(orders_by_status['in_progress']),
                'completed': len(orders_by_status['completed']),
                'mixed_status': len(orders_by_status['mixed_status']),
                'total_orders': sum(len(orders) for orders in orders_by_status.values())
            }
        })
    
    @action(detail=False, methods=['get'])
    def tasks_by_order(self, request):
        """Get tasks organized by order for worker view"""
        user = request.user
        
        # Get tasks assigned to current user (if warehouse worker)
        if user.is_warehouse_worker and not user.can_manage_tasks:
            tasks = Task.objects.filter(assigned_to=user)
        else:
            tasks = Task.objects.all()
        
        tasks = tasks.select_related('order', 'task_type', 'assigned_to').order_by('order__delivery_deadline', 'created_at')
        
        # Group tasks by order
        tasks_by_order = {}
        for task in tasks:
            order_key = task.order.order_number if task.order else 'No Order'
            
            if order_key not in tasks_by_order:
                tasks_by_order[order_key] = {
                    'order_info': {
                        'id': task.order.id if task.order else None,
                        'order_number': task.order.order_number if task.order else 'No Order',
                        'customer_name': (task.order.customer.name if task.order.customer else task.order.customer_name) if task.order else 'N/A',
                        'delivery_deadline': task.order.delivery_deadline if task.order else None,
                        'urgency': self._calculate_urgency(task.order) if task.order else 'low',
                        'total_amount': float(task.order.total_amount) if task.order and task.order.total_amount is not None else 0.0,
                    },
                    'tasks': []
                }
            
            tasks_by_order[order_key]['tasks'].append({
                'id': task.id,
                'title': task.title,
                'task_type': task.task_type.name,
                'assigned_to': task.assigned_to.get_full_name() or task.assigned_to.username,
                'status': task.status,
                'priority': task.priority,
                'is_running': task.is_running,
                'is_overdue': task.is_overdue,
                'time_elapsed_formatted': self._format_duration(task.time_elapsed),
                'total_time_formatted': self._format_duration(task.total_time_spent),
                'due_date': task.due_date,
                'created_at': task.created_at,
                'can_start': task.status == 'assigned',
                'can_pause': task.status == 'started',
                'can_complete': task.status in ['started', 'paused']
            })
        
        # Convert to list and sort by urgency
        orders_list = list(tasks_by_order.values())
        orders_list.sort(key=lambda x: (
            0 if x['order_info']['urgency'] == 'critical' else
            1 if x['order_info']['urgency'] == 'high' else
            2 if x['order_info']['urgency'] == 'medium' else 3,
            x['order_info']['delivery_deadline'] or timezone.now().date() + timedelta(days=999)
        ))
        
        return Response({
            'orders_with_tasks': orders_list,
            'summary': {
                'total_orders': len(orders_list),
                'total_tasks': sum(len(order['tasks']) for order in orders_list),
                'active_tasks': sum(len([t for t in order['tasks'] if t['is_running']]) for order in orders_list)
            }
        })
    
    def _calculate_urgency(self, order):
        """Helper method to calculate order urgency"""
        if not order or not order.delivery_deadline:
            return 'low'
        
        today = timezone.now().date()
        days_until_deadline = (order.delivery_deadline - today).days
        
        if days_until_deadline <= 2:
            return 'critical'
        elif days_until_deadline <= 5:
            return 'high'
        elif days_until_deadline <= 10:
            return 'medium'
        else:
            return 'low'
    
    def _format_duration(self, duration):
        """Helper method to format duration"""
        if not duration:
            return "0h 0m"
        
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{hours}h {minutes}m"
    
    @action(detail=False, methods=['get'])
    def real_time_updates(self, request):
        """Get real-time updates for dashboard"""
        from django.utils.dateparse import parse_datetime
        
        since = request.GET.get('since')
        user = request.user
        
        updates = {
            'has_updates': False,
            'notifications': [],
            'task_updates': [],
            'stock_alerts': [],
            'timestamp': timezone.now().isoformat()
        }
        
        # Get notifications since last check
        notifications_qs = Notification.objects.filter(user=user)
        if since:
            try:
                since_dt = parse_datetime(since)
                if since_dt:
                    notifications_qs = notifications_qs.filter(created_at__gt=since_dt)
            except:
                pass
        
        notifications = notifications_qs.order_by('-created_at')[:10]
        if notifications.exists():
            updates['has_updates'] = True
            updates['notifications'] = [{
                'id': n.id,
                'message': n.message,
                'type': n.type,
                'priority': n.priority,
                'is_read': n.is_read,
                'created_at': n.created_at.isoformat(),
                'task_id': n.task_id if n.task else None,
                'order_id': n.order_id if n.order else None
            } for n in notifications]
        
        # Get task updates for managers
        if user.can_manage_tasks:
            task_updates_qs = Task.objects.filter(
                status__in=['started', 'completed', 'paused']
            )
            if since:
                try:
                    since_dt = parse_datetime(since)
                    if since_dt:
                        task_updates_qs = task_updates_qs.filter(updated_at__gt=since_dt)
                except:
                    pass
            
            task_updates = task_updates_qs.select_related('assigned_to', 'order')[:20]
            if task_updates.exists():
                updates['has_updates'] = True
                updates['task_updates'] = [{
                    'id': t.id,
                    'title': t.title,
                    'status': t.status,
                    'assigned_to': t.assigned_to.get_full_name() or t.assigned_to.username,
                    'order_number': t.order.order_number if t.order else None,
                    'is_running': t.is_timer_running,
                    'updated_at': t.updated_at.isoformat()
                } for t in task_updates]
        
        # Get stock alerts (basic implementation)
        if user.role in ['admin', 'owner', 'warehouse_worker', 'warehouse', 'warehouse_manager']:
            try:
                from inventory.models import Material
                from django.db.models import F
                stock_alerts = Material.objects.filter(
                    current_stock__lte=F('minimum_stock_level')
                )[:10]
                if stock_alerts.exists():
                    updates['has_updates'] = True
                    updates['stock_alerts'] = [{
                        'id': m.id,
                        'name': m.name,
                        'current_stock': m.current_stock,
                        'minimum_stock_level': m.minimum_stock_level,
                        'unit': m.unit
                    } for m in stock_alerts]
            except:
                # If inventory app isn't available, skip stock alerts
                pass
        
        return Response(updates)


class NotificationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing notifications"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')
    
    def get_serializer_class(self):
        # For now, return a simple dict representation
        from rest_framework import serializers
        
        class NotificationSerializer(serializers.ModelSerializer):
            class Meta:
                model = Notification
                fields = ['id', 'message', 'type', 'priority', 'is_read', 'created_at', 'task', 'order']
                read_only_fields = ['id', 'created_at']
        
        return NotificationSerializer
    
    def list(self, request, *args, **kwargs):
        notifications = self.get_queryset()[:20]
        data = [
            {
                'id': n.id,
                'message': n.message,
                'type': n.type,
                'priority': n.priority,
                'is_read': n.is_read,
                'created_at': n.created_at.isoformat(),
                'task': {
                    'id': n.task.id,
                    'title': n.task.title,
                    'order_number': n.task.order.order_number if n.task and n.task.order else None,
                } if n.task else None
            }
            for n in notifications
        ]
        return Response(data)
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read for current user"""
        updated_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).update(
            is_read=True,
            read_at=timezone.now()
        )
        
        return Response({
            'message': f'{updated_count} notifications marked as read',
            'updated_count': updated_count
        })
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark a specific notification as read"""
        notification = self.get_object()
        notification.mark_as_read()
        
        return Response({
            'message': 'Notification marked as read',
            'is_read': notification.is_read
        })