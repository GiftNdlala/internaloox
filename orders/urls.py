from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'orders'

router = DefaultRouter()
router.register(r'customers', views.CustomerViewSet)
router.register(r'orders', views.OrderViewSet)
router.register(r'payment-proofs', views.PaymentProofViewSet)
router.register(r'order-history', views.OrderHistoryViewSet)
router.register(r'products', views.ProductViewSet)
router.register(r'colors', views.ColorViewSet)
router.register(r'fabrics', views.FabricViewSet)
router.register(r'order-items', views.OrderItemViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard-stats/', views.dashboard_stats, name='dashboard_stats'),
] 