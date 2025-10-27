"""
Tests for the cart and cart item API
"""
from decimal import Decimal
from rest_framework.test import APIClient
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from product.models import Product, Category
from order.models import Cart, CartItem


def get_cart_url():
    return reverse('order:cart')


def get_cart_item_url():
    return reverse('order:cart-item')


def cart_item_detail_url(item_id):
    return reverse('order:cart-item-detail', args=[item_id])


def create_category(name='default'):
    return Category.objects.create(name=name)


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

    def setUp(self):
        self.client = APIClient()
        self.product1 = create_product(name='PublicProduct1')

    def test_auth_required_for_post_cart_item(self):
        """Unauthenticated user cannot add an item to cart (401)."""
        payload = {'product': self.product1.id, 'quantity': 2}
        res = self.client.post(get_cart_item_url(), payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Cart.objects.count(), 0)
        self.assertEqual(CartItem.objects.count(), 0)

    def test_auth_required_for_patch_cart_item(self):
        """Unauthenticated user cannot update a cart item (401)."""
        other = get_user_model().objects.create_user(
            username='other_public',
            email='otherpub@example.com',
            first_name='Other',
            last_name='Public',
            phone_number='000000000',
            password='Test1234'
        )
        cart = Cart.objects.create(user=other)
        item = CartItem.objects.create(
            cart=cart,
            product=self.product1,
            quantity=3
        )

        res = self.client.patch(
            cart_item_detail_url(item.id),
            {'quantity': 5},
            format='json'
        )

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        item.refresh_from_db()
        self.assertEqual(item.quantity, 3)

    def test_auth_required_for_delete_cart_item(self):
        """Unauthenticated user cannot delete a cart item (401)."""
        other = get_user_model().objects.create_user(
            username='other_public2',
            email='otherpub2@example.com',
            first_name='Other',
            last_name='Public2',
            phone_number='000000001',
            password='Test1234'
        )
        cart = Cart.objects.create(user=other)
        item = CartItem.objects.create(
            cart=cart,
            product=self.product1,
            quantity=1
        )

        res = self.client.delete(cart_item_detail_url(item.id))

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(CartItem.objects.filter(pk=item.id).exists())

    def test_auth_required_for_get_cart(self):
        """Unauthenticated user cannot retrieve cart (401)."""
        res = self.client.get(get_cart_url())
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateCartAPITests(TestCase):
    """Tests for authenticated users"""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='janek123',
            email='user@example.com',
            first_name='Jan',
            last_name='Kowalski',
            phone_number='123456789',
            password='Test1234',
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.product1 = create_product(name='Product1')
        self.product2 = create_product(name='Product2')
        self.product3 = create_product(name='Product3')

    def test_add_first_product_creates_cart_and_cartitem(self):
        """
        An authenticated user can add first product and create cart+item
        """

        self.assertFalse(
            Cart.objects.filter(user=self.user).exists()
        )

        payload = {
            'product': self.product1.id,
            'quantity': 4,
        }
        res = self.client.post(get_cart_item_url(), payload, format='json')

        cart = Cart.objects.filter(user=self.user).first()
        cart_item = CartItem.objects.filter(
            cart=cart, product=self.product1
        ).first()

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Cart.objects.filter(user=self.user).count(), 1)
        self.assertEqual(
            CartItem.objects.filter(cart=cart).count(),
            1
        )
        self.assertEqual(res.data['product'], cart_item.product.id)
        self.assertEqual(res.data['quantity'], cart_item.quantity)
        self.assertEqual(
            Decimal(res.data['subtotal']),
            cart_item.product.price * cart_item.quantity
        )
        self.assertEqual(
            cart.total(),
            cart_item.product.price * cart_item.quantity
        )

    def test_add_new_product_to_existing_cart(self):
        """An authenticated user can add new product to existing cart"""

        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(
            cart=cart,
            product=self.product2,
            quantity=5
        )

        payload = {
            'product': self.product1.id,
            'quantity': 2,
        }
        res = self.client.post(get_cart_item_url(), payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(int(res.data['product']), payload['product'])
        self.assertEqual(
            CartItem.objects.filter(cart=cart).count(),
            2,
        )
        self.assertEqual(
            Decimal(res.data['subtotal']),
            self.product1.price * Decimal(payload['quantity'])
        )

        expected = 0
        for cart_item in cart.items.all():
            expected += cart_item.quantity * cart_item.product.price
        self.assertEqual(cart.total(), expected)

    def test_add_product_to_cart_when_item_exists(self):
        """When an authenticated user adds a product already in the cart,
        the item's quantity is increased and its subtotal is updated."""

        cart = Cart.objects.create(user=self.user)
        cart_item = CartItem.objects.create(
            cart=cart,
            product=self.product1,
            quantity=2
        )
        payload = {
            'product': self.product1.id,
            'quantity': 2,
        }
        res = self.client.post(get_cart_item_url(), payload, format='json')

        cart_item.refresh_from_db()
        cart.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(int(res.data['product']), payload['product'])
        self.assertEqual(
            CartItem.objects.filter(cart=cart).count(),
            1,
        )
        self.assertEqual(cart_item.quantity, 4)
        self.assertEqual(
            Decimal(res.data['subtotal']),
            cart_item.product.price * 4
        )
        self.assertEqual(
            cart.total(),
            cart_item.product.price * 4
        )

    def test_cannot_add_product_to_another_users_cart(self):
        """
        An authenticated user cannot add items to another user's cart.
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

        payload = {
            'cart': other_cart.id,
            'product': self.product1.id,
            'quantity': 1,
        }
        res = self.client.post(get_cart_item_url(), payload, format='json')

        self.assertIn(
            res.status_code,
            (status.HTTP_403_FORBIDDEN, status.HTTP_400_BAD_REQUEST),
        )

        self.assertEqual(
            CartItem.objects.filter(cart=other_cart).count(),
            0,
        )

        self.assertEqual(
            CartItem.objects.filter(cart__user=self.user).count(),
            0,
        )

    def test_update_cartitem_quantity_updates_subtotal_and_cart_total(self):
        """
        An authenticated user can update a cart item's quantity;
        the cartitem subtotal and cart total are updated accordingly.
        """

        cart = Cart.objects.create(user=self.user)
        cart_item = CartItem.objects.create(
            cart=cart,
            product=self.product1,
            quantity=6
        )
        cart_item2 = CartItem.objects.create(
            cart=cart,
            product=self.product2,
            quantity=4
        )

        payload = {
            'quantity': 2,
        }
        res = self.client.patch(
            cart_item_detail_url(cart_item.id),
            payload,
            format='json'
        )

        cart_item.refresh_from_db()
        cart.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(cart_item.quantity, 2)
        self.assertEqual(cart_item2.quantity, 4)
        self.assertEqual(int(res.data.get('product')), self.product1.id)
        self.assertEqual(res.data.get('quantity'), 2)
        self.assertEqual(
            CartItem.objects.filter(cart=cart).count(),
            2
        )
        self.assertEqual(
            Decimal(res.data['subtotal']),
            cart_item.product.price * 2
        )
        self.assertEqual(
            cart.total(),
            cart_item.product.price * 2 + cart_item2.product.price * 4
        )

    def test_remove_cartitem_deletes_item_and_updates_cart(self):
        """
        An authenticated user can delete a cart item;
        the item is removed and the cart total is updated;
        even if it is the last cart item, the cart will remain and be empty.
        """

        cart = Cart.objects.create(user=self.user)
        cart_item = CartItem.objects.create(
            cart=cart,
            product=self.product1,
            quantity=6
        )

        res = self.client.delete(cart_item_detail_url(cart_item.id))

        self.assertIn(
            res.status_code,
            (status.HTTP_204_NO_CONTENT, status.HTTP_200_OK)
        )
        self.assertFalse(CartItem.objects.filter(pk=cart_item.id).exists())

        self.assertTrue(Cart.objects.filter(pk=cart.id).exists())
        cart.refresh_from_db()
        self.assertEqual(cart.items.count(), 0)
        self.assertEqual(cart.total(), Decimal('0'))

    def test_setting_cartitem_quantity_to_zero_removes_item_from_cart(self):
        """
        An authenticated user setting a cart item's quantity to zero
        removes the item from the cart and updates the cart total.
        """
        cart = Cart.objects.create(user=self.user)
        cart_item = CartItem.objects.create(
            cart=cart,
            product=self.product1,
            quantity=6
        )
        cart_item2 = CartItem.objects.create(
            cart=cart,
            product=self.product2,
            quantity=4
        )

        payload = {
            'quantity': 0,
        }
        res = self.client.patch(
            cart_item_detail_url(cart_item.id),
            payload,
            format='json'
        )

        cart.refresh_from_db()

        self.assertIn(
            res.status_code,
            (status.HTTP_200_OK, status.HTTP_204_NO_CONTENT)
        )
        self.assertFalse(CartItem.objects.filter(pk=cart_item.id).exists())
        self.assertEqual(
            CartItem.objects.filter(cart=cart).count(),
            1
        )
        self.assertEqual(
            cart.total(),
            cart_item2.product.price * cart_item2.quantity
        )

    def test_cannot_update_another_users_cartitem(self):
        """An authenticated user cannot update the quantity of a cart item
        that belongs to another user (should return 403 or 400).
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
        other_item = CartItem.objects.create(
            cart=other_cart,
            product=self.product1,
            quantity=3
        )

        payload = {'quantity': 5}
        res = self.client.patch(
            cart_item_detail_url(other_item.id),
            payload,
            format='json'
        )

        self.assertIn(
            res.status_code,
            (status.HTTP_403_FORBIDDEN, status.HTTP_400_BAD_REQUEST),
        )

        other_item.refresh_from_db()
        self.assertEqual(other_item.quantity, 3)
        self.assertEqual(CartItem.objects.filter(cart=other_cart).count(), 1)
        self.assertEqual(
            CartItem.objects.filter(cart__user=self.user).count(),
            0
        )

    def test_cannot_delete_another_users_cartitem(self):
        """An authenticated user cannot delete a cart item
        that belongs to another user
        (should return 403 or 400) and the item remains.
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
        other_item = CartItem.objects.create(
            cart=other_cart,
            product=self.product2,
            quantity=2
        )

        res = self.client.delete(cart_item_detail_url(other_item.id))

        self.assertIn(
            res.status_code,
            (status.HTTP_403_FORBIDDEN, status.HTTP_400_BAD_REQUEST),
        )

        self.assertTrue(CartItem.objects.filter(pk=other_item.id).exists())
        self.assertEqual(CartItem.objects.filter(cart=other_cart).count(), 1)
        self.assertEqual(
            CartItem.objects.filter(cart__user=self.user).count(),
            0
        )

    def test_retrieve_cart_returns_items_and_total(self):
        """
        An authenticated user can retrieve their cart with items and total.
        """
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product1, quantity=2)
        CartItem.objects.create(cart=cart, product=self.product2, quantity=3)

        res = self.client.get(get_cart_url())

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('items', res.data)
        self.assertIn('total', res.data)
        self.assertEqual(len(res.data['items']), 2)
        self.assertEqual(Decimal(res.data.get('total')), cart.total())

    def test_delete_cart_clears_items_but_keeps_cart(self):
        """
        An authenticated user deleting the cart clears all items
        but keeps the Cart instance.
        """

        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product1, quantity=1)
        CartItem.objects.create(cart=cart, product=self.product2, quantity=2)

        res = self.client.delete(get_cart_url())

        self.assertIn(
            res.status_code,
            (status.HTTP_204_NO_CONTENT, status.HTTP_200_OK)
        )

        self.assertTrue(Cart.objects.filter(pk=cart.id).exists())
        cart.refresh_from_db()
        self.assertEqual(cart.items.count(), 0)
        self.assertEqual(cart.total(), Decimal('0'))
