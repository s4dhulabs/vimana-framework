# -*- coding: utf-8 -*-
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from shop.views import (
    AdminOrderViewSet,
    HealthView,
    OpenAPIView,
    OpenOrderViewSet,
    SecureOrderViewSet,
    SeedStatusView,
)

router = DefaultRouter()
router.register(r'api/orders', OpenOrderViewSet, basename='open-orders')
router.register(r'api/secure/orders', SecureOrderViewSet, basename='secure-orders')
router.register(r'api/admin/orders', AdminOrderViewSet, basename='admin-orders')

urlpatterns = [
    path('health', HealthView.as_view()),
    path('health/', HealthView.as_view()),
    path('openapi.json', OpenAPIView.as_view()),
    path('api/schema/', OpenAPIView.as_view()),
    path('orders/catalog', SeedStatusView.as_view()),
    path('', include(router.urls)),
]
