"""
Serializers for the order API View.
"""
from rest_framework import serializers

from product.models import Product, ProductImage
from .models import Cart, CartItem


class ProductCartSerializer(serializers.ModelSerializer):
    main_image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['name', 'description', 'main_image']

    def get_main_image(self, obj):
        image = ProductImage.objects.filter(product=obj).first()
        if image:
            return image.image.url
        else:
            return None


class CartItemSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all()
    )
    product_data = serializers.SerializerMethodField()
    subtotal = serializers.SerializerMethodField()
    quantity = serializers.IntegerField(min_value=1, default=1)

    class Meta:
        model = CartItem
        fields = ['id', 'cart', 'product', 'product_data', 'quantity',
                  'subtotal']
        read_only_fields = ['id', 'subtotal', 'cart']

    def get_product_data(self, obj):
        return ProductCartSerializer(obj.product).data

    def get_subtotal(self, obj):
        return obj.subtotal()


class CartSerializer(serializers.ModelSerializer):
    total = serializers.SerializerMethodField()
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'items', 'total', 'total_items', 'total']

    def get_total(self, obj):
        return obj.total()

    def get_total_items(self, obj):
        return sum(item.quantity for item in obj.items.all())
