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
router.register(r'products', views.ProductViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('materials/quick_stock_entry/', views.quick_stock_entry, name='quick_stock_entry'),
    # Alias for categories list used by frontend helper
    path('material-categories/', views.MaterialCategoryViewSet.as_view({'get': 'list'}), name='material_categories'),
    # Product management endpoints
    path('products/create_with_options/', views.create_product_with_options, name='create_product_with_options'),
]