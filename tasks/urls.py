from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'task-types', views.TaskTypeViewSet)
router.register(r'tasks', views.TaskViewSet)
router.register(r'time-sessions', views.TaskTimeSessionViewSet)
router.register(r'notes', views.TaskNoteViewSet)
router.register(r'notifications', views.TaskNotificationViewSet)
router.register(r'materials', views.TaskMaterialViewSet)
router.register(r'templates', views.TaskTemplateViewSet)
router.register(r'productivity', views.WorkerProductivityViewSet)

urlpatterns = [
    path('', include(router.urls)),
]