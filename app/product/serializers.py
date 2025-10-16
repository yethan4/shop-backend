"""
Serializers for the product and category API View.
"""
from rest_framework import serializers

from .models import Category, Product, ProductImage


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']


class ProductSerializer(serializers.ModelSerializer):
    main_image = serializers.SerializerMethodField()
    is_available = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'category',
                  'main_image', 'is_available']

    def get_main_image(self, obj):
        image = ProductImage.objects.filter(product=obj).first()
        if image:
            return image.image.url
        else:
            return None

    def get_is_available(self, obj):
        return getattr(obj, 'stock', 0) > 0


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image']


class ProductDetailSerializer(ProductSerializer):
    images = ProductImageSerializer(source='productimage_set',
                                    many=True, read_only=True)

    class Meta(ProductSerializer.Meta):
        fields = ProductSerializer.Meta.fields + ['images']
