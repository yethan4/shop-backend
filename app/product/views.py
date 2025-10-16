"""
Views for product and category API
"""
from rest_framework import viewsets

from .models import Product, Category
from .serializers import (
    ProductDetailSerializer,
    ProductSerializer,
    CategorySerializer,
)


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """View for listing and retrieving products"""
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductSerializer

    def get_queryset(self):
        """
        Retrieve and list products for any user (authenticated or not).
        Optionally filter products by category (?category=).
        """
        queryset = Product.objects.all()
        category_id = self.request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        return queryset


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """View for listing and retrieving categories"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
