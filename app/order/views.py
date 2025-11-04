from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer


class CartItemViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for individual cart items.
    """
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return cart items for all users (filtered in get_object)."""
        return CartItem.objects.all()

    def get_object(self):
        """Ensure the cart item belongs to the current user."""
        obj = super().get_object()
        if obj.cart.user != self.request.user:
            raise PermissionDenied(
                "Cannot access another user's cart item."
            )
        return obj

    def create(self, request, *args, **kwargs):
        """
        Add a product to the cart.
        If the product already exists in the cart, increase its quantity.
        """
        requested_cart_id = request.data.get('cart')
        if requested_cart_id:
            try:
                requested_cart = Cart.objects.get(pk=requested_cart_id)
                if requested_cart.user != request.user:
                    return Response(
                        {"detail": "Cannot add to another user's cart."},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except Cart.DoesNotExist:
                pass

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cart, _ = Cart.objects.get_or_create(user=request.user)
        product = serializer.validated_data['product']
        quantity = serializer.validated_data['quantity']

        item, created = CartItem.objects.get_or_create(
            cart=cart, product=product
        )
        if created:
            item.quantity = quantity
        else:
            item.quantity += quantity
        item.save()
        serializer.instance = item

        status_c = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(serializer.data, status=status_c)

    def partial_update(self, request, *args, **kwargs):
        """
        Update the quantity of a cart item.
        - quantity < 0 → returns 400
        - quantity = 0 → deletes the item (204)
        """
        item = self.get_object()
        quantity = request.data.get('quantity', None)

        if quantity is None:
            serializer = self.get_serializer(item, data=request.data,
                                             partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

        quantity = int(quantity)
        if quantity < 0:
            return Response(
                {"quantity": "Quantity cannot be negative."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if quantity == 0:
            item.delete()
            return Response(
                {"detail": "Cart item deleted"},
                status=status.HTTP_204_NO_CONTENT
            )

        item.quantity = quantity
        item.save()
        serializer = self.get_serializer(item)
        return Response(serializer.data)

    def perform_destroy(self, instance):
        """Delete a cart item."""
        instance.delete()


class CartViewSet(viewsets.ViewSet):
    """
    Retrieve or clear the current user's cart.
    """
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """
        GET /cart/
        Retrieve the current user's cart with items and total.
        """
        cart, _ = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    @action(detail=False, methods=['delete'])
    def clear(self, request):
        """
        DELETE /cart/clear/
        Remove all items from the current user's cart, but keep the cart.
        """
        cart = Cart.objects.get(user=request.user)
        cart.items.all().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
