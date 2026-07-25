# -*- coding: utf-8 -*-
"""
Vulnerable DRF views for objgate BOLA lab.

- /api/orders/{id}         — no auth required, no owner filter (CWE-306 + CWE-639)
- /api/secure/orders/{id}  — requires Bearer token, but does NOT enforce ownership
- /api/admin/orders/{id}   — privileged path reachable by any authenticated user (BFLA)
"""

from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from shop.models import Order
from shop.serializers import OrderSerializer


class OpenOrderViewSet(viewsets.ModelViewSet):
    """Open orders — AllowAny and full queryset (classic BOLA lab)."""

    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [AllowAny]
    http_method_names = ['get', 'patch', 'put', 'head', 'options']


class SecureOrderViewSet(viewsets.ModelViewSet):
    """
    'Secure' orders — authentication required, ownership NOT checked.
    Documented intent: user-a → order 1, user-b → order 2.
    Actual: any valid token can GET/PATCH any order id.
    """

    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'patch', 'put', 'head', 'options']


class AdminOrderViewSet(viewsets.ReadOnlyModelViewSet):
    """Admin-looking path — should be staff-only; allows any authenticated user."""

    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'head', 'options']


class HealthView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        return Response({'status': 'ok', 'service': 'objgate-lab'})


class OpenAPIView(APIView):
    """Minimal OpenAPI document for objgate discovery."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        return Response({
            'openapi': '3.0.3',
            'info': {
                'title': 'Objgate Lab API',
                'description': 'Vulnerable DRF order endpoints for BOLA/IDOR audits',
                'version': '1.0.0',
            },
            'paths': {
                '/api/orders/{id}/': {
                    'get': {
                        'summary': 'Retrieve order (open — no auth)',
                        'operationId': 'open_order_retrieve',
                        'parameters': [{
                            'name': 'id',
                            'in': 'path',
                            'required': True,
                            'schema': {'type': 'integer'},
                        }],
                    },
                    'patch': {
                        'summary': 'Update order (open — no auth)',
                        'operationId': 'open_order_partial_update',
                    },
                },
                '/api/secure/orders/{id}/': {
                    'get': {
                        'summary': 'Retrieve order (auth required, ownership broken)',
                        'operationId': 'secure_order_retrieve',
                        'parameters': [{
                            'name': 'id',
                            'in': 'path',
                            'required': True,
                            'schema': {'type': 'integer'},
                        }],
                    },
                    'patch': {
                        'summary': 'Update order (auth required, ownership broken)',
                        'operationId': 'secure_order_partial_update',
                    },
                },
                '/api/admin/orders/{id}/': {
                    'get': {
                        'summary': 'Admin order detail (BFLA — any authenticated user)',
                        'operationId': 'admin_order_retrieve',
                    },
                },
                '/health': {
                    'get': {
                        'summary': 'Health check',
                        'operationId': 'health',
                    },
                },
            },
        })


class SeedStatusView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        return Response({
            'orders': list(
                Order.objects.values('id', 'owner', 'amount', 'note', 'secret')
            ),
            'tokens': {
                'user-a': 'Bearer user-a-token',
                'user-b': 'Bearer user-b-token',
            },
        })
