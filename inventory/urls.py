from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'categories', views.MaterialCategoryViewSet)
router.register(r'suppliers', views.SupplierViewSet)
router.register(r'materials', views.MaterialViewSet)
router.register(r'stock-movements', views.StockMovementViewSet)
router.register(r'product-materials', views.ProductMaterialViewSet)
router.register(r'alerts', views.StockAlertViewSet)
router.register(r'predictions', views.MaterialConsumptionPredictionViewSet)


urlpatterns = [
    path('', include(router.urls)),
    path('materials/quick_stock_entry/', views.MaterialViewSet.as_view({'post': 'quick_stock_entry'}), name='quick_stock_entry'),
    # Alias for categories list used by frontend helper
    path('material-categories/', views.MaterialCategoryViewSet.as_view({'get': 'list'}), name='material_categories'),

    # Material dashboard endpoints
    path('materials/warehouse_dashboard/', views.MaterialViewSet.as_view({'get': 'warehouse_dashboard'}), name='warehouse_dashboard'),
    path('materials/low_stock/', views.MaterialViewSet.as_view({'get': 'low_stock'}), name='low_stock'),
]