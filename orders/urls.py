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
    
    # Core workflow endpoints
    path('orders/workflow_dashboard/', views.OrderViewSet.as_view({'get': 'order_workflow_dashboard'}), name='order_workflow_dashboard'),
    path('orders/management_data/', views.OrderViewSet.as_view({'get': 'order_management_data'}), name='order_management_data'),
    
    # Order actions
    path('orders/<int:pk>/advance_workflow/', views.OrderViewSet.as_view({'post': 'advance_workflow'}), name='advance_workflow'),
    path('orders/<int:pk>/assign/', views.OrderViewSet.as_view({'post': 'assign_order'}), name='assign_order'),
    path('orders/<int:pk>/cancel/', views.OrderViewSet.as_view({'post': 'cancel_order'}), name='cancel_order'),
    path('orders/<int:pk>/update_status/', views.OrderViewSet.as_view({'patch': 'update_status'}), name='update_order_status'),
    
    # Role-based dashboard endpoints
    path('orders/owner_dashboard/', views.OrderViewSet.as_view({'get': 'owner_dashboard_orders'}), name='owner_dashboard_orders'),
    path('orders/admin_dashboard/', views.OrderViewSet.as_view({'get': 'admin_dashboard_orders'}), name='admin_dashboard_orders'),
    path('orders/warehouse_dashboard/', views.OrderViewSet.as_view({'get': 'warehouse_dashboard_orders'}), name='warehouse_dashboard_orders'),
    path('orders/delivery_dashboard/', views.OrderViewSet.as_view({'get': 'delivery_dashboard_orders'}), name='delivery_dashboard_orders'),
    
    # Legacy/existing endpoints
    path('orders/warehouse_orders/', views.OrderViewSet.as_view({'get': 'warehouse_orders'}), name='warehouse_orders'),
    path('orders/<int:pk>/create_task/', views.OrderViewSet.as_view({'post': 'create_task'}), name='order_create_task'),
    path('orders/<int:pk>/escalate_priority/', views.OrderViewSet.as_view({'post': 'escalate_priority'}), name='escalate_priority'),
    path('orders/<int:pk>/assign_warehouse/', views.OrderViewSet.as_view({'post': 'assign_warehouse'}), name='assign_warehouse'),
    path('orders/<int:pk>/assign_delivery/', views.OrderViewSet.as_view({'post': 'assign_delivery'}), name='assign_delivery'),
] 