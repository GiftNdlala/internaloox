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
router.register(r'color-references', views.ColorReferenceViewSet)
router.register(r'fabric-references', views.FabricReferenceViewSet)
router.register(r'order-items', views.OrderItemViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard-stats/', views.dashboard_stats, name='dashboard_stats'),
    # Frontend-aligned endpoints
    path('orders/warehouse_orders/', views.OrderViewSet.as_view({'get': 'warehouse_orders'}), name='warehouse_orders'),
    path('orders/<int:pk>/create_task/', views.OrderViewSet.as_view({'post': 'create_task'}), name='order_create_task'),
    
    # Role-based dashboard endpoints
    path('orders/owner_dashboard/', views.OrderViewSet.as_view({'get': 'owner_dashboard_orders'}), name='owner_dashboard_orders'),
    path('orders/admin_dashboard/', views.OrderViewSet.as_view({'get': 'admin_dashboard_orders'}), name='admin_dashboard_orders'),
    path('orders/warehouse_dashboard/', views.OrderViewSet.as_view({'get': 'warehouse_dashboard_orders'}), name='warehouse_dashboard_orders'),
    path('orders/delivery_dashboard/', views.OrderViewSet.as_view({'get': 'delivery_dashboard_orders'}), name='delivery_dashboard_orders'),
    
    # Order management endpoints
    path('orders/<int:pk>/cancel/', views.OrderViewSet.as_view({'post': 'cancel_order'}), name='cancel_order'),
    path('orders/<int:pk>/update_status/', views.OrderViewSet.as_view({'patch': 'update_status'}), name='update_order_status'),
] 