"""
Tests for the order and placement API
"""

from decimal import Decimal
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from django.test import TestCase
from django.contrib.auth import get_user_model
from user.models import Address
from product.models import Product
from order.models import (
    CartItem,
    Cart,
    OrderItem,
    Order
)
# from order.serializers import (
#     OrderItemSerializer,
#     OrderSerializer
# )


def get_order_url():
    return reverse('order:order-list')


def get_order_detail_url(order_id):
    return reverse('order:order-detail', args=[order_id])


def create_product(**params):
    defaults = {
        'name': 'Product 1',
        'description': 'Description 1',
        'price': Decimal('10.50'),
        'stock': 100,
        'average_rating': 4.5,
        'ratings_count': 10,
        'category': None,
    }
    defaults.update(params)
    return Product.objects.create(**defaults)


class PublicCartAPITests(TestCase):
    """Tests for unauthenticated users"""

    def test_auth_required_for_order_placement(self):
        """Unauthenticated users cannot place an order (401)."""
        client = APIClient()

        url = get_order_url()
        res = client.post(url)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

        self.assertEqual(Order.objects.count(), 0)


class PrivateCartAPITests(TestCase):
    """Tests for authenticated users"""

    @classmethod
    def setUpTestData(cls):
        """Create test data once for all tests."""
        cls.user = get_user_model().objects.create_user(
            username='janek123',
            email='user@example.com',
            first_name='Jan',
            last_name='Kowalski',
            phone_number='123456789',
            password='Test1234',
        )

        cls.products = [
            create_product(name='Product1', price=Decimal('25.00')),
            create_product(name='Product2', price=Decimal('30.25')),
            create_product(name='Product3', price=Decimal('40.99')),
        ]

    def setUp(self):
        """Create a fresh cart for each test."""
        self.client = APIClient()
        self.client.force_authenticate(self.user)

        self.cart = Cart.objects.create(user=self.user)
        self.cart_items = [
            CartItem.objects.create(
                cart=self.cart,
                product=product,
                quantity=3,
            )
            for product in self.products
        ]

    def test_cannot_place_order_with_empty_card(self):
        """Cannot place an order when the user's cart is empty."""
        self.client.delete(reverse('order:cart-clear'))
        res = self.client.post(get_order_url())

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Order.objects.filter(user=self.user).count(), 0)

    def test_successful_order_creation_from_cart(self):
        """
        Authenticated user can place an order from a non-empty cart
        """
        res = self.client.post(get_order_url())
        order = Order.objects.filter(user=self.user).first()

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(order)

    def test_order_items_match_cart_items(self):
        """
        Each CartItem is converted into a corresponding OrderItem with matching quantity and price. # noqa
        """

        cart_items = self.cart_items
        res = self.client.post(get_order_url())
        order = Order.objects.filter(user=self.user).first()
        order_items = OrderItem.objects.filter(order=order)

        self.assertTrue(
            all(
                o_item.product == c_item.product
                and o_item.quantity == c_item.quantity
                and o_item.price == c_item.product.price
                and o_item.total_price == c_item.subtotal()
                for o_item, c_item in zip(order_items, cart_items)
            ),
            "Not all OrderItems match their corresponding CartItems"
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_order_total_equals_sum_of_cart_items(self):
        """
        Order total equals the sum of all cart item subtotals.
        """
        total_cart = self.cart.total()
        res = self.client.post(get_order_url())

        order = Order.objects.filter(user=self.user).first()

        self.assertEqual(
            Decimal(total_cart), Decimal(order.calculate_total(save=False))
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_order_status_is_pending_after_creation(self):
        """Newly created order has status 'pending'."""
        res = self.client.post(get_order_url())
        order = Order.objects.filter(user=self.user).first()

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(order.status, "pending")

    def test_cart_items_cleared_after_successful_order(self):
        """CartItems are removed from the cart after placing an order."""
        res = self.client.post(get_order_url())
        cart_items = CartItem.objects.filter(cart=self.cart)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(cart_items.count(), 0)

    def test_cannot_place_order_for_another_user_cart(self):
        """
        Authenticated user cannot place an order using another user's cart (403 or 400). # noqa
        """
        other = get_user_model().objects.create_user(
            username='other_public2',
            email='otherpub2@example.com',
            first_name='Other',
            last_name='Public2',
            phone_number='000000001',
            password='Test1234'
        )
        other_cart = Cart.objects.create(user=other)

        res = self.client.post(
            get_order_url(), data={'cart_id': other_cart.id}
        )

        self.assertIn(
            res.status_code,
            [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN]
        )
        self.assertFalse(Order.objects.filter(user=self.user).exists())

    def test_multiple_orders_can_be_placed_independently(self):
        """
        User can place multiple orders over time; each creates a new Order instance. # noqa
        """
        res1 = self.client.post(get_order_url())
        order1 = Order.objects.filter(user=self.user).first()
        CartItem.objects.create(
                cart=self.cart,
                product=self.products[1],
                quantity=2,
            )
        res2 = self.client.post(get_order_url())
        order2 = Order.objects.filter(user=self.user).last()

        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res2.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(order1, order2)
        self.assertEqual(order1.items.count(), 3) # 3 items in setUp # noqa 
        self.assertEqual(order2.items.count(), 1)

    def test_user_can_list_their_orders(self):
        """Authenticated user can retrieve their own orders list."""
        # ensure orders have an address (Order.address is non-nullable)
        address = Address.objects.create(
            user=self.user,
            street="Testowa 1",
            city="Warszawa",
            zip_code="00-001",
            country="Poland",
        )
        Order.objects.create(
            user=self.user, address=address, status="pending", total=100
        )
        Order.objects.create(
            user=self.user, address=address, status="pending", total=200
        )

        other_user = get_user_model().objects.create_user(
            username='other_public2',
            email='otherpub2@example.com',
            first_name='Other',
            last_name='Public2',
            phone_number='000000001',
            password='Test1234'
        )
        other_address = Address.objects.create(
            user=other_user,
            street="Other 1",
            city="Town",
            zip_code="11-111",
            country="Poland",
        )
        Order.objects.create(
            user=other_user,
            address=other_address,
            status="pending",
            total=300,
        )

        res = self.client.get(get_order_url())

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        orders = Order.objects.filter(user=self.user).order_by('id')
        serializer = OrderSerializer(orders, many=True)
        self.assertEqual(res.data, serializer.data)

    def test_user_can_retrieve_their_order_detail(self):
        """Authenticated user can retrieve a single order detail."""
        address = Address.objects.create(
            user=self.user,
            street="Testowa 12",
            city="Warszawa",
            zip_code="00-001",
            country="Poland"
        )
        order = Order.objects.create(
            user=self.user,
            address=address,
            status="pending",
            total=Decimal("123.45"),
        )

        url = get_order_detail_url(order.id)
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        serializer = OrderItemSerializer(order)
        self.assertEqual(res.data, serializer.data)

    def test_user_cannot_access_another_users_order(self):
        """
        Authenticated user cannot retrieve another user's order detail.
        """
        other_user = get_user_model().objects.create_user(
            username='other_public2',
            email='otherpub2@example.com',
            first_name='Other',
            last_name='Public2',
            phone_number='000000001',
            password='Test1234'
        )
        address = Address.objects.create(
            user=other_user,
            street="Testowa 12",
            city="Warszawa",
            zip_code="00-001",
            country="Poland"
        )
        order = Order.objects.create(
            user=other_user, address=address, total=Decimal('99.99')
        )
        res = self.client.get(get_order_detail_url(order.id))
        self.assertIn(
            res.status_code,
            [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]
        )
