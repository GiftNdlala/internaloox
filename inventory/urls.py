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
]