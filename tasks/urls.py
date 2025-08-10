from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'task_types', views.TaskTypeViewSet)  # Changed to match frontend
router.register(r'tasks', views.TaskViewSet)
router.register(r'time_sessions', views.TaskTimeSessionViewSet)  # Changed to match frontend
router.register(r'notes', views.TaskNoteViewSet)
router.register(r'task_notifications', views.TaskNotificationViewSet)  # Changed to match frontend
router.register(r'materials', views.TaskMaterialViewSet)
router.register(r'templates', views.TaskTemplateViewSet)
router.register(r'productivity', views.WorkerProductivityViewSet)
router.register(r'dashboard', views.WarehouseDashboardViewSet, basename='warehouse-dashboard')
router.register(r'notifications', views.NotificationViewSet, basename='notifications')

urlpatterns = [
    path('', include(router.urls)),
]