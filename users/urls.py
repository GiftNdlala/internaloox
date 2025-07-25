from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from django.views.decorators.csrf import csrf_exempt

app_name = 'users'

router = DefaultRouter()
router.register(r'users', views.UserViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('current-user/', views.CurrentUserView.as_view(), name='current_user'),
    path('permissions/', views.UserPermissionsView.as_view(), name='user_permissions'),
    path('create/', views.CreateUserView.as_view(), name='create_user'),  # NEW SECURE ENDPOINT
    path('create-admin/', views.create_admin_user, name='create_admin_user'),  # DEPRECATED
] 