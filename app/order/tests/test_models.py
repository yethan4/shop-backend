# ...existing code...
"""
Tests for Cart, CartItem, Order, OrderItem and Payment models
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.utils import timezone
from order import models
from product.models import Product
from user.models import Address


def create_user(
    email='user@example.com',
    password='testpass123',
    **extra_fields
):
    """
    Create and return a new user.

    Accepts optional extra fields (username, phone_number,
    first_name, last_name, etc.)
    """
    User = get_user_model()
    defaults = {
        'username': extra_fields.pop('username', 'testuser'),
        'phone_number': extra_fields.pop('phone_number', '123456789'),
        'first_name': extra_fields.pop('first_name', 'Test'),
        'last_name': extra_fields.pop('last_name', 'User'),
    }

    defaults.update(extra_fields)
    return User.objects.create_user(
        email=email,
        password=password,
        **defaults
    )


def create_product(name='Test Product', price='9.99'):
    """Create and return a simple Product for tests."""
    return Product.objects.create(
        name=name,
        description='Desc',
        price=Decimal(price),
        stock=100,
        average_rating=Decimal('4.5'),
        ratings_count=1,
    )


def create_address_for_user(user):
    """Create an Address for a user, tolerate different Address signatures."""
    try:
        return Address.objects.create(
            user=user,
            street='Street 1',
            city='City',
            postal_code='00000',
            country='Country',
        )
    except Exception:
        try:
            return Address.objects.create(user=user)
        except Exception:
            return Address.objects.create()


class BaseOrderTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = create_user()
        cls.product = create_product()
        cls.address = create_address_for_user(cls.user)


class CartModelTests(BaseOrderTest):
    def test_cart_total_and_str(self):
        """Test that cart.total() sums subtotals and __str__ contains Cart."""
        cart = models.Cart.objects.create(user=self.user)
        models.CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=2,
        )

        self.assertIn('Cart', str(cart))
        self.assertEqual(cart.total(), self.product.price * 2)

    def test_empty_cart_total_zero(self):
        """Test that an empty cart returns total 0.00."""
        cart = models.Cart.objects.create(user=self.user)
        self.assertEqual(cart.total(), Decimal('0.00'))


class CartItemModelTests(BaseOrderTest):
    def test_cartitem_subtotal_and_unique_constraint(self):
        """Test subtotal() and unique (cart, product) constraint."""
        cart = models.Cart.objects.create(user=self.user)
        models.CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=3,
        )
        item = models.CartItem.objects.get(cart=cart, product=self.product)
        self.assertEqual(item.subtotal(), self.product.price * 3)

        with self.assertRaises(IntegrityError):
            models.CartItem.objects.create(
                cart=cart,
                product=self.product,
                quantity=1,
            )


class OrderItemModelTests(BaseOrderTest):
    def test_orderitem_total_price_and_str(self):
        """Test OrderItem.total_price and __str__ content."""
        order = models.Order.objects.create(
            user=self.user,
            address=self.address,
        )
        oi = models.OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=4,
            price=self.product.price,
        )
        self.assertEqual(oi.total_price, self.product.price * 4)
        self.assertIn(self.product.name, str(oi))


class OrderModelTests(BaseOrderTest):
    def test_order_calculate_total(self):
        """Test calculate_total() sums items and persists when save=True."""
        order = models.Order.objects.create(
            user=self.user,
            address=self.address,
        )
        p2 = create_product(name='Other', price='5.00')
        models.OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=1,
            price=self.product.price,
        )
        models.OrderItem.objects.create(
            order=order,
            product=p2,
            quantity=2,
            price=p2.price,
        )

        items = list(order.items.all())
        expected = sum(i.total_price for i in items)
        self.assertEqual(order.calculate_total(save=False), expected)
        order.calculate_total(save=True)
        self.assertEqual(order.total, expected)


class PaymentModelTests(BaseOrderTest):
    def test_payment_mark_succeeded(self):
        """Test mark_succeeded() sets status and paid_at timestamp."""
        order = models.Order.objects.create(
            user=self.user,
            address=self.address,
        )
        models.OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=1,
            price=self.product.price,
        )
        order.calculate_total(save=True)

        payment = models.Payment.objects.create(
            order=order,
            payment_method='card',
            amount=order.total,
            status='pending',
        )
        payment.mark_succeeded()
        self.assertEqual(payment.status, 'succeeded')
        self.assertIsNotNone(payment.paid_at)

        delta_seconds = (timezone.now() - payment.paid_at).total_seconds()
        self.assertLessEqual(delta_seconds, 5)
