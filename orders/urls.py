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
router.register(r'payments/transactions', views.PaymentTransactionViewSet, basename='payment-transactions')

urlpatterns = [
    path('', include(router.urls)),
    
    # Status options
    path('orders/status_options/', views.OrderViewSet.as_view({'get': 'status_options'}), name='status_options'),
    path('status_options/', views.OrderViewSet.as_view({'get': 'status_options'}), name='status_options_alias'),

    # Payments
    path('orders/<int:pk>/update_payment/', views.OrderViewSet.as_view({'patch': 'update_payment'}), name='update_payment'),
    path('orders/<int:pk>/payment_transactions/', views.OrderViewSet.as_view({'get': 'payment_transactions'}), name='order_payment_transactions'),
    path('reports/payments_data/', views.OrderViewSet.as_view({'get': 'payments_data'}), name='payments_data'),

    # Invoice/Delivery note data
    path('orders/<int:pk>/invoice_data/', views.OrderViewSet.as_view({'get': 'invoice_data'}), name='invoice_data'),
    path('orders/<int:pk>/delivery_note_data/', views.OrderViewSet.as_view({'get': 'delivery_note_data'}), name='delivery_note_data'),

    # Proof of payment signed access
    path('payment-proofs/signed_file/', views.payment_proof_signed_file, name='paymentproof-signed-file'),

    # Dashboards/analytics
    path('orders/warehouse_analytics/', views.OrderViewSet.as_view({'get': 'warehouse_analytics'}), name='warehouse_analytics'),
    path('orders/owner_dashboard/', views.OrderViewSet.as_view({'get': 'owner_dashboard_orders'}), name='owner_dashboard_orders'),
    path('orders/admin_dashboard/', views.OrderViewSet.as_view({'get': 'admin_dashboard_orders'}), name='admin_dashboard_orders'),
    path('orders/admin_warehouse_overview/', views.OrderViewSet.as_view({'get': 'admin_warehouse_overview'}), name='admin_warehouse_overview'),
    path('orders/warehouse_dashboard/', views.OrderViewSet.as_view({'get': 'warehouse_dashboard_orders'}), name='warehouse_dashboard_orders'),
    path('orders/delivery_dashboard/', views.OrderViewSet.as_view({'get': 'delivery_dashboard_orders'}), name='delivery_dashboard_orders'),

    # Legacy helpers
    path('orders/warehouse_orders/', views.OrderViewSet.as_view({'get': 'warehouse_orders'}), name='warehouse_orders'),
    path('orders/<int:pk>/create_task/', views.OrderViewSet.as_view({'post': 'create_task'}), name='order_create_task'),
    path('orders/<int:pk>/escalate_priority/', views.OrderViewSet.as_view({'post': 'escalate_priority'}), name='escalate_priority'),
    path('orders/<int:pk>/assign_warehouse/', views.OrderViewSet.as_view({'post': 'assign_warehouse'}), name='assign_warehouse'),
    path('orders/<int:pk>/assign_delivery/', views.OrderViewSet.as_view({'post': 'assign_delivery'}), name='assign_delivery'),
] 