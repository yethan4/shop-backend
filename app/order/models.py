from decimal import Decimal
from django.utils import timezone
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from product.models import Product
from user.models import Address


class Cart(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='carts'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart {self.id} ({self.user})"

    def total(self):
        total = Decimal('0.00')
        for item in self.items.all():
            total += item.subtotal()
        return total


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='cart_items'
    )
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"

    def subtotal(self):
        return self.product.price * self.quantity

    class Meta:
        verbose_name = 'cart item'
        verbose_name_plural = 'cart items'
        constraints = [
            models.UniqueConstraint(
                fields=['cart', 'product'],
                name='unique_cart_product'
            )
        ]


class Order(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    address = models.ForeignKey(
        Address,
        on_delete=models.PROTECT,
        related_name='orders'
    )
    status = models.CharField(max_length=50, default='pending', db_index=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def calculate_total(self, save=False):
        total = sum(
            (item.total_price for item in self.items.all()),
            Decimal('0.00')
        )
        self.total = total
        if save:
            self.save(update_fields=['total'])
        return total

    def __str__(self):
        return f"Order {self.id} ({self.user})"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='order_items'
    )
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def total_price(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"

    class Meta:
        verbose_name = 'order item'
        verbose_name_plural = 'order items'


class Payment(models.Model):
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='payment'
    )
    payment_method = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50, default='pending')
    paid_at = models.DateTimeField(null=True, blank=True)

    def mark_succeeded(self):
        self.status = 'succeeded'
        self.paid_at = timezone.now()
        self.save(update_fields=['status', 'paid_at'])

    def __str__(self):
        return f"Payment {self.id} for Order {self.order.id}"
